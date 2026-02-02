# backend/features/chat/router.py
"""
Chat Agent WebSocket 라우터 - Adaptive RAG
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict
import json
import asyncio
import time

from core.websocket import manager
from core.dependencies import get_rag_system, get_user_profile
from features.chat.agent import create_chat_agent

router = APIRouter()

chat_sessions: Dict[str, dict] = {}

@router.websocket("/ws/{session_id}")
async def chat_websocket(
    websocket: WebSocket,
    session_id: str,
    rag_system = Depends(get_rag_system),
    user_profile = Depends(get_user_profile)
):
    """채팅 Agent WebSocket - Adaptive RAG"""
    
    await websocket.accept()
    print(f"[WS] Connected: {session_id}")
    
    if not rag_system:
        print("[WS] RAG 시스템 없음")
        await websocket.send_json({
            "type": "error",
            "message": "RAG 시스템을 사용할 수 없습니다."
        })
        await websocket.close()
        return
    
    try:
        agent = create_chat_agent(rag_system)
        if not agent:
            raise ValueError("Agent 생성 실패")
        print("[WS] Adaptive RAG Agent 생성 완료")
    except Exception as e:
        print(f"[WS] Agent 생성 에러: {e}")
        import traceback
        traceback.print_exc()
        await websocket.send_json({
            "type": "error",
            "message": f"Agent 생성 실패: {str(e)}"
        })
        await websocket.close()
        return
    
    manager.active_connections[session_id] = websocket
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "messages": [],
            "user_constraints": {}
        }
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            print(f"[WS] 메시지 수신: {msg_type}")
            
            if msg_type == "init_context":
                member_info = message.get("member_info", {})
                chat_sessions[session_id]["user_constraints"] = member_info
                print(f"[WS] 컨텍스트 설정: {member_info.get('names', [])}")
                continue
            
            elif msg_type == "user_message":
                content = message.get("content", "")
                print(f"[WS] 사용자 메시지: {content}")
                
                start_time = time.time()
                
                chat_sessions[session_id]["messages"].append({
                    "role": "user",
                    "content": content
                })
                
                chat_history = [
                    f"{msg['role']}: {msg['content']}"
                    for msg in chat_sessions[session_id]["messages"]
                ]
                
                await websocket.send_json({
                    "type": "thinking",
                    "message": "생각 중..."
                })
                
                agent_state = {
                    "question": content,
                    "original_question": content,
                    "chat_history": chat_history,
                    "documents": [],
                    "generation": "",
                    "web_search_needed": "no",
                    "user_constraints": chat_sessions[session_id]["user_constraints"],
                    "constraint_warning": ""
                }

                print(f"[WS] user_constraints: {chat_sessions[session_id]['user_constraints']}")
                
                async def progress_notifier():
                    steps = [
                        (0, "쿼리 재작성 중..."),
                        (3, "레시피 검색 중..."),
                        (6, "관련성 평가 중..."),
                        (10, "답변 생성 중..."),
                        (15, "거의 완료..."),
                    ]
                    
                    for delay, msg in steps:
                        await asyncio.sleep(delay if delay == 0 else 3)
                        elapsed_now = time.time() - start_time
                        if elapsed_now < 20:
                            await websocket.send_json({
                                "type": "progress",
                                "message": f"{msg} ({int(elapsed_now)}초)"
                            })
                        else:
                            break
                
                notifier_task = asyncio.create_task(progress_notifier())
                
                try:
                    async def run_agent():
                        import asyncio
                        loop = asyncio.get_event_loop()
                        return await loop.run_in_executor(None, agent.invoke, agent_state)
                    
                    result = await asyncio.wait_for(run_agent(), timeout=20.0)
                    
                    elapsed = time.time() - start_time
                    print(f"[WS] ✅ Agent 완료 ({elapsed:.1f}초)")
                    
                    response = result.get("generation", "답변을 생성할 수 없습니다.")

                    if response == "NOT_RECIPE_RELATED":
                        print(f"[WS] 요리 무관 대화 감지")
                        
                        chat_sessions[session_id]["messages"].append({
                            "role": "assistant",
                            "content": "죄송합니다. 저는 요리 레시피만 도와드릴 수 있어요! 🍳\n일반적인 질문은 다른 AI 챗봇을 이용해주세요."
                        })
                        
                        await websocket.send_json({
                            "type": "not_recipe_related",
                            "content": "죄송합니다. 저는 요리 레시피만 도와드릴 수 있어요! 🍳\n일반적인 질문은 다른 AI 챗봇을 이용해주세요."
                        })
                        continue
                    
                    chat_sessions[session_id]["messages"].append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    await websocket.send_json({
                        "type": "agent_message",
                        "content": response
                    })
                
                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    print(f"[WS] ⏱️ Agent 타임아웃 ({elapsed:.1f}초)")
                    
                    await websocket.send_json({
                        "type": "agent_message",
                        "content": f"죄송합니다. 응답 시간이 너무 오래 걸렸어요 ({int(elapsed)}초). 다시 시도해주세요."
                    })
                
                except Exception as e:
                    elapsed = time.time() - start_time
                    print(f"[WS] ⚠️ Agent 실행 에러 ({elapsed:.1f}초): {e}")
                    import traceback
                    traceback.print_exc()
                    
                    await websocket.send_json({
                        "type": "error",
                        "message": f"오류가 발생했습니다 ({int(elapsed)}초). 다시 시도해주세요."
                    })
                
                finally:
                    notifier_task.cancel()
                    try:
                        await notifier_task
                    except asyncio.CancelledError:
                        pass
    
    except WebSocketDisconnect:
        print(f"[WS] Disconnected: {session_id}")
    except Exception as e:
        print(f"[WS] 에러: {e}")
        import traceback
        traceback.print_exc()
    finally:
        manager.disconnect(session_id)
        print(f"[WS] Closed: {session_id}")

@router.get("/session/{session_id}")
async def get_chat_session(session_id: str):
    """채팅 세션 정보 조회"""
    print(f"[Chat API] 세션 조회: {session_id}")
    
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    session = chat_sessions[session_id]
    
    return {
        "session_id": session_id,
        "messages": session.get("messages", []),
        "user_constraints": session.get("user_constraints", {})
    }