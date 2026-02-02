// src/pages/Chat/ChatPage.jsx
import { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import ButtonRed from "@/components/ButtonRed";
import "./ChatPage.css";

export default function ChatPage() {
  const navigate = useNavigate();
  const location = useLocation();

  // 재생성 버튼에서 넘어온 경우
  const {
    sessionId: existingSessionId,
    existingMessages,
    memberInfo: existingMemberInfo,
    skipToChat,
    fromRegenerate,
  } = location.state || {};

  const [messages, setMessages] = useState(existingMessages || []);
  const [input, setInput] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isThinking, setIsThinking] = useState(false);

  // 플로우 상태
  const [flowState, setFlowState] = useState(
    skipToChat ? "FREE_CHAT" : existingMessages ? "FREE_CHAT" : "LOADING",
  );

  const [familyMembers, setFamilyMembers] = useState({});
  const [selectedMembers, setSelectedMembers] = useState([]);
  const [combinedMemberInfo, setCombinedMemberInfo] = useState(
    existingMemberInfo || null,
  );

  // 레시피 생성 버튼 활성화
  const [hasRecipeGenerated, setHasRecipeGenerated] = useState(
    !!existingMessages || skipToChat,
  );

  const wsRef = useRef(null);
  const sessionIdRef = useRef(existingSessionId || crypto.randomUUID());
  const sessionId = sessionIdRef.current;
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const API_URL = import.meta.env.VITE_API_URL || "http://211.188.62.72:8080";
  const WS_URL = import.meta.env.VITE_WS_URL || "ws://211.188.62.72:8080";

  // 디버깅용
  useEffect(() => {
    console.log("[ChatPage] 세션 ID:", sessionId);
    console.log("[ChatPage] 재생성 여부:", !!existingSessionId);
    console.log("[ChatPage] skipToChat:", skipToChat);
    console.log("[ChatPage] 현재 상태:", flowState);
  }, [sessionId, existingSessionId, skipToChat, flowState]);

  // 스크롤 최하단
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  // 가족 정보 불러오기
  useEffect(() => {
    if (existingMemberInfo || skipToChat) {
      console.log("[ChatPage] 기존 세션 복원 (skipToChat)");
      return;
    }

    console.log("[ChatPage] 가족 정보 로딩 시작...");

    fetch(`${API_URL}/api/user/family`)
      .then((res) => res.json())
      .then((data) => {
        console.log("[ChatPage] 가족 정보 받음:", data);
        setFamilyMembers(data.family_members);

        setMessages([
          {
            role: "assistant",
            content:
              "안녕하세요! 누구를 위한 요리를 만들까요?\n(여러 명 선택 가능)",
            timestamp: new Date().toISOString(),
            showButtons: true,
            buttonType: "select_member",
          },
        ]);

        setFlowState("SELECT_MEMBER");
      })
      .catch((err) => {
        console.error("[ChatPage] 가족 정보 로딩 실패:", err);
        alert("가족 정보를 불러올 수 없습니다.");
      });
  }, [API_URL, existingMemberInfo, skipToChat]);

  // WebSocket 연결
  useEffect(() => {
    if (flowState !== "FREE_CHAT") {
      console.log("[ChatPage] WebSocket 대기 중... 현재:", flowState);
      return;
    }

    console.log("[ChatPage] WebSocket 연결 시작...");
    const ws = new WebSocket(`${WS_URL}/api/chat/ws/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[WebSocket] Connected");
      setIsConnected(true);

      if (combinedMemberInfo) {
        ws.send(
          JSON.stringify({
            type: "init_context",
            member_info: combinedMemberInfo,
          }),
        );

        if (!existingMessages && !skipToChat) {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content:
                '어떤 요리를 만들고 싶으세요? 자유롭게 말씀해주세요!\n예) "매운 찌개 먹고 싶어요", "간식으로 먹을 요리 알려줘"',
              timestamp: new Date().toISOString(),
            },
          ]);
        }
      }
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("[WebSocket] Received:", data);

      if (data.type === "agent_message") {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.content,
            timestamp: new Date().toISOString(),
            image_url: data.image_url,
          },
        ]);
        setIsThinking(false);
        setHasRecipeGenerated(true);
      } else if (data.type === "not_recipe_related") {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.content,
            timestamp: new Date().toISOString(),
            showHomeButton: true,
          },
        ]);
        setIsThinking(false);
        setHasRecipeGenerated(false);
      } else if (data.type === "thinking") {
        setIsThinking(true);
      } else if (data.type === "progress") {
        console.log("[Progress]", data.message);
      } else if (data.type === "error") {
        console.error("Error:", data.message);
        alert(data.message);
        setIsThinking(false);
      }
    };

    ws.onclose = () => {
      console.log("[WebSocket] Disconnected");
      setIsConnected(false);
    };

    ws.onerror = (error) => {
      console.error("[WebSocket] Error:", error);
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [
    flowState,
    combinedMemberInfo,
    sessionId,
    WS_URL,
    existingMessages,
    skipToChat,
  ]);

  // 가족 선택
  const handleSelectMember = (memberName) => {
    setSelectedMembers((prev) =>
      prev.includes(memberName)
        ? prev.filter((name) => name !== memberName)
        : [...prev, memberName],
    );
  };

  // 선택 완료
  const handleConfirmSelection = async () => {
    if (selectedMembers.length === 0) {
      alert("최소 1명을 선택해주세요.");
      return;
    }

    try {
      const memberInfoPromises = selectedMembers.map((name) =>
        fetch(`${API_URL}/api/user/family/${name}`).then((r) => r.json()),
      );

      const allMemberInfo = await Promise.all(memberInfoPromises);

      const combined = {
        names: selectedMembers,
        allergies: [
          ...new Set(allMemberInfo.flatMap((m) => m.allergies || [])),
        ],
        dislikes: [...new Set(allMemberInfo.flatMap((m) => m.dislikes || []))],
        cooking_tools: [
          ...new Set(allMemberInfo.flatMap((m) => m.cooking_tools || [])),
        ],
      };

      setCombinedMemberInfo(combined);

      const namesText = selectedMembers.join(", ");
      const infoText =
        `[ ${namesText} ]님을 위한 요리 정보\n\n` +
        `- 알레르기: ${combined.allergies.join(", ") || "없음"}\n\n` +
        `- 싫어하는 음식: ${combined.dislikes.join(", ") || "없음"}\n\n` +
        `- 사용 가능한 조리도구\n: ${combined.cooking_tools.join(", ")}\n\n` +
        `이 정보가 맞나요?`;

      setMessages((prev) => [
        ...prev,
        {
          role: "user",
          content: namesText,
          timestamp: new Date().toISOString(),
        },
        {
          role: "assistant",
          content: infoText,
          timestamp: new Date().toISOString(),
          showButtons: true,
          buttonType: "confirm_info",
        },
      ]);

      setFlowState("CONFIRM_INFO");
    } catch (error) {
      console.error("[ChatPage] 멤버 정보 로딩 실패:", error);
      alert("멤버 정보를 불러올 수 없습니다.");
    }
  };

  // 정보 확인
  const handleConfirmInfo = (confirmed) => {
    if (confirmed) {
      setMessages((prev) => [
        ...prev,
        {
          role: "user",
          content: "예, 맞아요",
          timestamp: new Date().toISOString(),
        },
      ]);

      setFlowState("FREE_CHAT");
      console.log("[ChatPage] 자유 대화 상태로 전환");
    } else {
      console.log("[ChatPage] 마이페이지로 이동");
      navigate("/mypage");
    }
  };

  // 메시지 전송
  const handleSend = () => {
    if (!input.trim() || !isConnected || isThinking) return;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: input,
        timestamp: new Date().toISOString(),
      },
    ]);

    wsRef.current.send(
      JSON.stringify({
        type: "user_message",
        content: input,
      }),
    );

    setInput("");
    setIsThinking(true);
  };

  // 레시피 생성
  const handleGenerateRecipe = () => {
    if (!combinedMemberInfo?.names?.length) {
      alert("가족 정보가 없습니다.");
      return;
    }

    const validMessages = messages.filter(
      (m) => m.role && m.content && typeof m.content === "string",
    );

    console.log("[ChatPage] 레시피 생성 버튼 클릭");

    navigate("/loading", {
      state: {
        memberInfo: combinedMemberInfo,
        chatHistory: validMessages,
        sessionId: sessionId,
        isRegeneration: !!fromRegenerate,
      },
    });
  };

  // textarea 자동 높이 조절
  const handleTextareaChange = (e) => {
    setInput(e.target.value);

    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "48px";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  };

  return (
    <div className="chat-page">
      {/* 헤더 */}
      <button className="header-closed" onClick={() => navigate(-1)}>
        <img src="/exit-icon.png" alt="닫기" className="closed-icon" />
      </button>
      <div className="chat-header">
        <h1>조리 전, 마지막으로 확인할게요</h1>
      </div>

      {/* 메시지 영역 */}
      <div className="chat-content">
        {flowState === "LOADING" && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <p>로딩 중...</p>
          </div>
        )}

        <div className="messages">
          {messages.map((msg, idx) => (
            <div key={idx}>
              <div className={`message ${msg.role}`}>
                <div className="bubble">{msg.content}</div>
              </div>

              {msg.image && (
                <div className="message-image-wrapper">
                  <img
                    src={msg.image}
                    alt="레시피 이미지"
                    className="message-recipe-image"
                    onError={(e) => {
                      e.target.style.display = "none";
                    }}
                  />
                </div>
              )}

              {msg.showHomeButton && (
                <div className="home-button-wrapper">
                  <button
                    className="btn-confirm-selection"
                    onClick={() => navigate("/home")}
                  >
                    외부 챗봇으로 이동
                  </button>
                </div>
              )}

              {msg.showButtons && msg.buttonType === "select_member" && (
                <div className="selection-area">
                  <div className="button-group">
                    {Object.keys(familyMembers).map((name) => (
                      <button
                        key={name}
                        className={`btn-option ${selectedMembers.includes(name) ? "selected" : ""}`}
                        onClick={() => handleSelectMember(name)}
                      >
                        {name}
                      </button>
                    ))}
                  </div>

                  <button
                    className="btn-confirm-selection"
                    onClick={handleConfirmSelection}
                    disabled={selectedMembers.length === 0}
                  >
                    선택 완료
                  </button>
                </div>
              )}

              {msg.showButtons && msg.buttonType === "confirm_info" && (
                <div className="button-group confirm-group">
                  <button
                    className="btn-option btn-confirm"
                    onClick={() => handleConfirmInfo(true)}
                  >
                    예, 맞아요
                  </button>
                  <button
                    className="btn-option btn-edit"
                    onClick={() => handleConfirmInfo(false)}
                  >
                    수정이 필요해요
                  </button>
                </div>
              )}
            </div>
          ))}

          {isThinking && (
            <div className="message assistant">
              <div className="bubble thinking">
                <div className="thinking-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span>생각 중...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 레시피 생성 버튼 */}
      {flowState === "FREE_CHAT" && (
        <div className="action-area">
          <ButtonRed
            onClick={handleGenerateRecipe}
            disabled={!hasRecipeGenerated || isThinking}
          >
            대화 종료하고 레시피 생성하기
          </ButtonRed>
        </div>
      )}

      {/* 입력창 */}
      {flowState === "FREE_CHAT" && (
        <div className="chat-input-area">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleTextareaChange}
            onKeyPress={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={isConnected ? "어떤 요리를 원하세요?" : "연결 중..."}
            disabled={!isConnected || isThinking}
            rows={1}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || !isConnected || isThinking}
          >
            전송
          </button>
        </div>
      )}
    </div>
  );
}
