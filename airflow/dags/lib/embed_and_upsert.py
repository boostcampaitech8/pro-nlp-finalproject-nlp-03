import time
import logging
from collections import OrderedDict
from typing import Dict, List

from langchain_core.documents import Document
from langchain_community.vectorstores import Milvus

from lib.mongo_utils import mark_embedded

MILVUS_HOST = "milvus-standalone"
MILVUS_PORT = "19530"
COLLECTION_NAME = "recipe_docs"
MODEL_NAME = "bge-m3"

logger = logging.getLogger(__name__)


def group_by_recipe(documents: List[Document]) -> Dict[str, List[Document]]:
    """
    청크를 recipe_id 단위로 묶는다 (입력 순서 유지).
    recipe_id가 없는 문서는 완료 처리 기준이 없으므로 제외한다.
    """
    groups: Dict[str, List[Document]] = OrderedDict()
    for doc in documents:
        recipe_id = doc.metadata.get("recipe_id")
        if not recipe_id:
            logger.warning("recipe_id 없는 문서 제외: %s", doc.metadata.get("title"))
            continue
        groups.setdefault(recipe_id, []).append(doc)
    return groups


def delete_existing_vectors(vectorstore: Milvus, recipe_id: str) -> None:
    """
    재실행 시 중복 적재를 막기 위해 해당 레시피의 기존 벡터를 먼저 삭제한다.
    컬렉션이 아직 없으면(첫 적재) 삭제할 대상이 없다.
    """
    if vectorstore.col is None:
        return
    vectorstore.delete(expr=f'recipe_id == "{recipe_id}"')


def embedding_and_upsert(documents, embeddings, recipes_col, sleep_per_doc=1.0):
    """
    레시피 단위로 [기존 벡터 삭제 → 전체 청크 적재 → embedded 플래그 갱신]을 수행한다.

    - 모든 청크가 적재된 뒤에만 embedded=True로 표시하므로,
      중간에 실패한 레시피는 다음 실행에서 다시 처리된다.
    - 적재 전에 같은 recipe_id의 벡터를 지우므로 재실행해도 벡터가 중복되지 않는다.
    """
    vectorstore = Milvus(
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
        connection_args={
            "host": MILVUS_HOST,
            "port": MILVUS_PORT,
        },
        drop_old=False,
        auto_id=True,
    )

    succeeded, failed = 0, 0

    for recipe_id, chunks in group_by_recipe(documents).items():
        try:
            delete_existing_vectors(vectorstore, recipe_id)
            vectorstore.add_texts(
                texts=[doc.page_content for doc in chunks],
                metadatas=[doc.metadata for doc in chunks],
            )
            mark_embedded(recipes_col, recipe_id, MODEL_NAME)
            succeeded += 1
        except Exception:
            # 완료 표시를 하지 않았으므로 다음 실행에서 재처리된다.
            logger.exception("임베딩 적재 실패: recipe_id=%s", recipe_id)
            failed += 1

        # 임베딩 API 호출 속도 제한 (기존과 같은 청크당 간격 유지)
        time.sleep(sleep_per_doc * len(chunks))

    logger.info("임베딩 적재 완료: 성공 %d건, 실패 %d건", succeeded, failed)

    # 성공한 레시피는 반영해 두고, 실패가 있으면 태스크를 실패로 끝내
    # Airflow UI·알림에서 확인할 수 있게 한다.
    if failed:
        raise RuntimeError(f"임베딩 적재 실패 {failed}건 (성공 {succeeded}건)")

    return succeeded, failed
