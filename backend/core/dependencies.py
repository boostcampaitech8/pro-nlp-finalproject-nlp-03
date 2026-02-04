# core/dependencies.py
"""
FastAPI 의존성 관리
"""
from functools import lru_cache
from typing import Optional, Dict, Any
import os

from services.rag import RecipeRAGLangChain
from app.config import settings
from models.database import RecipeDB


# 싱글톤 인스턴스
_rag_system: Optional[RecipeRAGLangChain] = None
_recipe_db: Optional[RecipeDB] = None


@lru_cache()
def get_rag_system() -> Optional[RecipeRAGLangChain]:
    """RAG 시스템 싱글톤"""
    global _rag_system

    if _rag_system is None:
        if not settings.CLOVASTUDIO_API_KEY:
            print("CLOVASTUDIO_API_KEY 환경변수가 설정되지 않았습니다.")
            return None

        try:
            _rag_system = RecipeRAGLangChain(
                milvus_host=settings.MILVUS_HOST,
                milvus_port=settings.MILVUS_PORT,
                collection_name=settings.COLLECTION_NAME,
                use_reranker=settings.USE_RERANKER,
                temperature=0.01,
                max_tokens=2000,
            )
        except Exception as e:
            print(f"RAG 초기화 실패: {e}")
            return None

    return _rag_system


@lru_cache()
def get_recipe_db() -> Optional[RecipeDB]:
    """레시피 SQLite DB 싱글톤"""
    global _recipe_db

    if _recipe_db is None:
        # DATABASE_URL 예: sqlite:///./recipes.db
        database_url = os.getenv("DATABASE_URL", "sqlite:///./recipes.db")
        if database_url.startswith("sqlite:///"):
            db_path = database_url.replace("sqlite:///", "")
        elif database_url.startswith("sqlite://"):
            db_path = database_url.replace("sqlite://", "")
        else:
            # 다른 형태면 그대로 경로로 취급
            db_path = database_url
        _recipe_db = RecipeDB(path=db_path)

    return _recipe_db


def get_user_profile() -> Dict[str, Any]:
    """사용자 프로필 의존성 (기본값 제공)"""
    return {}