# backend/features/recipe/router.py
"""
Recipe REST API 라우터
"""
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks

from core.dependencies import get_rag_system, get_user_profile
from core.exceptions import RAGNotAvailableError
from features.recipe.service import RecipeService
from features.recipe.schemas import RecipeGenerateRequest
from models.mysql_db import save_my_recipe, get_my_recipes, get_my_recipe

router = APIRouter()


@router.post("/generate")
async def generate_recipe(
    request: RecipeGenerateRequest,
    background_tasks: BackgroundTasks,
    rag_system = Depends(get_rag_system),
    user_profile = Depends(get_user_profile)
):
    """레시피 생성 (대화 히스토리 반영) - 병렬 저장"""
    print("\n" + "="*60)
    print("[Recipe API] 레시피 생성 요청")
    print("="*60)

    if not rag_system:
        raise RAGNotAvailableError()

    service = RecipeService(rag_system, None, user_profile)

    try:
        recipe_data = await service.generate_recipe(
            chat_history=request.chat_history,
            member_info=request.member_info
        )

        # member_id 추출 (숫자면 사용, 아니면 0)
        member_id = 0
        if request.member_info:
            mid = request.member_info.get('member_id')
            if mid and str(mid).isdigit():
                member_id = int(mid)

        # 백그라운드로 DB 저장 (병렬 처리!)
        def save_to_db():
            try:
                result = save_my_recipe(
                    member_id=member_id,
                    recipe_name=recipe_data.get('title', '추천 레시피'),
                    ingredients=recipe_data.get('ingredients', []),
                    steps=recipe_data.get('steps', []),
                    image_url=recipe_data.get('image', '')
                )
                print(f"[Recipe API] 백그라운드 저장 완료: ID={result.get('my_recipe_id')}")
            except Exception as e:
                print(f"[Recipe API] 백그라운드 저장 실패: {e}")

        background_tasks.add_task(save_to_db)

        # 즉시 응답 (DB 저장 기다리지 않음!)
        return {
            "recipe": recipe_data,
            "member_id": member_id,
            "title": recipe_data.get('title', '추천 레시피'),
            "constraints": request.member_info or {}
        }

    except Exception as e:
        print(f"[Recipe API] 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-from-chat")
async def generate_recipe_from_chat(
    session_id: str,
    background_tasks: BackgroundTasks,
    rag_system = Depends(get_rag_system),
    user_profile = Depends(get_user_profile)
):
    """채팅 세션에서 제대로 된 레시피 생성 (RecipeService 사용)"""
    print("\n" + "="*60)
    print("[Recipe API] 채팅 세션에서 레시피 생성")
    print("="*60)

    from features.chat.router import chat_sessions

    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    if not rag_system:
        raise RAGNotAvailableError()

    session = chat_sessions[session_id]
    messages = session.get("messages", [])
    user_constraints = session.get("user_constraints", {})

    if not messages:
        raise HTTPException(status_code=400, detail="대화 내용이 없습니다")

    print(f"[Recipe API] 세션 메시지 수: {len(messages)}")
    print(f"[Recipe API] 사용자 제약: {user_constraints.get('names', [])}")

    service = RecipeService(rag_system, None, user_profile)

    try:
        # 레시피 생성 (RAG + LLM + MongoDB 이미지)
        recipe_json = await service.generate_recipe(
            chat_history=messages,
            member_info=user_constraints
        )

        print(f"[Recipe API] 레시피 생성 완료: {recipe_json.get('title')}")
        print(f"[Recipe API] 이미지: {recipe_json.get('image', 'None')[:60]}...")

        # member_id 추출 (숫자면 사용, 아니면 0)
        member_id = 0
        if user_constraints:
            mid = user_constraints.get('member_id')
            if mid and str(mid).isdigit():
                member_id = int(mid)

        # 백그라운드 저장
        def save_to_db():
            try:
                result = save_my_recipe(
                    member_id=member_id,
                    recipe_name=recipe_json.get('title', '추천 레시피'),
                    ingredients=recipe_json.get('ingredients', []),
                    steps=recipe_json.get('steps', []),
                    image_url=recipe_json.get('image', '')
                )
                print(f"[Recipe API] 백그라운드 저장 완료: ID={result.get('my_recipe_id')}")
            except Exception as e:
                print(f"[Recipe API] 백그라운드 저장 실패: {e}")

        background_tasks.add_task(save_to_db)

        # 즉시 응답 (이미지 포함!)
        return {
            "recipe": recipe_json,
            "member_id": member_id,
            "title": recipe_json.get("title"),
            "constraints": user_constraints,
            "session_id": session_id
        }

    except Exception as e:
        print(f"[Recipe API] 레시피 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_recipes(
    member_id: int = Query(default=0),
    limit: int = Query(default=50),
):
    """저장된 레시피 목록 조회"""
    try:
        rows = get_my_recipes(member_id, limit)
        recipes = []
        for row in rows:
            recipes.append({
                "id": row.get("my_recipe_id"),
                "title": row.get("recipe_name"),
                "created_at": row.get("created_at"),
                "image": row.get("image_url", ""),
                "rating": row.get("rating") or 0,
                "ingredients": row.get("ingredients", []),
                "steps": row.get("steps", []),
            })
        return {"recipes": recipes}
    except Exception as e:
        print(f"[Recipe API] 목록 조회 실패: {e}")
        return {"recipes": []}


@router.get("/{recipe_id}")
async def get_recipe_detail(
    recipe_id: int,
):
    """레시피 상세 조회"""
    try:
        row = get_my_recipe(recipe_id)
        if not row:
            raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다")

        return {
            "id": row.get("my_recipe_id"),
            "member_id": row.get("member_id"),
            "title": row.get("recipe_name"),
            "recipe": {
                "title": row.get("recipe_name"),
                "ingredients": row.get("ingredients", []),
                "steps": row.get("steps", []),
                "image": row.get("image_url", ""),
            },
            "rating": row.get("rating") or 0,
            "created_at": row.get("created_at"),
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Recipe API] 상세 조회 실패: {e}")
        raise HTTPException(status_code=503, detail="DB 조회 실패")

@router.post("/save-my-recipe")
async def save_recipe_to_mypage(
    request: dict,
):
    """요리 완료 후 마이레시피에 저장"""
    try:
        # member_id 추출 (숫자면 사용, 아니면 0)
        member_id = 0
        mid = request.get("member_id")
        if mid and str(mid).isdigit():
            member_id = int(mid)

        recipe = request.get("recipe", {})
        result = save_my_recipe(
            member_id=member_id,
            recipe_name=recipe.get("title", "마이레시피"),
            ingredients=recipe.get("ingredients", []),
            steps=recipe.get("steps", []),
            rating=request.get("rating", 0),
            image_url=recipe.get("image", "")
        )

        return {
            "success": True,
            "recipe_id": result.get("my_recipe_id"),
            "message": "마이레시피에 저장되었습니다"
        }
    except Exception as e:
        print(f"[Recipe API] 마이레시피 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))