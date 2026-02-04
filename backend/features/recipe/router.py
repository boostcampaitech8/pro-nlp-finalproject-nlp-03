# # backend/features/recipe/router.py
# """
# Recipe REST API 라우터
# """
# import json
# import asyncio
# from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks

# from core.dependencies import get_rag_system
# from core.exceptions import RAGNotAvailableError
# from features.recipe.service import RecipeService
# from features.recipe.schemas import RecipeGenerateRequest
# from models.mysql_db import (
#     save_my_recipe, get_my_recipes, get_my_recipe, delete_my_recipe, update_my_recipe,
#     get_member_personalization, get_member_by_id,
#     create_generate, get_generate, get_session_generates
# )

# router = APIRouter()


# def get_user_profile_from_db(member_id: int) -> dict:
#     """MySQL에서 사용자 프로필 조회"""
#     if member_id == 0:
#         return {"name": "게스트", "allergies": [], "dislikes": []}

#     member = get_member_by_id(member_id)
#     psnl = get_member_personalization(member_id)

#     return {
#         "name": member.get("nickname", "사용자") if member else "사용자",
#         "allergies": psnl.get("allergies", []) if psnl else [],
#         "dislikes": psnl.get("dislikes", []) if psnl else []
#     }


# @router.post("/generate")
# async def generate_recipe(
#     request: RecipeGenerateRequest,
#     background_tasks: BackgroundTasks,
#     rag_system = Depends(get_rag_system)
# ):
#     """레시피 생성 (대화 히스토리 반영) - generate 테이블에 저장"""
#     print("\n" + "="*60)
#     print("[Recipe API] 레시피 생성 요청")
#     print("="*60)

#     if not rag_system:
#         raise RAGNotAvailableError()

#     # member_id 추출 (숫자면 사용, 아니면 0)
#     member_id = 0
#     if request.member_info:
#         mid = request.member_info.get('member_id')
#         if mid and str(mid).isdigit():
#             member_id = int(mid)

#     # MySQL에서 사용자 프로필 조회
#     user_profile = get_user_profile_from_db(member_id)
#     print(f"[Recipe API] 사용자 프로필: {user_profile}")

#     service = RecipeService(rag_system, None, user_profile)

#     try:
#         recipe_data = await service.generate_recipe(
#             chat_history=request.chat_history,
#             member_info=request.member_info
#         )

#         generate_id = None
#         # 백그라운드로 generate 테이블에 저장
#         def save_to_generate():
#             nonlocal generate_id
#             try:
#                 # session_id가 없으면 None으로 저장 (직접 호출 시)
#                 session_id = request.member_info.get('session_id') if request.member_info else None
#                 if session_id and str(session_id).isdigit():
#                     session_id = int(session_id)
#                 else:
#                     session_id = None

#                 result = create_generate(
#                     session_id=session_id,
#                     member_id=member_id,
#                     recipe_name=recipe_data.get('title', '추천 레시피'),
#                     ingredients=recipe_data.get('ingredients', []),
#                     steps=recipe_data.get('steps', []),
#                     gen_type="FIRST"
#                 )
#                 generate_id = result.get('generate_id')
#                 print(f"[Recipe API] generate 테이블 저장 완료: ID={generate_id}")
#             except Exception as e:
#                 print(f"[Recipe API] generate 저장 실패: {e}")

#         background_tasks.add_task(save_to_generate)

#         # 즉시 응답 (generate_id는 백그라운드 저장 후 결정됨)
#         return {
#             "recipe": recipe_data,
#             "member_id": member_id,
#             "title": recipe_data.get('title', '추천 레시피'),
#             "constraints": request.member_info or {}
#         }

#     except Exception as e:
#         print(f"[Recipe API] 에러 발생: {e}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/generate-from-chat")
# async def generate_recipe_from_chat(
#     session_id: str,
#     background_tasks: BackgroundTasks,
#     rag_system = Depends(get_rag_system)
# ):
#     """채팅 세션에서 레시피 생성 → generate 테이블에 저장"""
#     print("\n" + "="*60)
#     print("[Recipe API] 채팅 세션에서 레시피 생성")
#     print("="*60)

#     from features.chat.router import chat_sessions

#     if session_id not in chat_sessions:
#         raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

#     if not rag_system:
#         raise RAGNotAvailableError()

#     session = chat_sessions[session_id]
#     messages = session.get("messages", [])
#     user_constraints = session.get("user_constraints", {})
#     db_session_id = session.get("db_session_id")  # MySQL session.session_id

#     # member_id 추출 (숫자면 사용, 아니면 0)
#     member_id = session.get("member_id", 0)
#     if not member_id and user_constraints:
#         mid = user_constraints.get('member_id')
#         if mid and str(mid).isdigit():
#             member_id = int(mid)

#     # 세션에 저장된 user_profile 또는 MySQL에서 조회
#     user_profile = session.get("user_profile") or get_user_profile_from_db(member_id)

#     if not messages:
#         raise HTTPException(status_code=400, detail="대화 내용이 없습니다")

#     print(f"[Recipe API] 세션 메시지 수: {len(messages)}")
#     print(f"[Recipe API] 사용자 프로필: {user_profile}")
#     print(f"[Recipe API] DB session_id: {db_session_id}")

#     service = RecipeService(rag_system, None, user_profile)

#     try:
#         # 레시피 생성 (RAG + LLM + MongoDB 이미지)
#         recipe_json = await service.generate_recipe(
#             chat_history=messages,
#             member_info=user_constraints
#         )

#         print(f"[Recipe API] 레시피 생성 완료: {recipe_json.get('title')}")
#         print(f"[Recipe API] 이미지: {recipe_json.get('image', 'None')[:60]}...")

#         generate_id = None
#         # generate 테이블에 저장 (동기로 저장하여 generate_id 반환)
#         if member_id > 0:
#             try:
#                 # 해당 세션의 이전 생성 개수 확인
#                 existing = get_session_generates(db_session_id) if db_session_id else []
#                 gen_order = len(existing) + 1
#                 gen_type = "FIRST" if gen_order == 1 else "RETRY"

#                 result = create_generate(
#                     session_id=db_session_id,
#                     member_id=member_id,
#                     recipe_name=recipe_json.get('title', '추천 레시피'),
#                     ingredients=recipe_json.get('ingredients', []),
#                     steps=recipe_json.get('steps', []),
#                     gen_type=gen_type,
#                     gen_order=gen_order
#                 )
#                 generate_id = result.get('generate_id')
#                 print(f"[Recipe API] generate 테이블 저장 완료: ID={generate_id}, order={gen_order}")
#             except Exception as e:
#                 print(f"[Recipe API] generate 저장 실패: {e}")

#         # 응답에 generate_id 포함 (마이레시피 저장 시 사용)
#         return {
#             "recipe": recipe_json,
#             "member_id": member_id,
#             "title": recipe_json.get("title"),
#             "constraints": user_constraints,
#             "session_id": session_id,
#             "db_session_id": db_session_id,
#             "generate_id": generate_id
#         }

#     except Exception as e:
#         print(f"[Recipe API] 레시피 생성 실패: {e}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/list")
# async def list_recipes(
#     member_id: int = Query(default=0),
#     limit: int = Query(default=50),
# ):
#     """저장된 레시피 목록 조회"""
#     try:
#         rows = get_my_recipes(member_id, limit)
#         recipes = []
#         for row in rows:
#             recipes.append({
#                 "id": row.get("my_recipe_id"),
#                 "title": row.get("recipe_name"),
#                 "created_at": row.get("created_at"),
#                 "image": row.get("image_url", ""),
#                 "rating": row.get("rating") or 0,
#                 "ingredients": row.get("ingredients", []),
#                 "steps": row.get("steps", []),
#             })
#         return {"recipes": recipes}
#     except Exception as e:
#         print(f"[Recipe API] 목록 조회 실패: {e}")
#         return {"recipes": []}


# @router.get("/{recipe_id}")
# async def get_recipe_detail(
#     recipe_id: int,
# ):
#     """레시피 상세 조회"""
#     try:
#         row = get_my_recipe(recipe_id)
#         if not row:
#             raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다")

#         return {
#             "id": row.get("my_recipe_id"),
#             "member_id": row.get("member_id"),
#             "title": row.get("recipe_name"),
#             "recipe": {
#                 "title": row.get("recipe_name"),
#                 "ingredients": row.get("ingredients", []),
#                 "steps": row.get("steps", []),
#                 "image": row.get("image_url", ""),
#             },
#             "rating": row.get("rating") or 0,
#             "created_at": row.get("created_at"),
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"[Recipe API] 상세 조회 실패: {e}")
#         raise HTTPException(status_code=503, detail="DB 조회 실패")

# @router.post("/save-my-recipe")
# async def save_recipe_to_mypage(
#     request: dict,
# ):
#     """요리 완료 후 마이레시피에 저장 (generate_id, session_id 연결)"""
#     try:
#         # member_id 추출 (숫자면 사용, 아니면 0)
#         member_id = 0
#         mid = request.get("member_id")
#         if mid and str(mid).isdigit():
#             member_id = int(mid)

#         # generate_id, session_id 추출
#         generate_id = request.get("generate_id")
#         if generate_id and str(generate_id).isdigit():
#             generate_id = int(generate_id)
#         else:
#             generate_id = None

#         session_id = request.get("session_id") or request.get("db_session_id")
#         if session_id and str(session_id).isdigit():
#             session_id = int(session_id)
#         else:
#             session_id = None

#         recipe = request.get("recipe", {})
#         result = save_my_recipe(
#             member_id=member_id,
#             recipe_name=recipe.get("title", "마이레시피"),
#             ingredients=recipe.get("ingredients", []),
#             steps=recipe.get("steps", []),
#             rating=request.get("rating"),
#             image_url=recipe.get("image", ""),
#             session_id=session_id,
#             generate_id=generate_id
#         )

#         print(f"[Recipe API] 마이레시피 저장: ID={result.get('my_recipe_id')}, generate_id={generate_id}, session_id={session_id}")

#         return {
#             "success": True,
#             "recipe_id": result.get("my_recipe_id"),
#             "message": "마이레시피에 저장되었습니다"
#         }
#     except Exception as e:
#         print(f"[Recipe API] 마이레시피 저장 실패: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/{recipe_id}")
# async def delete_recipe(recipe_id: int):
#     """마이레시피 삭제"""
#     try:
#         existing = get_my_recipe(recipe_id)
#         if not existing:
#             raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다")

#         delete_my_recipe(recipe_id)
#         return {"success": True, "message": "레시피가 삭제되었습니다"}
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"[Recipe API] 마이레시피 삭제 실패: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.put("/{recipe_id}")
# async def update_recipe(recipe_id: int, request: dict):
#     """마이레시피 수정 (평점, 제목 등)"""
#     try:
#         existing = get_my_recipe(recipe_id)
#         if not existing:
#             raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다")

#         result = update_my_recipe(
#             my_recipe_id=recipe_id,
#             recipe_name=request.get("title"),
#             rating=request.get("rating"),
#             image_url=request.get("image")
#         )

#         return {
#             "success": True,
#             "recipe": {
#                 "id": result.get("my_recipe_id"),
#                 "title": result.get("recipe_name"),
#                 "rating": result.get("rating"),
#                 "image": result.get("image_url")
#             }
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"[Recipe API] 마이레시피 수정 실패: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# backend/features/recipe/router.py
"""
Recipe REST API 라우터
"""
import json
import time
import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks

from core.dependencies import get_rag_system, get_recipe_db, get_user_profile
from core.exceptions import RAGNotAvailableError, DatabaseNotAvailableError
from features.recipe.service import RecipeService
from features.recipe.schemas import RecipeGenerateRequest

logger = logging.getLogger(__name__)

router = APIRouter()


def _log_timing_summary(steps: list, total_ms: float):
    logger.info("┌─────────────────────────────────────────┐")
    logger.info("│      generate-from-chat Timing          │")
    logger.info("├─────────────────────────────────────────┤")
    max_ms = max((ms for _, ms in steps), default=1)
    for label, ms in steps:
        bar_len = int(ms / max_ms * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        pct = (ms / total_ms * 100) if total_ms > 0 else 0
        sec = ms / 1000
        logger.info(f"│  {label:<18} {bar} {sec:>5.1f}초 ({pct:>4.1f}%) │")
    logger.info("├─────────────────────────────────────────┤")
    total_sec = total_ms / 1000
    logger.info(f"│  {'TOTAL':<18} {'':20} {total_sec:>5.1f}초        │")
    logger.info("└─────────────────────────────────────────┘")


@router.post("/generate")
async def generate_recipe(
    request: RecipeGenerateRequest,
    background_tasks: BackgroundTasks,
    rag_system = Depends(get_rag_system),
    recipe_db = Depends(get_recipe_db),
    user_profile = Depends(get_user_profile)
):
    """레시피 생성 (대화 히스토리 반영)"""
    logger.info("[Recipe API] 레시피 생성 요청")

    if not rag_system:
        raise RAGNotAvailableError()
    if not recipe_db:
        raise DatabaseNotAvailableError()

    service = RecipeService(rag_system, recipe_db, user_profile)

    try:
        recipe_data = await service.generate_recipe(
            chat_history=request.chat_history,
            member_info=request.member_info
        )

        user_id = request.member_info.get('names', ['사용자'])[0] if request.member_info else '사용자'

        def save_to_db():
            try:
                recipe_id = recipe_db.save_recipe(user_id=user_id, recipe=recipe_data, constraints=request.member_info or {})
                logger.info(f"[Recipe API] 백그라운드 저장 완료: ID={recipe_id}")
            except Exception as e:
                logger.error(f"[Recipe API] 백그라운드 저장 실패: {e}")

        background_tasks.add_task(save_to_db)

        return {
            "recipe": recipe_data,
            "user_id": user_id,
            "title": recipe_data.get('title', '추천 레시피'),
            "constraints": request.member_info or {}
        }
    except Exception as e:
        logger.error(f"[Recipe API] 에러: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-from-chat")
async def generate_recipe_from_chat(
    session_id: str,
    background_tasks: BackgroundTasks,
    rag_system = Depends(get_rag_system),
    recipe_db = Depends(get_recipe_db),
    user_profile = Depends(get_user_profile)
):
    """채팅 세션에서 레시피 생성 — Agent 캐시 재사용"""
    t_total = time.time()
    steps = []

    logger.info("\n" + "="*60)
    logger.info("[Recipe API] 채팅 세션에서 레시피 생성")
    logger.info("="*60)

    from features.chat.router import chat_sessions

    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    if not rag_system:
        raise RAGNotAvailableError()
    if not recipe_db:
        raise DatabaseNotAvailableError()

    # ── 세션 파싱 ──
    t0 = time.time()
    session = chat_sessions[session_id]
    messages            = session.get("messages", [])
    user_constraints    = session.get("user_constraints", {})
    cached_documents    = session.get("last_documents", [])
    last_agent_response = session.get("last_agent_response", "")   # ← Agent 최종 답변
    steps.append(("세션 파싱", (time.time() - t0) * 1000))

    if not messages:
        raise HTTPException(status_code=400, detail="대화 내용이 없습니다")

    logger.info(f"[Recipe API] 캐시 문서 수: {len(cached_documents)}")
    logger.info(f"[Recipe API] Agent 답변 캐시: {'있음' if last_agent_response else '없음'}")

    service = RecipeService(rag_system, recipe_db, user_profile)

    try:
        t0 = time.time()
        if cached_documents:
            logger.info("[Recipe API] 캐시 경로 (검색 스킵)")
            recipe_json = await service.generate_recipe_from_cached_docs(
                chat_history=messages,
                member_info=user_constraints,
                cached_documents=cached_documents,
                last_agent_response=last_agent_response   # ← 전달
            )
        else:
            logger.info("[Recipe API] 캐시 없음 → 전체 검색 폴백")
            recipe_json = await service.generate_recipe(
                chat_history=messages,
                member_info=user_constraints
            )
        steps.append(("Service 전체", (time.time() - t0) * 1000))

        # service 내부 단계별 타이밍 삽입
        if hasattr(service, '_last_timings') and service._last_timings:
            internal = service._last_timings
            steps = steps[:-1] + internal + [steps[-1]]

        logger.info(f"[Recipe API] 레시피 생성 완료: {recipe_json.get('title')}")

        user_id = user_constraints.get('names', ['사용자'])[0] if user_constraints else '사용자'

        def save_to_db():
            try:
                recipe_id = recipe_db.save_recipe(user_id=user_id, recipe=recipe_json, constraints=user_constraints)
                logger.info(f"[Recipe API] 백그라운드 저장 완료: ID={recipe_id}")
            except Exception as e:
                logger.error(f"[Recipe API] 백그라운드 저장 실패: {e}")

        background_tasks.add_task(save_to_db)

        # ── 타이밍 출력 ──
        total_ms = (time.time() - t_total) * 1000
        _log_timing_summary(steps, total_ms)
        total_sec = total_ms / 1000
        logger.info(f"[Recipe API] ✅ 레시피 결과까지 총 {total_sec:.1f}초")

        return {
            "recipe": recipe_json,
            "user_id": user_id,
            "title": recipe_json.get("title"),
            "constraints": user_constraints,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"[Recipe API] 레시피 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_recipes(
    user_id: str = Query(default=None),
    limit: int = Query(default=50),
    recipe_db=Depends(get_recipe_db),
):
    if not recipe_db:
        return {"recipes": []}
    rows = recipe_db.get_recent(user_id, limit)
    recipes = []
    for row in rows:
        recipe_json = json.loads(row[3]) if len(row) > 3 and row[3] else {}
        recipes.append({
            "id": row[0],
            "title": row[1],
            "created_at": row[2],
            "image": recipe_json.get('image', ''),
        })
    return {"recipes": recipes}


@router.get("/{recipe_id}")
async def get_recipe(
    recipe_id: int,
    recipe_db=Depends(get_recipe_db),
):
    if not recipe_db:
        raise HTTPException(status_code=503, detail="DB 사용 불가")
    row = recipe_db.get_recipe_by_id(recipe_id)
    if not row:
        raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다")
    recipe_json = json.loads(row[3]) if row[3] else {}
    return {
        "id": row[0],
        "user_id": row[1],
        "title": row[2],
        "recipe": recipe_json,
        "constraints": json.loads(row[4]) if row[4] else {},
        "created_at": row[5],
    }
