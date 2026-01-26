# features/recipe/router.py
"""
Recipe REST API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from core.dependencies import get_rag_system, get_recipe_db, get_user_profile
from core.exceptions import RAGNotAvailableError, DatabaseNotAvailableError, RecipeNotFoundError
from features.recipe.service import RecipeService
from features.recipe.schemas import RecipeGenerateRequest, RecipeResponse, RecentRecipeResponse


router = APIRouter()


@router.post("/generate")
async def generate_recipe(
    request: RecipeGenerateRequest,
    rag_system = Depends(get_rag_system),
    recipe_db = Depends(get_recipe_db),
    user_profile = Depends(get_user_profile)
):
    """레시피 생성 (대화 히스토리 반영)"""
    print("\n" + "="*60)
    print("[Recipe API] 레시피 생성 요청")
    print("="*60)
    
    if not rag_system:
        raise RAGNotAvailableError()
    
    if not recipe_db:
        raise DatabaseNotAvailableError()
    
    service = RecipeService(rag_system, recipe_db, user_profile)
    
    try:
        # 대화 히스토리는 이미 Dict 형태
        recipe_data = await service.generate_recipe(
            recipe_title=request.recipe_title,
            chat_history=request.chat_history,  # ← Dict 그대로 전달
            member_info=request.member_info
        )
        
        # 응답 형식 맞추기
        return {
            "recipe": recipe_data,
            "user_id": request.member_info.get('names', ['사용자'])[0] if request.member_info else '사용자',
            "title": recipe_data.get('title', request.recipe_title),
            "constraints": request.member_info or {}
        }
    
    except Exception as e:
        print(f"[Recipe API] 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent", response_model=List[RecentRecipeResponse])
async def get_recent_recipes(
    limit: int = 5,
    recipe_db = Depends(get_recipe_db),
    user_profile = Depends(get_user_profile)
):
    """최근 레시피 조회"""
    if not recipe_db:
        raise DatabaseNotAvailableError()
    
    recent = recipe_db.get_recent(user_profile["name"], limit=limit)
    
    return [
        {
            "id": recipe_id,
            "title": title,
            "created_at": created_at
        }
        for recipe_id, title, created_at in recent
    ]


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: int,
    recipe_db = Depends(get_recipe_db)
):
    """레시피 상세 조회"""
    if not recipe_db:
        raise DatabaseNotAvailableError()
    
    row = recipe_db.get_recipe_by_id(recipe_id)
    
    if not row:
        raise RecipeNotFoundError(recipe_id)
    
    import json
    _, user_id, title, recipe_json_str, constraints_json_str, created_at = row
    
    return {
        "recipe_id": recipe_id,
        "user_id": user_id,
        "title": title,
        "recipe": json.loads(recipe_json_str),
        "constraints": json.loads(constraints_json_str),
        "created_at": created_at,
    }