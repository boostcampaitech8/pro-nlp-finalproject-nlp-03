# core/websocket.py
"""
WebSocket 연결 관리
"""
from typing import Dict
from fastapi import WebSocket


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """연결 수락"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"[WS] Connected: {session_id}")
    
    def disconnect(self, session_id: str):
        """연결 해제"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"[WS] Disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """메시지 전송"""
        websocket = self.active_connections.get(session_id)
        if websocket:
            await websocket.send_json(message)
    
    def is_connected(self, session_id: str) -> bool:
        """연결 여부 확인"""
        return session_id in self.active_connections


# 싱글톤 인스턴스
manager = ConnectionManager()