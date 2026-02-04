import os
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime
from features.ranking.schemas import RecipeDetail, RecipePreview, RankingResponse

router = APIRouter()

# MongoDB 연결
MONGODB_URL = os.getenv(
    "MONGODB_URL", "mongodb://root:RootPassword123@136.113.251.237:27017"
)
DATABASE_NAME = os.getenv("DATABASE_NAME", "recipe_db")

client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

RANKING_CACHE = {
    "today": None,
    "updated_at": None,
}


async def load_today_ranking_cache():
    """오늘 랭킹을 미리 메모리에 로드 (순서 보존 버전)"""

    today_kst = datetime.now().strftime("%Y-%m-%d")

    # 1️⃣ 오늘 랭킹 ID 조회
    ranking_data = await db.ranking_id.find_one(
        {
            "date_kst": today_kst,
            "source": "10000recipes",
        },
        sort=[("created_at_kst", -1)],
    )

    if not ranking_data:
        print("❌ 랭킹 데이터 없음")
        return

    recipe_ids = ranking_data.get("recipe_ids", [])

    if not recipe_ids:
        print("❌ recipe_ids 비어있음")
        return

    # 2️⃣ Mongo에서 한 번에 조회 (순서 없음)
    recipes_raw = await db.recipes.find({"recipe_id": {"$in": recipe_ids}}).to_list(
        length=200
    )

    if not recipes_raw:
        print("❌ recipes 컬렉션 조회 실패")
        return

    # 3️⃣ recipe_id → document 매핑
    recipe_map = {r["recipe_id"]: r for r in recipes_raw if "recipe_id" in r}

    # 4️⃣ ranking 순서대로 재정렬 (🔥 핵심)
    recipes_sorted = [recipe_map[rid] for rid in recipe_ids if rid in recipe_map]

    # 5️⃣ Preview 변환
    previews = [
        RecipePreview(
            recipe_id=r["recipe_id"],
            title=r.get("title", ""),
            author=r.get("author", ""),
            image=r.get("image", ""),
        )
        for r in recipes_sorted
    ]

    # 6️⃣ 캐시 저장
    RANKING_CACHE["today"] = {
        "date_kst": today_kst,
        "recipes": previews,
        "total_count": len(previews),
    }

    RANKING_CACHE["updated_at"] = datetime.now()

    print(f"✅ 랭킹 캐시 완료 " f"({len(previews)}개, {RANKING_CACHE['updated_at']})")


# 오늘의 랭킹
@router.get("/today", response_model=RankingResponse)
async def get_today_ranking(limit: int = Query(100, ge=1, le=100)):

    # 캐시 있으면 바로 반환
    if RANKING_CACHE["today"]:
        data = RANKING_CACHE["today"]

        return RankingResponse(
            date_kst=data["date_kst"],
            recipes=data["recipes"][:limit],
            total_count=data["total_count"],
        )

    # 없으면 로딩
    await load_today_ranking_cache()

    if not RANKING_CACHE["today"]:
        raise HTTPException(404, "No ranking data")

    data = RANKING_CACHE["today"]

    return RankingResponse(
        date_kst=data["date_kst"],
        recipes=data["recipes"][:limit],
        total_count=data["total_count"],
    )


@router.get("/{date_kst}", response_model=RankingResponse)
async def get_ranking_by_date(
    date_kst: str,
    limit: int = Query(100, ge=1, le=100),
):

    try:
        datetime.strptime(date_kst, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, "Invalid date format")

    ranking_data = await db.ranking_id.find_one(
        {
            "date_kst": date_kst,
            "source": "10000recipes",
        },
        sort=[("created_at_kst", -1)],
    )

    if not ranking_data:
        raise HTTPException(404, "No ranking data")

    recipe_ids = ranking_data.get("recipe_ids", [])

    recipes = await db.recipes.find({"recipe_id": {"$in": recipe_ids}}).to_list(
        length=200
    )

    previews = [
        RecipePreview(
            recipe_id=r["recipe_id"],
            title=r["title"],
            author=r.get("author", ""),
            image=r.get("image", ""),
        )
        for r in recipes
    ]

    return RankingResponse(
        date_kst=date_kst,
        recipes=previews[:limit],
        total_count=len(previews),
    )


@router.get("/search", response_model=List[RecipePreview])
async def search_recipes(
    keyword: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
):

    cursor = db.recipes.find(
        {
            "$or": [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"ingredients.name": {"$regex": keyword, "$options": "i"}},
            ]
        }
    ).limit(limit)

    recipes = []

    async for r in cursor:
        recipes.append(
            RecipePreview(
                recipe_id=r["recipe_id"],
                title=r["title"],
                author=r.get("author", ""),
                image=r.get("image", ""),
            )
        )

    return recipes


# ===============================
# 레시피 상세 (단건 조회)
# ===============================


@router.get("/recipes/{recipe_id}", response_model=RecipeDetail)
async def get_recipe_detail(recipe_id: str):

    recipe = await db.recipes.find_one({"recipe_id": recipe_id})

    if not recipe:
        raise HTTPException(404, "Recipe not found")

    return RecipeDetail(
        recipe_id=recipe["recipe_id"],
        title=recipe["title"],
        author=recipe.get("author", ""),
        image=recipe.get("image", ""),
        intro=recipe.get("intro", ""),
        portion=recipe.get("portion", ""),
        cook_time=recipe.get("cook_time", ""),
        level=recipe.get("level", ""),
        detail_url=recipe.get("detail_url", ""),
        ingredients=recipe.get("ingredients", []),
        steps=recipe.get("steps", []),
    )
