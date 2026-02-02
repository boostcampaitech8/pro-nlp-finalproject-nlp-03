# backend/features/recipe/router.py
"""
Recipe REST API 라우터
"""
import json
from fastapi import APIRouter, Depends, HTTPException, Query

from core.dependencies import get_rag_system, get_recipe_db, get_user_profile
from core.exceptions import RAGNotAvailableError, DatabaseNotAvailableError
from features.recipe.service import RecipeService
from features.recipe.schemas import RecipeGenerateRequest

router = APIRouter()


# backend/features/recipe/router.py
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
        
        # 요리와 관련 없는 질문인 경우 (에러 응답)
        if recipe_data.get('error') == 'NOT_RECIPE_RELATED':
            return {
                "error": "NOT_RECIPE_RELATED",
                "message": recipe_data.get('message')
            }
        
        # 정상 레시피 응답
        response = {
            "recipe": recipe_data, 
            "user_id": request.member_info.get('names', ['사용자'])[0] if request.member_info else '사용자',
            "title": recipe_data.get('title', '추천 레시피'),
            "constraints": request.member_info or {}
        }
        
        print(f"[Recipe API] 응답 데이터:")
        print(f"  - 레시피명: {response['title']}")
        print(f"  - 인원수: {recipe_data.get('servings', 'N/A')}")
        print(f"  - 이미지: {recipe_data.get('image_url', 'None')}")
        print(f"  - 조리시간: {recipe_data.get('cook_time', 'None')}")
        print(f"  - 난이도: {recipe_data.get('level', 'None')}")
        
        return response
    
    except Exception as e:
        print(f"[Recipe API] 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def save_recipe(
    recipe_data: dict,
    recipe_db=Depends(get_recipe_db),
):
    """
    레시피 저장 API (백그라운드 저장용)
    프론트엔드에서 백그라운드로 호출
    """
    print("\n" + "="*60)
    print("[Recipe API] 레시피 저장 요청")
    print("="*60)
    
    if not recipe_db:
        raise DatabaseNotAvailableError()
    
    try:
        user_id = recipe_data.get('user_id', '사용자')
        recipe = recipe_data.get('recipe', {})
        constraints = recipe_data.get('constraints', {})
        
        recipe_id = recipe_db.save_recipe(
            user_id=user_id,
            recipe=recipe,
            constraints=constraints
        )
        
        print(f"[Recipe API] 저장 완료: ID={recipe_id}")
        
        return {
            "status": "success",
            "recipe_id": recipe_id,
            "message": "레시피가 저장되었습니다."
        }
    
    except Exception as e:
        print(f"[Recipe API] 저장 실패: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_recipes(
    user_id: str = Query(default=None),
    limit: int = Query(default=50),
    recipe_db=Depends(get_recipe_db),
):
    """저장된 레시피 목록 조회"""
    if not recipe_db:
        return {"recipes": []}

    rows = recipe_db.get_recent(user_id, limit)
    recipes = []
    for row in rows:
        # row 구조: (id, title, created_at, recipe_json, ...)
        recipe_json = json.loads(row[3]) if len(row) > 3 and row[3] else {}
        
        recipes.append({
            "id": row[0],
            "title": row[1],
            "created_at": row[2],
            "image_url": recipe_json.get('image_url', '/images/default-food.jpg'),
        })
    return {"recipes": recipes}


@router.get("/{recipe_id}")
async def get_recipe(
    recipe_id: int,
    recipe_db=Depends(get_recipe_db),
):
    """레시피 상세 조회"""
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