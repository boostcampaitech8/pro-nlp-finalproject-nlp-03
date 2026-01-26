# features/chat/router.py
"""
Chat Agent WebSocket 라우터
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict

from core.websocket import manager
from core.dependencies import get_rag_system, get_user_profile
from core.exceptions import RAGNotAvailableError
from features.chat.agent import create_chat_agent
from features.chat.schemas import ChatMessage


router = APIRouter()

# 세션별 상태 저장
chat_sessions: Dict[str, dict] = {}


@router.websocket("/ws/{session_id}")
async def chat_websocket(
    websocket: WebSocket,
    session_id: str,
    rag_system = Depends(get_rag_system),
    user_profile = Depends(get_user_profile)
):
    """채팅 Agent WebSocket"""
    
    if not rag_system:
        await websocket.close(code=1011, reason="RAG system not available")
        return
    
    await manager.connect(websocket, session_id)
    
    # Agent 생성
    agent = create_chat_agent(rag_system)
    
    # 초기 상태
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "messages": [],
            "user_constraints": {
                "allergies": user_profile["allergies"],
                "dislike": user_profile["dislike"]
            },
            "search_query": "",
            "retrieved_recipes": [],
            "filtered_recipes": [],
            "selected_recipe": {},
            "response": "",
            "step": "start"
        }
    
    await manager.send_message(session_id, {
        "type": "agent_message",
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "user_message":
                user_message = data["content"]
                
                # 상태에 메시지 추가
                chat_sessions[session_id]["messages"].append({
                    "role": "user",
                    "content": user_message
                })
                
                # Agent 실행 (스트리밍)
                await manager.send_message(session_id, {
                    "type": "thinking",
                    "message": "생각 중..."
                })
                
                # 각 노드의 진행 상황 전송
                async for event in agent.astream_events(
                    chat_sessions[session_id],
                    version="v1"
                ):
                    if event["event"] == "on_chain_start":
                        node_name = event["name"]
                        status_msg = {
                            "understand": "의도 파악 중...",
                            "search": "레시피 검색 중...",
                            "filter": "제약 조건 필터링 중...",
                            "generate": "응답 생성 중..."
                        }.get(node_name, "처리 중...")
                        
                        await manager.send_message(session_id, {
                            "type": "progress",
                            "step": node_name,
                            "message": status_msg
                        })
                
                # 최종 상태
                final_state = await agent.ainvoke(chat_sessions[session_id])
                chat_sessions[session_id] = final_state
                
                # 응답 파싱
                from utils.parser import parse_recommendation
                
                response = final_state["response"]
                recipe = final_state.get("selected_recipe", {})
                recipe_info = parse_recommendation(response)
                
                # 응답 전송
                await manager.send_message(session_id, {
                    "type": "agent_message",
                    "content": response,
                    "recipe_info": recipe_info
                })
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"Chat WebSocket 오류: {e}")
        import traceback
        traceback.print_exc()
        manager.disconnect(session_id)