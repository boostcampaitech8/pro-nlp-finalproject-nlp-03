"use client";

import { useNavigate, useLocation } from "react-router-dom";
import React, { useEffect, useMemo, useRef, useState } from "react";
import RecipeLayout from "@/layouts/RecipeLayout";
import "./CookModeAudioPage.css";

/**
 * CookModeAudioPage
 * - RecipeLayout 사용 (CookModePage와 동일한 틀)
 * - 중앙 컴포넌트만 채팅 UI로 변경
 * - API 호출 로직은 그대로 유지
 */

// ====== API endpoints ======
const STT_BASE_URL = "http://213.173.102.218:14184";
const LLM_BASE_URL = "http://213.173.102.218:14186";
const TTS_BASE_URL = "http://213.173.102.218:14185";

const STT_ENDPOINT = "/transcribe_bytes";
const LLM_ENDPOINT = "/classify";
const TTS_ENDPOINT = "/synthesize/stream";

// ====== VAD tuning ======
const VAD_THRESHOLD = 0.02;
const VAD_SILENCE_MS = 800;
const VAD_MIN_SPEECH_MS = 300;

function pickMimeType() {
  const candidates = [
    "audio/mp4;codecs=mp4a.40.2",
    "audio/mp4",
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/ogg",
  ];
  return candidates.find((t) => MediaRecorder.isTypeSupported(t)) || "";
}

function nowTs() {
  return Date.now();
}

// ====== API calls ======
async function sttTranscribeRawBlob(blob) {
  const ab = await blob.arrayBuffer();
  const res = await fetch(`${STT_BASE_URL}${STT_ENDPOINT}`, {
    method: "POST",
    headers: { "Content-Type": "application/octet-stream" },
    body: ab,
  });

  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`STT HTTP ${res.status}: ${txt}`);
  }
  return await res.json();
}

async function llmClassifyAndRespond({ userText, currentStep }) {
  const res = await fetch(`${LLM_BASE_URL}${LLM_ENDPOINT}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: userText, current_step: currentStep }),
  });

  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`LLM HTTP ${res.status}: ${txt}`);
  }

  const json = await res.json();
  const intent = json.intent || "";
  const responseText = json.responseText || json.response || "";

  const safeResponse =
    (responseText || "").trim() ||
    (intent === "next_step"
      ? "다음 단계로 넘어갈게요."
      : intent === "prev_step"
        ? "이전 단계로 돌아갈게요."
        : "알겠어요. 조금만 더 자세히 말해줄래요?");

  return { intent, responseText: safeResponse, raw: json };
}

function buildWavBlobFromPCM16Bytes(pcmBytes, sampleRate) {
  const numChannels = 1;
  const bitsPerSample = 16;
  const byteRate = sampleRate * numChannels * (bitsPerSample / 8);
  const blockAlign = numChannels * (bitsPerSample / 8);
  const dataSize = pcmBytes.byteLength;

  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);

  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + dataSize, true);
  writeString(view, 8, "WAVE");

  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);

  writeString(view, 36, "data");
  view.setUint32(40, dataSize, true);

  new Uint8Array(buffer, 44).set(pcmBytes);

  return new Blob([buffer], { type: "audio/wav" });
}

function writeString(view, offset, str) {
  for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
}

function concatUint8Arrays(chunks) {
  const total = chunks.reduce((acc, c) => acc + c.length, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const c of chunks) {
    out.set(c, offset);
    offset += c.length;
  }
  return out;
}

class TTSStreamPlayer {
  constructor() {
    this.audioContext = null;
    this.isPlaying = false;
    this.leftoverChunk = null;
    this.nextStartTime = 0;
  }

  async playAndCollect({ text, tone, textLang, speedFactor }) {
    if (this.isPlaying) this.stop();
    this.isPlaying = true;
    this.leftoverChunk = null;

    const pcmChunks = [];

    try {
      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (this.audioContext.state === "suspended") {
        await this.audioContext.resume();
      }
      this.nextStartTime = this.audioContext.currentTime;

      const payload = {
        text,
        tone: tone || "kiwi",
        text_lang: textLang || "ko",
        speed_factor: typeof speedFactor === "number" ? speedFactor : 1.0,
      };

      const response = await fetch(`${TTS_BASE_URL}${TTS_ENDPOINT}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const txt = await response.text().catch(() => "");
        throw new Error(`TTS(stream) HTTP ${response.status}: ${txt}`);
      }
      if (!response.body) throw new Error("TTS(stream) 응답에 ReadableStream이 없습니다.");

      const sampleRate = parseInt(response.headers.get("X-Sample-Rate") || "32000", 10);
      const reader = response.body.getReader();

      while (this.isPlaying) {
        const { done, value } = await reader.read();
        if (done) break;
        if (value && value.length) this.processChunk(value, sampleRate, pcmChunks);
      }

      this.leftoverChunk = null;

      const pcmAll = concatUint8Arrays(pcmChunks);
      return buildWavBlobFromPCM16Bytes(pcmAll, sampleRate);
    } finally {
      this.isPlaying = false;
    }
  }

  processChunk(incomingChunk, sampleRate, pcmChunks) {
    if (!this.audioContext) return;

    let chunkToProcess = incomingChunk;

    if (this.leftoverChunk) {
      const combined = new Uint8Array(this.leftoverChunk.length + incomingChunk.length);
      combined.set(this.leftoverChunk);
      combined.set(incomingChunk, this.leftoverChunk.length);
      chunkToProcess = combined;
      this.leftoverChunk = null;
    }

    const remainder = chunkToProcess.length % 2;
    if (remainder !== 0) {
      this.leftoverChunk = chunkToProcess.slice(chunkToProcess.length - remainder);
      chunkToProcess = chunkToProcess.slice(0, chunkToProcess.length - remainder);
    }

    if (chunkToProcess.byteLength === 0) return;

    pcmChunks.push(chunkToProcess.slice(0));

    const int16Data = new Int16Array(
      chunkToProcess.buffer,
      chunkToProcess.byteOffset,
      chunkToProcess.byteLength / 2
    );
    const float32Data = new Float32Array(int16Data.length);
    for (let i = 0; i < int16Data.length; i++) {
      float32Data[i] = int16Data[i] / 32768.0;
    }

    const audioBuffer = this.audioContext.createBuffer(1, float32Data.length, sampleRate);
    audioBuffer.getChannelData(0).set(float32Data);

    const source = this.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.audioContext.destination);

    if (this.nextStartTime < this.audioContext.currentTime) {
      this.nextStartTime = this.audioContext.currentTime + 0.02;
    }

    source.start(this.nextStartTime);
    this.nextStartTime += audioBuffer.duration;
  }

  stop() {
    this.isPlaying = false;
    this.leftoverChunk = null;
    if (this.audioContext) {
      this.audioContext.close().catch(() => {});
      this.audioContext = null;
    }
  }
}

const ttsStreamPlayer = new TTSStreamPlayer();

export default function CookModeAudioPage() {
  const navigate = useNavigate();
  const location = useLocation();

  // CookModePage에서 전달받은 데이터
  const passedStepIndex = location.state?.currentStepIndex ?? 0;
  const passedRecipeSteps = location.state?.recipeSteps || [];
  const passedRecipe = location.state?.recipe || { name: "레시피 없음" };
  const passedElapsedTime = location.state?.elapsedTime ?? 0;

  const [currentStepIndex, setCurrentStepIndex] = useState(passedStepIndex);
  const [elapsedTime, setElapsedTime] = useState(passedElapsedTime);

  const recipeSteps = passedRecipeSteps.length > 0 ? passedRecipeSteps : [
    { no: 1, desc: "레시피 정보가 없습니다." },
  ];

  // 타이머
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${String(hrs).padStart(2, "0")}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  // Chat messages
  const [messages, setMessages] = useState([]);
  const [errorMsg, setErrorMsg] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [vadState, setVadState] = useState("idle");
  const [pipelineBusy, setPipelineBusy] = useState(false);

  const supported = useMemo(() => {
    return !!(
      navigator?.mediaDevices?.getUserMedia &&
      typeof window !== "undefined" &&
      typeof window.MediaRecorder !== "undefined"
    );
  }, []);

  // Audio refs
  const streamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const rafRef = useRef(null);

  // VAD refs
  const vadStateRef = useRef("idle");
  const speechStartAtRef = useRef(null);
  const lastAboveAtRef = useRef(null);
  const segStartAtRef = useRef(null);

  // Recorder refs
  const segRecorderRef = useRef(null);
  const segChunksRef = useRef([]);
  const mimeTypeRef = useRef("");

  // Pipeline queue
  const pipelineQueueRef = useRef([]);
  const pipelineRunningRef = useRef(false);

  const ttsAudioRef = useRef(null);

  // 페이지 진입 시 자동으로 녹음 시작
  useEffect(() => {
    startListening();

    return () => {
      stopListening();
      ttsStreamPlayer.stop();
      setMessages((prev) => {
        prev.forEach((m) => {
          if (m.audioUrl) URL.revokeObjectURL(m.audioUrl);
        });
        return [];
      });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function applyIntentToStep(intent) {
    if (intent === "next_step") {
      setCurrentStepIndex((i) => Math.min(i + 1, recipeSteps.length - 1));
    } else if (intent === "prev_step") {
      setCurrentStepIndex((i) => Math.max(i - 1, 0));
    }
  }

  function appendMessage(msg) {
    const id = msg.id || `msg_${Date.now()}_${Math.random().toString(16).slice(2)}`;
    setMessages((prev) => [...prev, { id, ...msg }]);
    return id;
  }

  function patchMessage(id, patch) {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, ...patch } : m)));
  }

  function enqueuePipelineJob({ audioBlob }) {
    pipelineQueueRef.current.push({ audioBlob });
    drainPipelineQueue();
  }

  async function drainPipelineQueue() {
    if (pipelineRunningRef.current) return;
    const job = pipelineQueueRef.current.shift();
    if (!job) return;

    pipelineRunningRef.current = true;
    setPipelineBusy(true);

    const { audioBlob } = job;

    try {
      const sttOut = await sttTranscribeRawBlob(audioBlob);
      const userText = (sttOut.text || "").trim();

      if (!userText) {
        pipelineRunningRef.current = false;
        setPipelineBusy(false);
        drainPipelineQueue();
        return;
      }

      appendMessage({ type: "user", text: userText });

      const currentStepText = recipeSteps[currentStepIndex]?.desc ?? "";
      const llmOut = await llmClassifyAndRespond({
        userText,
        currentStep: currentStepText,
      });

      applyIntentToStep(llmOut.intent);

      const aiMsgId = appendMessage({
        type: "ai",
        text: llmOut.responseText,
        intent: llmOut.intent,
        audioUrl: "",
        status: "tts_generating",
      });

      patchMessage(aiMsgId, { status: "tts_streaming" });

      const wavBlob = await ttsStreamPlayer.playAndCollect({
        text: llmOut.responseText,
        tone: "kiwi",
        textLang: "ko",
        speedFactor: 1.0,
      });

      const ttsUrl = URL.createObjectURL(wavBlob);
      patchMessage(aiMsgId, { audioUrl: ttsUrl, status: "done" });

    } catch (e) {
      setErrorMsg(String(e));
      appendMessage({ type: "ai", text: `⚠️ 오류: ${String(e)}`, status: "error" });
    } finally {
      pipelineRunningRef.current = false;
      setPipelineBusy(false);
      drainPipelineQueue();
    }
  }

  function startSegmentRecording() {
    const stream = streamRef.current;
    if (!stream) return;

    segChunksRef.current = [];

    const mt = mimeTypeRef.current;
    const recorder = new MediaRecorder(
      stream,
      mt && mt !== "browser-default" ? { mimeType: mt } : undefined
    );

    segRecorderRef.current = recorder;

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) segChunksRef.current.push(e.data);
    };

    recorder.onerror = (e) => {
      setErrorMsg(`녹음 오류: ${e?.error?.message || "unknown"}`);
    };

    recorder.onstop = async () => {
      const chunks = segChunksRef.current;
      segChunksRef.current = [];
      segRecorderRef.current = null;

      if (!chunks.length) {
        segStartAtRef.current = null;
        return;
      }

      const audioBlob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });

      const endAt = nowTs();
      const startAt = segStartAtRef.current || endAt;
      const durationMs = Math.max(0, endAt - startAt);

      if (durationMs < VAD_MIN_SPEECH_MS) {
        segStartAtRef.current = null;
        return;
      }

      try {
        enqueuePipelineJob({ audioBlob });
      } catch (e) {
        setErrorMsg(String(e));
        appendMessage({ type: "ai", text: `⚠️ 세그먼트 처리 오류: ${String(e)}`, status: "error" });
      } finally {
        segStartAtRef.current = null;
      }
    };

    recorder.start(250);
  }

  function stopSegmentRecording() {
    try {
      const r = segRecorderRef.current;
      if (r && r.state !== "inactive") {
        try {
          r.requestData?.();
        } catch {}
        r.stop();
      }
    } catch {}
  }

  function setVadStateInternal(next) {
    vadStateRef.current = next;
    setVadState(next);
  }

  function loopVAD() {
    const analyser = analyserRef.current;
    if (!analyser) return;

    const bufferLen = analyser.fftSize;
    const data = new Uint8Array(bufferLen);
    analyser.getByteTimeDomainData(data);

    let sum = 0;
    for (let i = 0; i < data.length; i++) {
      const v = (data[i] - 128) / 128;
      sum += v * v;
    }
    const rms = Math.sqrt(sum / data.length);

    const now = nowTs();
    const isAbove = rms >= VAD_THRESHOLD;

    if (isAbove) {
      lastAboveAtRef.current = now;
      if (vadStateRef.current === "idle") {
        speechStartAtRef.current = now;
        segStartAtRef.current = now;
        setVadStateInternal("speaking");
        startSegmentRecording();
      }
    } else {
      if (vadStateRef.current === "speaking") {
        const lastAbove = lastAboveAtRef.current || now;
        const silentFor = now - lastAbove;
        if (silentFor >= VAD_SILENCE_MS) {
          setVadStateInternal("idle");
          stopSegmentRecording();
        }
      }
    }

    rafRef.current = requestAnimationFrame(loopVAD);
  }

  async function startListening() {
    if (!supported) {
      setErrorMsg("이 브라우저는 마이크/녹음을 지원하지 않아요.");
      return;
    }

    setErrorMsg("");

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;

    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    audioCtxRef.current = audioCtx;

    const source = audioCtx.createMediaStreamSource(stream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 2048;
    analyserRef.current = analyser;

    source.connect(analyser);

    mimeTypeRef.current = pickMimeType() || "browser-default";

    lastAboveAtRef.current = null;
    speechStartAtRef.current = null;
    segStartAtRef.current = null;
    setVadStateInternal("idle");

    setIsListening(true);
    rafRef.current = requestAnimationFrame(loopVAD);
  }

  function stopListening() {
    setIsListening(false);
    setVadStateInternal("idle");

    // RAF 중지
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }

    // 녹음 중지
    stopSegmentRecording();

    // 마이크 스트림 완전히 중지 (핵심!)
    const stream = streamRef.current;
    if (stream) {
      const tracks = stream.getTracks();
      tracks.forEach((track) => {
        track.stop();
        console.log("[stopListening] Track stopped:", track.kind, track.readyState);
      });
      streamRef.current = null;
    }

    // AudioContext 닫기
    const audioCtx = audioCtxRef.current;
    if (audioCtx) {
      if (audioCtx.state !== "closed") {
        audioCtx.close().then(() => {
          console.log("[stopListening] AudioContext closed");
        }).catch(() => {});
      }
      audioCtxRef.current = null;
    }

    analyserRef.current = null;
    console.log("[stopListening] 완료");
  }

  // 버튼 클릭 시 녹음 중지 후 CookModePage로 복귀
  function handleMicClick() {
    // 먼저 녹음 완전히 중지
    stopListening();
    ttsStreamPlayer.stop();

    // 상태 정리 후 페이지 이동
    setTimeout(() => {
      navigate("/cook", {
        state: {
          recipe: passedRecipe,
          currentStepIndex,
          elapsedTime,
        },
      });
    }, 100);
  }

  // RecipeBottomSheet용 steps 포맷
  const formattedSteps = recipeSteps.map((step, index) => ({
    no: step.no || index + 1,
    desc: step.desc || "",
  }));

  return (
    <RecipeLayout
      steps={formattedSteps}
      currentStep={currentStepIndex + 1}
      onStepClick={(index) => setCurrentStepIndex(index)}
    >
      {/* hidden audio element */}
      <audio ref={ttsAudioRef} style={{ display: "none" }} />

      {/* 레시피 제목 */}
      <h1 className="cook-recipe-title">{passedRecipe.name}</h1>

      {/* 소요시간 & 스톱워치 아이콘 */}
      <div className="cook-time-row">
        <span className="cook-time-text">소요시간 {formatTime(elapsedTime)}</span>
        <img
          src="/stopwatch.png"
          alt="스톱워치"
          className="cook-stopwatch-icon"
          onError={(e) => (e.target.style.display = "none")}
        />
      </div>

      {/* 단계 설명 박스 */}
      <div className="cook-step-box">
        <span className="cook-step-label">
          STEP {recipeSteps[currentStepIndex]?.no || currentStepIndex + 1}
        </span>
        <p className="cook-step-description">
          {recipeSteps[currentStepIndex]?.desc || "단계 정보가 없습니다."}
        </p>
      </div>

      {/* 채팅 박스 */}
      <div className="audio-chat-box">
        <div className="audio-chat-messages">
          {messages.map((msg) => (
            <div key={msg.id} className={`audio-chat-bubble ${msg.type}`}>
              <div className="audio-bubble-content">{msg.text}</div>
            </div>
          ))}
        </div>

        {/* 로딩 스피너 */}
        {(isListening || pipelineBusy) && (
          <div className="audio-chat-loading">
            <div className="audio-loading-spinner"></div>
          </div>
        )}
      </div>

      {/* 에러 메시지 */}
      {errorMsg && (
        <div className="audio-error-msg">{errorMsg}</div>
      )}

      {/* 마이크 버튼 */}
      <div className="cook-record-wrapper">
        <button
          className={`cook-record-btn ${isListening ? "recording" : ""}`}
          onClick={handleMicClick}
          disabled={!supported}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
          </svg>
        </button>
      </div>
    </RecipeLayout>
  );
}
