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
  const [lastRecommendation, setLastRecommendation] = useState(null);
  
  // 플로우 상태
  const [flowState, setFlowState] = useState('LOADING'); // LOADING, SELECT_MEMBER, CONFIRM_INFO, CHAT
  const [familyMembers, setFamilyMembers] = useState({});
  const [selectedMembers, setSelectedMembers] = useState([]); // 복수 선택
  const [combinedMemberInfo, setCombinedMemberInfo] = useState(null);
  
  const wsRef = useRef(null);
  const sessionId = useRef(crypto.randomUUID()).current;
  
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

  // 가족 정보 불러오기
  useEffect(() => {
    console.log('[ChatPage] 가족 정보 로딩 시작...');
    
    fetch(`${API_URL}/api/user/family`)
      .then(res => res.json())
      .then(data => {
        console.log('[ChatPage] 가족 정보 받음:', data);
        setFamilyMembers(data.family_members);
        
        // 환영 메시지 추가
        setMessages([{
          role: 'assistant',
          content: '안녕하세요! 누구를 위한 요리를 만들까요?\n(여러 명 선택 가능)',
          timestamp: new Date().toISOString(),
          showButtons: true,
          buttonType: 'select_member'
        }]);
        
        setFlowState('SELECT_MEMBER');
        console.log('[ChatPage] 가족 선택 상태로 전환');
      })
      .catch(err => {
        console.error('[ChatPage] 가족 정보 로딩 실패:', err);
        alert('가족 정보를 불러올 수 없습니다.');
      });
  }, [API_URL]);

  // WebSocket 연결 (CHAT 상태일 때만)
  useEffect(() => {
    if (flowState !== 'CHAT') {
      console.log('[ChatPage] WebSocket 연결 대기 중... 현재 상태:', flowState);
      return;
    }

    console.log('[ChatPage] WebSocket 연결 시작...');
    const ws = new WebSocket(`${WS_URL}/api/chat/ws/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[WebSocket] Connected');
      setIsConnected(true);
      
      // 초기 컨텍스트 전송 & 자동 추천 요청
      if (combinedMemberInfo) {
        // 추천 시작 메시지 먼저 추가
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: '레시피를 추천해드릴게요!',
          timestamp: new Date().toISOString()
        }]);
        
        // 컨텍스트 전송
        ws.send(JSON.stringify({
          type: 'init_context',
          member_info: combinedMemberInfo
        }));
        
        // 자동 추천 요청
        setIsThinking(true);
        ws.send(JSON.stringify({
          type: 'user_message',
          content: '오늘 날씨와 가족 정보를 고려해서 레시피를 추천해주세요.'
        }));
      }
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('[WebSocket] Received:', data);

      if (data.type === 'agent_message') {
        // ✅ 전체 content를 저장 (매우 중요!)
        const newMessage = {
          role: 'assistant',
          content: data.content,  // ← 전체 텍스트 (재료, 조리법 포함!)
          timestamp: new Date().toISOString()
        };
        
        // recipeInfo는 메타데이터로만 사용
        if (data.recipe_info) {
          newMessage.recipeInfo = data.recipe_info;
          setLastRecommendation(data.recipe_info);
        }
        
        setMessages(prev => [...prev, newMessage]);

        setIsThinking(false);
      } 
      
      else if (data.type === 'thinking') {
        setIsThinking(true);
      }
      else if (data.type === 'progress') {
        console.log('[Progress]', data.message);
      }
      else if (data.type === 'error') {
        console.error('Error:', data.message);
        alert(data.message);
        setIsThinking(false);
      }
    };

    ws.onclose = () => {
      console.log('[WebSocket] Disconnected');
      setIsConnected(false);
    };

    ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [flowState, combinedMemberInfo, sessionId, WS_URL]);

  // 가족 구성원 선택/해제 (복수 선택)
  const handleSelectMember = (memberName) => {
    console.log('[ChatPage] 가족 선택/해제:', memberName);
    
    setSelectedMembers(prev => {
      if (prev.includes(memberName)) {
        // 이미 선택됨 -> 제거
        return prev.filter(name => name !== memberName);
      } else {
        // 새로 선택
        return [...prev, memberName];
      }
    });
  };

  // 선택 완료
  const handleConfirmSelection = async () => {
    if (selectedMembers.length === 0) {
      alert('최소 1명을 선택해주세요.');
      return;
    }

    console.log('[ChatPage] 선택 완료:', selectedMembers);

    try {
      // 선택된 모든 멤버 정보 가져오기
      const memberInfoPromises = selectedMembers.map(name =>
        fetch(`${API_URL}/api/user/family/${name}`).then(r => r.json())
      );
      
      const allMemberInfo = await Promise.all(memberInfoPromises);
      
      // 모든 정보 합치기
      const combined = {
        names: selectedMembers,
        allergies: [...new Set(allMemberInfo.flatMap(m => m.allergies || []))],
        dislikes: [...new Set(allMemberInfo.flatMap(m => m.dislikes || []))],
        cooking_tools: [...new Set(allMemberInfo.flatMap(m => m.cooking_tools || []))]
      };
      
      console.log('[ChatPage] 합쳐진 정보:', combined);
      setCombinedMemberInfo(combined);
      
      // 개인화 정보 메시지 추가
      const namesText = selectedMembers.join(', ');
      const infoText = `${namesText}님을 위한 요리 정보:\n` +
        `- 알레르기: ${combined.allergies.join(', ') || '없음'}\n` +
        `- 싫어하는 음식: ${combined.dislikes.join(', ') || '없음'}\n` +
        `- 사용 가능한 조리도구: ${combined.cooking_tools.join(', ')}`;
      
      setMessages(prev => [...prev, 
        {
          role: 'user',
          content: namesText,
          timestamp: new Date().toISOString()
        },
        {
          role: 'assistant',
          content: infoText + '\n\n이 정보가 맞나요?',
          timestamp: new Date().toISOString(),
          showButtons: true,
          buttonType: 'confirm_info'
        }
      ]);
      
      setFlowState('CONFIRM_INFO');
      console.log('[ChatPage] 정보 확인 상태로 전환');
    } catch (error) {
      console.error('[ChatPage] 멤버 정보 로딩 실패:', error);
      alert('멤버 정보를 불러올 수 없습니다.');
    }
  };

  // 정보 확인
  const handleConfirmInfo = async (confirmed) => {
    console.log('[ChatPage] 정보 확인:', confirmed);
    
    if (confirmed) {
      setMessages(prev => [...prev, {
        role: 'user',
        content: '예, 맞아요',
        timestamp: new Date().toISOString()
      }]);
      
      // 그 다음 CHAT 상태로 전환
      setFlowState('CHAT');
      console.log('[ChatPage] 채팅 상태로 전환 - 자동 추천 시작');
    } else {
      setMessages(prev => [...prev,
        {
          role: 'user',
          content: '아니요, 수정할게요',
          timestamp: new Date().toISOString()
        },
        {
          role: 'assistant',
          content: '알겠습니다. 어떤 정보를 수정하시겠어요?',
          timestamp: new Date().toISOString()
        }
      ]);
      
      setFlowState('CHAT');
    }
  };

  // 메시지 전송
  const handleSend = () => {
    if (!input.trim() || !isConnected || isThinking) return;

    setMessages(prev => [...prev, {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }]);

    wsRef.current.send(JSON.stringify({
      type: 'user_message',
      content: input
    }));

    setInput("");
    setIsThinking(true);
  };

  // 레시피 생성
  const handleGenerateRecipe = async () => {
    if (!lastRecommendation) return;

    if (!combinedMemberInfo?.names?.length) {
      alert('가족 정보가 없습니다.');
      return;
    }

    const validMessages = messages.filter(m => 
      m.role && m.content && typeof m.content === 'string'
    );

    if (validMessages.length < 2) {
      alert('대화 내용이 충분하지 않습니다.');
      return;
    }

    console.log('[ChatPage] 로딩 페이지로 이동...');
    
    // LoadingPage로 필요한 데이터 전달 (API는 LoadingPage에서 호출!)
    navigate("/loading", {
      state: { 
        recipeTitle: lastRecommendation.title,
        memberInfo: combinedMemberInfo,
        chatHistory: validMessages
      }
    });
  };

  console.log('[ChatPage] 현재 상태:', {
    flowState,
    messagesCount: messages.length,
    familyMembersLoaded: Object.keys(familyMembers).length > 0,
    selectedMembersCount: selectedMembers.length
  });

  return (
    <div className="chat-page">
      {/* 헤더 */}
      <div className="chat-header">
        <button className="back-button" onClick={() => navigate(-1)}>
          ←
        </button>
        <h1>조리 전, 마지막으로 확인할게요</h1>
        {flowState === 'CHAT' && (
          <div className="connection-status">
            {isConnected ? '🟢' : '🔴'}
          </div>
        )}
      </div>

      {/* 메시지 영역 */}
      <div className="chat-content">
        {flowState === 'LOADING' && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <p>로딩 중...</p>
          </div>
        )}

        <div className="messages">
          {messages.map((msg, idx) => (
            <div key={idx}>
              <div className={`message ${msg.role}`}>
                <div className="bubble">
                  {msg.content}
                </div>
                {msg.recipeInfo && (
                  <div className="recipe-card">
                    <h4>{msg.recipeInfo.title}</h4>
                    <div className="recipe-meta">
                      <span>⏱️ {msg.recipeInfo.cook_time}</span>
                      <span>📊 {msg.recipeInfo.level}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* 가족 선택 버튼 (복수 선택) */}
              {msg.showButtons && msg.buttonType === 'select_member' && (
                <div className="selection-area">
                  <div className="button-group">
                    {Object.keys(familyMembers).map(name => (
                      <button
                        key={name}
                        className={`btn-option ${selectedMembers.includes(name) ? 'selected' : ''}`}
                        onClick={() => handleSelectMember(name)}
                      >
                        {selectedMembers.includes(name) && '✓ '}
                        {name} ({familyMembers[name].role})
                      </button>
                    ))}
                  </div>
                  
                  {/* 선택 완료 버튼 */}
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
              {msg.showButtons && msg.buttonType === 'confirm_info' && (
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
                <span>레시피 추천 중...</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 레시피 생성 버튼 */}
      {lastRecommendation && (
        <div className="generate-section">
          <div className="recommendation-info">
            <span>현재 추천: <strong>{lastRecommendation.title}</strong></span>
          </div>
          <button 
            className="btn-generate"
            onClick={handleGenerateRecipe}
            disabled={isThinking}
          >
            대화 종료하고 레시피 생성하기
          </button>
        </div>
      )}

      {/* 입력창 */}
      {flowState === 'CHAT' && (
        <div className="chat-input-area">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder={isConnected ? "메시지를 입력하세요..." : "연결 중..."}
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