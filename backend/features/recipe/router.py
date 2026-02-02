# backend/features/recipe/router.py
"""
Recipe REST API 라우터
"""
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks

from core.dependencies import get_rag_system, get_recipe_db, get_user_profile
from core.exceptions import RAGNotAvailableError, DatabaseNotAvailableError
from features.recipe.service import RecipeService
from features.recipe.schemas import RecipeGenerateRequest

router = APIRouter()


@router.post("/generate")
async def generate_recipe(
    request: RecipeGenerateRequest,
    background_tasks: BackgroundTasks,
    rag_system = Depends(get_rag_system),
    recipe_db = Depends(get_recipe_db),
    user_profile = Depends(get_user_profile)
):
    """레시피 생성 (대화 히스토리 반영) - 병렬 저장"""
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
        
        user_id = request.member_info.get('names', ['사용자'])[0] if request.member_info else '사용자'
        
        # 백그라운드로 DB 저장 (병렬 처리!)
        def save_to_db():
            try:
                recipe_id = recipe_db.save_recipe(
                    user_id=user_id,
                    recipe=recipe_data,
                    constraints=request.member_info or {}
                )
                print(f"[Recipe API] 백그라운드 저장 완료: ID={recipe_id}")
            except Exception as e:
                print(f"[Recipe API] 백그라운드 저장 실패: {e}")
        
        background_tasks.add_task(save_to_db)
        
        # 즉시 응답 (DB 저장 기다리지 않음!)
        return {
            "recipe": recipe_data,
            "user_id": user_id,
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
    recipe_db = Depends(get_recipe_db),
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
    
    if not recipe_db:
        raise DatabaseNotAvailableError()
    
    session = chat_sessions[session_id]
    messages = session.get("messages", [])
    user_constraints = session.get("user_constraints", {})
    
    if not messages:
        raise HTTPException(status_code=400, detail="대화 내용이 없습니다")
    
    print(f"[Recipe API] 세션 메시지 수: {len(messages)}")
    print(f"[Recipe API] 사용자 제약: {user_constraints.get('names', [])}")
    
    service = RecipeService(rag_system, recipe_db, user_profile)
    
    try:
        # 레시피 생성 (RAG + LLM + MongoDB 이미지)
        recipe_json = await service.generate_recipe(
            chat_history=messages,
            member_info=user_constraints
        )
        
        print(f"[Recipe API] 레시피 생성 완료: {recipe_json.get('title')}")
        print(f"[Recipe API] 이미지: {recipe_json.get('image', 'None')[:60]}...")
        
        user_id = user_constraints.get('names', ['사용자'])[0] if user_constraints else '사용자'
        
        # 백그라운드 저장
        def save_to_db():
            try:
                recipe_id = recipe_db.save_recipe(
                    user_id=user_id,
                    recipe=recipe_json,
                    constraints=user_constraints
                )
                print(f"[Recipe API] 백그라운드 저장 완료: ID={recipe_id}")
            except Exception as e:
                print(f"[Recipe API] 백그라운드 저장 실패: {e}")
        
        background_tasks.add_task(save_to_db)
        
        # 즉시 응답 (이미지 포함!)
        return {
            "recipe": recipe_json,
            "user_id": user_id,
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
        recipe_json = json.loads(row[3]) if len(row) > 3 and row[3] else {}
        
        recipes.append({
            "id": row[0],
            "title": row[1],
            "created_at": row[2],
            "image": recipe_json.get('image', ''),  # 이미지 URL 포함!
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
        "recipe": recipe_json,  # 이미지 URL 포함된 전체 레시피
        "constraints": json.loads(row[4]) if row[4] else {},
        "created_at": row[5],
    }