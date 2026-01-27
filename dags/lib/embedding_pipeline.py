from lib.embed_and_upsert import embedding_and_upsert
from lib.chunking import chunk_documents
from lib.mongo_utils import get_mongo_collections, get_unembedded_recipes
from lib.recipe_to_doc import recipe_to_document


def run_embedding_pipeline():
    recipes = get_mongo_collections()

    raw_recipes = list(get_unembedded_recipes(recipes, limit=50))

    docs = [recipe_to_document(r) for r in raw_recipes]
    docs = chunk_documents(docs)

    embedding_and_upsert(docs, recipes)
