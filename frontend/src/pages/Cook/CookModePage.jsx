// src/pages/Cook/CookModePage.jsx
import { useState, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useCookingAgent } from "@/features/chat/hooks/useCookingAgent";
import "./CookModePage.css";

export default function CookModePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { recipe } = location.state || {};

  const sessionId = useRef(crypto.randomUUID()).current;
  const fileInputRef = useRef(null);
  const [textInput, setTextInput] = useState("");

  const {
    currentStep,
    totalSteps,
    response,
    audioUrl,
    isConnected,
    isThinking,
    sendText,
    uploadVoice,
    goNext,
    goPrev,
  } = useCookingAgent(sessionId, recipe);

  // 레시피가 없으면 홈으로
  if (!recipe) {
    navigate("/home", { replace: true });
    return null;
  }

  const currentStepData = recipe.steps?.[currentStep];

  // 텍스트 입력 전송
  const handleSendText = () => {
    if (!textInput.trim() || isThinking) return;
    sendText(textInput);
    setTextInput("");
  };

  // 음성 파일 업로드
  const handleVoiceUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      await uploadVoice(file);
    } catch (error) {
      console.error("음성 업로드 실패:", error);
      alert("음성 처리에 실패했습니다.");
    }

    // 파일 입력 초기화
    e.target.value = "";
  };

  // 조리 완료
  const handleComplete = () => {
    navigate("/cook-complete", {
      state: { recipe },
    });
  };

  return (
    <div className="cook-mode-page">
      {/* 헤더 */}
      <div className="cook-header">
        <button className="back-button" onClick={() => navigate(-1)}>
          ←
        </button>
        <div className="cook-header-info">
          <h1>🎙️ 조리모드</h1>
          <div className="step-indicator">
            {currentStep + 1} / {totalSteps} 단계
          </div>
          <div className="connection-status">
            {isConnected ? "연결됨 ✅" : "연결 끊김 ❌"}
          </div>
        </div>
      </div>

      {/* 현재 단계 */}
      <div className="cook-content">
        <div className="step-display">
          <div className="step-number">
            {currentStepData?.no || currentStep + 1}단계
          </div>

          {isThinking ? (
            <div className="thinking-indicator">
              <div className="spinner"></div>
              <p>처리 중...</p>
            </div>
          ) : (
            <div className="step-description">
              {response ||
                currentStepData?.desc ||
                "단계 정보를 불러오는 중..."}
            </div>
          )}
        </div>

        {/* 음성 재생 */}
        {audioUrl && !isThinking && (
          <div className="audio-player">
            <audio controls autoPlay key={audioUrl}>
              <source src={audioUrl} type="audio/wav" />
            </audio>
          </div>
        )}
      </div>

      {/* 컨트롤 영역 */}
      <div className="cook-controls">
        {/* 이전/다음 버튼 */}
        <div className="nav-buttons">
          <button
            className="btn-nav btn-prev"
            onClick={goPrev}
            disabled={isThinking || !isConnected}
          >
            ⬅️ 이전
          </button>

          {currentStep === totalSteps - 1 ? (
            <button
              className="btn-nav btn-complete"
              onClick={handleComplete}
              disabled={isThinking}
            >
              완료 ✨
            </button>
          ) : (
            <button
              className="btn-nav btn-next"
              onClick={goNext}
              disabled={isThinking || !isConnected}
            >
              다음 ➡️
            </button>
          )}
        </div>

        {/* 음성 입력 */}
        <div className="voice-input-section">
          <input
            ref={fileInputRef}
            type="file"
            accept=".wav,.m4a,.mp3"
            onChange={handleVoiceUpload}
            style={{ display: "none" }}
          />
          <button
            className="btn-voice"
            onClick={() => fileInputRef.current?.click()}
            disabled={isThinking || !isConnected}
          >
            🎤 음성으로 명령하기
          </button>
          <p className="voice-hint">
            "다음", "재료 대체", "탔어요" 등을 말해보세요
          </p>
        </div>

        {/* 텍스트 입력 */}
        <div className="text-input-section">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSendText()}
            placeholder="또는 텍스트로 입력 (예: 다음, 이전, 재료 없어)"
            disabled={isThinking || !isConnected}
          />
          <button
            onClick={handleSendText}
            disabled={isThinking || !isConnected || !textInput.trim()}
          >
            전송
          </button>
        </div>
      </div>
    </div>
  );
}
