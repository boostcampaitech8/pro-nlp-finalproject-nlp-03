// src/pages/Chat/ChatPage.jsx
import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./ChatPage.css";

export default function ChatPage() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isThinking, setIsThinking] = useState(false);

  // 플로우 상태
  const [flowState, setFlowState] = useState("LOADING"); // LOADING, SELECT_MEMBER, CONFIRM_INFO, FREE_CHAT
  const [familyMembers, setFamilyMembers] = useState({});
  const [selectedMembers, setSelectedMembers] = useState([]);
  const [combinedMemberInfo, setCombinedMemberInfo] = useState(null);

  const wsRef = useRef(null);
  const sessionId = useRef(crypto.randomUUID()).current;

  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

  // 가족 정보 불러오기
  useEffect(() => {
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
  }, [API_URL]);

  // WebSocket 연결 (FREE_CHAT 상태일 때만)
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

      // 컨텍스트만 전송 (자동 추천 X)
      if (combinedMemberInfo) {
        ws.send(
          JSON.stringify({
            type: "init_context",
            member_info: combinedMemberInfo,
          }),
        );

        // 자유 대화 시작 안내
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              '어떤 요리를 만들고 싶으세요? 자유롭게 말씀해주세요! \n\n예: "매운 찌개 먹고 싶어요", \n"간단한 요리 알려줘"',
            timestamp: new Date().toISOString(),
          },
        ]);
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
          },
        ]);
        setIsThinking(false);
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
  }, [flowState, combinedMemberInfo, sessionId, WS_URL]);

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
        `${namesText}님을 위한 요리 정보:\n` +
        `- 알레르기: ${combined.allergies.join(", ") || "없음"}\n` +
        `- 싫어하는 음식: ${combined.dislikes.join(", ") || "없음"}\n` +
        `- 사용 가능한 조리도구: ${combined.cooking_tools.join(", ")}`;

      setMessages((prev) => [
        ...prev,
        {
          role: "user",
          content: namesText,
          timestamp: new Date().toISOString(),
        },
        {
          role: "assistant",
          content: infoText + "\n\n이 정보가 맞나요?",
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
    } else {
      setMessages((prev) => [
        ...prev,
        {
          role: "user",
          content: "아니요, 수정할게요",
          timestamp: new Date().toISOString(),
        },
      ]);
    }

    // 자유 대화 상태로 전환
    setFlowState("FREE_CHAT");
    console.log("[ChatPage] 자유 대화 상태로 전환");
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

    if (validMessages.length < 4) {
      alert("대화를 좀 더 진행해주세요! (최소 4개 메시지)");
      return;
    }

    console.log("[ChatPage] 레시피 생성 시작...");
    console.log("- 대화 수:", validMessages.length);
    console.log("- 가족:", combinedMemberInfo.names);

    // LoadingPage로 이동
    navigate("/loading", {
      state: {
        memberInfo: combinedMemberInfo,
        chatHistory: validMessages,
      },
    });
  };

  return (
    <div className="chat-page">
      {/* 헤더 */}
      <div className="chat-header">
        <button className="back-button" onClick={() => navigate(-1)}>
          ←
        </button>
        <h1>
          {flowState === "FREE_CHAT"
            ? "어떤 요리를 만들까요?"
            : "조리 전, 마지막으로 확인할게요"}
        </h1>
        {flowState === "FREE_CHAT" && (
          <div className="connection-status">{isConnected ? "🟢" : "🔴"}</div>
        )}
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

              {/* 가족 선택 버튼 */}
              {msg.showButtons && msg.buttonType === "select_member" && (
                <div className="selection-area">
                  <div className="button-group">
                    {Object.keys(familyMembers).map((name) => (
                      <button
                        key={name}
                        className={`btn-option ${selectedMembers.includes(name) ? "selected" : ""}`}
                        onClick={() => handleSelectMember(name)}
                      >
                        {selectedMembers.includes(name) && "✓ "}
                        {name} ({familyMembers[name].role})
                      </button>
                    ))}
                  </div>

                  <button
                    className="btn-confirm-selection"
                    onClick={handleConfirmSelection}
                    disabled={selectedMembers.length === 0}
                  >
                    선택 완료 ({selectedMembers.length}명)
                  </button>
                </div>
              )}

              {/* 정보 확인 버튼 */}
              {msg.showButtons && msg.buttonType === "confirm_info" && (
                <div className="button-group">
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
                    아니요, 수정할게요
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
        </div>
      </div>

      {/* 레시피 생성 버튼 - FREE_CHAT 상태에서 항상 표시 */}
      {flowState === "FREE_CHAT" && (
        <div className="action-area">
          <button
            className="btn-generate-primary"
            onClick={handleGenerateRecipe}
            disabled={isThinking || messages.length < 4}
          >
            레시피 생성하기
          </button>
        </div>
      )}

      {/* 입력창 */}
      {flowState === "FREE_CHAT" && (
        <div className="chat-input-area">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSend()}
            placeholder={isConnected ? "어떤 요리를 원하세요?" : "연결 중..."}
            disabled={!isConnected || isThinking}
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
