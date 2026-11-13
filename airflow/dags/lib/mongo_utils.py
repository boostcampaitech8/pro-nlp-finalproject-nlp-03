import os
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING

DB_NAME = "recipe_db"
RECIPE_COL = "recipes"


def get_mongo_uri() -> str:
    """
    MongoDB 접속 URI를 환경변수(MONGO_URI)에서 읽는다.
    DAG 파싱 시점이 아니라 태스크 실행 시점에 호출해, 값이 없으면 명확한 오류를 낸다.
    """
    uri = os.environ.get("MONGO_URI")
    if not uri:
        raise RuntimeError("환경변수 MONGO_URI가 설정되지 않았습니다. airflow/.env를 확인하세요.")
    return uri


# MongoDB
def get_mongo_collections():
    mongo = MongoClient(get_mongo_uri())
    db = mongo[DB_NAME]
    recipes = db[RECIPE_COL]

    recipes.create_index([("recipe_id", ASCENDING)], unique=True)

    return recipes


def get_unembedded_recipes(recipes, limit=150):
    """
    아직 임베딩 안 된 레시피 조회
    """
    return (
        recipes.find({"embedded": {"$ne": True}}).sort("registered_at", -1).limit(limit)
    )


def mark_embedded(recipes, recipe_id, model_name):
    """
    임베딩 완료 표시
    """
    return recipes.update_one(
        {"recipe_id": recipe_id},
        {
            "$set": {
                "embedded": True,
                "embedded_at": datetime.now(timezone.utc),
                "embedding_model": model_name,
            }
        },
    )
