import os
import re
from datetime import datetime
from pymongo import MongoClient
from neo4j import GraphDatabase
from langchain_community.embeddings import ClovaXEmbeddings

MONGO_URI = "mongodb://root:RootPassword123@mongodb:27017/admin"
DB_NAME = "recipe_db"
RECIPE_COL = "recipes"

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

MODEL_NAME = "bge-m3"

CYPHER = """
MERGE (r:Recipe {recipe_id: $recipe_id})
SET r.title = $title,
    r.intro = $intro,
    r.cook_time = $cook_time,
    r.level = $level

MERGE (c:Chunk {chunk_id: $chunk_id})
SET c.text = $text,
    c.embedding = $embedding

MERGE (r)-[:HAS_CHUNK]->(c)
"""

mongo = MongoClient(MONGO_URI)
collection = mongo[DB_NAME][RECIPE_COL]

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

embeddings = ClovaXEmbeddings(model=MODEL_NAME)


def normalize_ingredient(name: str) -> str:
    # 숫자/단위 제거 (간단 버전)
    return re.sub(r"[0-9]+.*", "", name).strip()


def make_text(recipe):
    title = recipe.get("title", "")
    intro = recipe.get("intro", "")

    # ingredients는 dict 리스트
    ingredient_names = [ing["name"] for ing in recipe.get("ingredients", [])]

    ingredient_text = ", ".join(ingredient_names)

    steps = recipe.get("steps", [])
    step_text = " ".join(steps)

    return f"""
제목: {title}
소개: {intro}
재료: {ingredient_text}
조리과정: {step_text}
"""


def run_batch():
    docs = collection.find({"neo4j_embed": {"$ne": True}}).limit(50)

    count = 0

    with driver.session() as session:
        for doc in docs:
            recipe_id = str(doc.get("recipe_id") or doc["_id"])

            text = make_text(doc)
            vector = embeddings.embed_query(text)

            chunk_id = f"{recipe_id}_main"

            # Recipe + Chunk 저장
            session.run(
                CYPHER,
                recipe_id=recipe_id,
                title=doc.get("title", ""),
                intro=doc.get("intro", ""),
                cook_time=doc.get("cook_time", ""),
                level=doc.get("level", ""),
                chunk_id=chunk_id,
                text=text,
                embedding=vector,
            )

            # Ingredient 연결
            for ing in doc.get("ingredients", []):
                raw_name = ing["name"]
                clean_name = normalize_ingredient(raw_name)

                session.run(
                    """
                    MERGE (i:Ingredient {name: $name})
                    WITH i
                    MATCH (r:Recipe {recipe_id: $recipe_id})
                    MERGE (r)-[:CONTAINS]->(i)
                """,
                    name=clean_name,
                    recipe_id=recipe_id,
                )

            # Mongo에 표시
            collection.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "neo4j_embed": True,
                        "neo4j_embed_at": datetime.utcnow(),
                        "neo4j_embedding_model": MODEL_NAME,
                    }
                },
            )

            count += 1

    print(f"Processed {count} recipes")
