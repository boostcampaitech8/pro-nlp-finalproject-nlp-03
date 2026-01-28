# backend/features/recipe/router.py
"""
Recipe REST API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import get_rag_system, get_recipe_db, get_user_profile
from core.exceptions import RAGNotAvailableError, DatabaseNotAvailableError
from features.recipe.service import RecipeService
from features.recipe.schemas import RecipeGenerateRequest

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
        recipe_data = await service.generate_recipe(
            chat_history=request.chat_history,
            member_info=request.member_info
        )
        
        return {
            "recipe": recipe_data,
            "user_id": request.member_info.get('names', ['사용자'])[0] if request.member_info else '사용자',
            "title": recipe_data.get('title', '추천 레시피'),
            "constraints": request.member_info or {}
        }
    
    except Exception as e:
        print(f"[Recipe API] 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))