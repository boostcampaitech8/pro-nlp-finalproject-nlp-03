"""
services/rag.py
CLOVA Studio Reranker API 사용 (API Key만 필요)
"""

import json
import os
import http.client
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

# LangChain CLOVA X
try:
    from langchain_naver import ChatClovaX, ClovaXEmbeddings
except ImportError:
    from langchain_community.chat_models import ChatClovaX
    from langchain_community.embeddings import ClovaXEmbeddings

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

# LangChain chains
try:
    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
except ImportError:
    from langchain_classic.chains import create_retrieval_chain
    from langchain_classic.chains.combine_documents import create_stuff_documents_chain

# Milvus
try:
    from langchain_milvus import Milvus
except ImportError:
    from langchain_community.vectorstores import Milvus

from pymilvus import connections, utility

import time

load_dotenv()


# ─────────────────────────────────────────────
# 타이밍 로그 헬퍼
# ─────────────────────────────────────────────
def _t():
    """현재 시간 반환 (time.time())"""
    return time.time()

def _log_step(label: str, start: float, end: float):
    """단계별 타이밍 로그 출력"""
    elapsed_ms = (end - start) * 1000
    elapsed_sec = elapsed_ms / 1000
    print(f"  ⏱️  [{label}] {elapsed_sec:.1f}초")


class ClovaStudioReranker:
    """CLOVA Studio Reranker API Wrapper"""
    
    def __init__(self, api_key: str, request_id: str = "recipe-rag-rerank"):
        self.host = 'clovastudio.stream.ntruss.com'
        self.api_key = f'Bearer {api_key}'
        self.request_id = request_id
        
    
    def rerank(self, query: str, documents: List[Dict[str, str]], max_tokens: int = 1024) -> Dict:
        """
        문서 재순위화
        
        Args:
            query: 검색 쿼리
            documents: [{"id": "doc1", "doc": "내용"}, ...] 형식의 문서 리스트
            max_tokens: 최대 토큰 수
        
        Returns:
            CLOVA Studio Reranker API 응답
        """
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': self.api_key,
            'X-NCP-CLOVASTUDIO-REQUEST-ID': self.request_id
        }
        
        request_data = {
            "documents": documents,
            "query": query,
            "maxTokens": max_tokens
        }
        
        try:
            conn = http.client.HTTPSConnection(self.host)
            conn.request('POST', '/v1/api-tools/reranker', json.dumps(request_data), headers)
            response = conn.getresponse()
            result = json.loads(response.read().decode(encoding='utf-8'))
            conn.close()
            
            if result.get('status', {}).get('code') == '20000':
                return result.get('result', {})
            else:
                print(f"[WARNING] Reranker API 오류: {result}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Reranker API 호출 실패: {e}")
            return None


class RecipeRAGLangChain:
    """
    LangChain + CLOVA X 기반 레시피 RAG 시스템
    - ClovaXEmbeddings (bge-m3) for vector search
    - ChatClovaX (HCX-DASH-001) for answer generation
    - CLOVA Studio Reranker API
    """

    def __init__(
        self,
        milvus_host: str,
        milvus_port: str,
        collection_name: str,
        use_reranker: bool = True,
        chat_model: str = "HCX-DASH-001",
        embedding_model: str = "bge-m3",
        temperature: float = 0,
        max_tokens: int = 2000,
    ):
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.milvus_uri = f"http://{milvus_host}:{milvus_port}"
        self.collection_name = collection_name
        self.use_reranker = use_reranker

        print("\n" + "="*60)
        print("Recipe RAG System (LangChain + CLOVA X)")
        print("="*60)

        # 1. CLOVA X Embeddings 초기화
        print(f"\n[1/5] CLOVA X Embeddings 초기화 중 (model: {embedding_model})")
        self.embeddings = ClovaXEmbeddings(model=embedding_model)
        print("[OK] Embeddings 초기화 완료")

        # 2. CLOVA X Chat 모델 초기화
        print(f"\n[2/5] CLOVA X Chat 모델 초기화 중 (model: {chat_model})")
        self.chat_model = ChatClovaX(
            model=chat_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        print("[OK] Chat 모델 초기화 완료")

        # 3. CLOVA Studio Reranker 초기화
        print("\n[3/5] CLOVA Studio Reranker 초기화 중")
        self.reranker = None
        if use_reranker:
            api_key = os.getenv("CLOVASTUDIO_RERANKER_API_KEY")
            request_id = os.getenv("CLOVASTUDIO_REQUEST_ID", "recipe-rag-rerank")
            
            if api_key:
                self.reranker = ClovaStudioReranker(
                    api_key=api_key,
                    request_id=request_id
                )
                print("[OK] CLOVA Studio Reranker 활성화")
            else:
                print("[WARNING] CLOVASTUDIO_RERANKER_API_KEY 없음. Reranker 비활성화.")
                self.use_reranker = False
        else:
            print("[OK] Reranker 비활성화")

        # 4. Milvus Vectorstore 연결
        print(f"\n[4/5] Milvus 연결 중 ({self.milvus_uri})")
        self.vectorstore = None
        self._connect_milvus()

        # 4. MongoDB 연결
        print("\n[5/5] MongoDB 연결 중")
        mongo_uri = os.getenv("MONGO_URI")
        self.mongo_client = MongoClient(mongo_uri)
        self.recipe_db = self.mongo_client["recipe_db"]
        self.recipes_collection = self.recipe_db["recipes"]
        print("[OK] MongoDB 연결 완료")
        
        print("\n" + "="*60)
        print("시스템 초기화 완료")
        print("="*60 + "\n")

    def _connect_milvus(self):
        """Milvus vectorstore 연결"""
        try:
            self.vectorstore = Milvus(
                embedding_function=self.embeddings,
                collection_name=self.collection_name,
                connection_args={"uri": self.milvus_uri},
                drop_old=False,
            )

            # Sanity check
            sanity_docs = self.vectorstore.similarity_search("조리법", k=1)
            if len(sanity_docs) > 0:
                print(f"[OK] Milvus 연결 성공 (Collection: {self.collection_name})")
                print(f"     Sanity check: {sanity_docs[0].metadata.get('title', 'N/A')[:50]}...")
            else:
                print(f"[WARNING] Milvus 연결됨, 하지만 문서가 없을 수 있습니다.")

        except Exception as e:
            print(f"[ERROR] Milvus 연결 실패: {e}")
            raise

    def _rerank_documents(
        self,
        query: str,
        documents: List[Document],
        top_n: int = 5
    ) -> List[tuple[Document, float]]:
        """CLOVA Studio Reranker를 사용한 문서 재순위화"""
        
        if not self.reranker or not documents:
            return [(doc, 1.0) for doc in documents[:top_n]]
        
        # CLOVA Studio Reranker 형식으로 변환
        rerank_docs = []
        for i, doc in enumerate(documents):
            rerank_docs.append({
                "id": f"doc{i}",
                "doc": doc.page_content[:2000]  # 토큰 제한
            })
        
        # Reranker API 호출
        result = self.reranker.rerank(query, rerank_docs, max_tokens=1024)
        
        if not result:
            # API 실패 시 원본 순서 유지
            print("[WARNING] Reranker 실패, 원본 순서 사용")
            return [(doc, 1.0) for doc in documents[:top_n]]
        
        # 결과 파싱
        reranked = []
        for item in result.get('topPassages', [])[:top_n]:
            doc_id = item.get('id', '')
            score = item.get('score', 0.0)
            
            # doc_id에서 인덱스 추출 (doc0 -> 0)
            try:
                idx = int(doc_id.replace('doc', ''))
                if 0 <= idx < len(documents):
                    reranked.append((documents[idx], score))
            except (ValueError, IndexError):
                continue
        
        # 결과가 없으면 원본 반환
        if not reranked:
            return [(doc, 1.0) for doc in documents[:top_n]]
        
        return reranked
    
    def _get_image_from_mongodb(self, recipe_id: str) -> str:
        """MongoDB에서 이미지 URL 가져오기"""
        try:
            recipe = self.recipes_collection.find_one(
                {"recipe_id": recipe_id},
                {"image": 1, "_id": 0}
            )
            
            if recipe and "image" in recipe:
                image_url = recipe["image"]
                print(f"[RAG] MongoDB 이미지: {image_url[:60]}...")
                return image_url
            else:
                print(f"[RAG] MongoDB에 이미지 없음: {recipe_id}")
                return ""
        except Exception as e:
            print(f"[RAG] MongoDB 조회 실패: {e}")
            return ""

    def _milvus_title_search(self, query: str, k: int) -> List[tuple]:
        """title 필드 기반 키워드 매칭 검색 (벡터 검색 보완용)"""
        try:
            collection = self.vectorstore.col
            output_fields = ["text", "title", "level", "cook_time", "source", "recipe_id"]

            # title에 쿼리 포함된 문서 필터 검색
            safe_query = query.replace('"', '\\"')
            expr = f'title like "%{safe_query}%"'

            t_title_start = _t()
            title_results = collection.query(
                expr=expr,
                output_fields=output_fields,
                limit=k
            )
            _log_step("Milvus title 검색", t_title_start, _t())

            if not title_results:
                return []

            print(f"  🎯 [title 매칭] {len(title_results)}개 발견!")
            docs_with_scores = []
            for hit in title_results:
                doc = Document(
                    page_content=hit.get("text", ""),
                    metadata={
                        "title": hit.get("title", "N/A"),
                        "level": hit.get("level", "N/A"),
                        "cook_time": hit.get("cook_time", "N/A"),
                        "source": hit.get("source", "N/A"),
                        "recipe_id": hit.get("recipe_id", ""),
                        "image_url": "",
                    }
                )
                docs_with_scores.append((doc, 0.0))  # title 매칭은 최고 점수
                print(f"    - {hit.get('title', 'N/A')}")

            return docs_with_scores

        except Exception as e:
            print(f"  [WARNING] title 검색 실패: {e}")
            return []

    def _milvus_search(self, query: str, k: int) -> List[tuple]:
        """pymilvus 직접 호출 - title 매칭 우선, 부족하면 벡터 검색 보완"""
        from pymilvus import Collection

        collection = self.vectorstore.col
        output_fields = ["text", "title", "level", "cook_time", "source", "recipe_id"]

        # ── 1단계: title 키워드 매칭 먼저 시도 ──
        title_results = self._milvus_title_search(query, k)

        if len(title_results) >= k:
            # title 매칭으로 충분하면 벡터 검색 스킵
            return title_results[:k]

        # ── 2단계: 벡터 검색 (title 매칭 부족할 때) ──
        t_emb_start = _t()
        query_embedding = self.embeddings.embed_query(query)
        _log_step("Embedding 생성", t_emb_start, _t())

        ef = max(k * 2, 50)
        search_params = {"metric_type": "L2", "params": {"ef": ef}}

        t_search_start = _t()
        results = collection.search(
            data=[query_embedding],
            anns_field="vector",
            param=search_params,
            limit=k,
            output_fields=output_fields
        )
        _log_step("Milvus ANN 검색", t_search_start, _t())

        vector_results = []
        for hit in results[0]:
            recipe_id = hit.entity.get("recipe_id", "")
            doc = Document(
                page_content=hit.entity.get("text", ""),
                metadata={
                    "title": hit.entity.get("title", "N/A"),
                    "level": hit.entity.get("level", "N/A"),
                    "cook_time": hit.entity.get("cook_time", "N/A"),
                    "source": hit.entity.get("source", "N/A"),
                    "recipe_id": recipe_id,
                    "image_url": "",
                }
            )
            vector_results.append((doc, hit.score))

        # ── title 결과 + 벡터 결과 합치기 (중복 제거) ──
        seen_titles = {doc.metadata.get("title") for doc, _ in title_results}
        merged = list(title_results)
        for doc, score in vector_results:
            if doc.metadata.get("title") not in seen_titles and len(merged) < k:
                merged.append((doc, score))
                seen_titles.add(doc.metadata.get("title"))

        return merged

    def search_recipes(
        self,
        query: str,
        k: int = 3,
        use_rerank: bool = False
    ) -> List[Dict]:
        """레시피 검색 (with optional CLOVA Studio reranking + image)"""

        t_total_start = _t()

        use_rerank = use_rerank if use_rerank is not None else self.use_reranker
        print(f"\n  📍 [search_recipes] 시작 (k={k}, rerank={use_rerank})")

        if use_rerank and self.reranker:
            search_k = min(k * 3, 20)

            # ── 타이밍: Milvus 검색 (embedding 포함) ──
            t_milvus_start = _t()
            docs_with_scores = self._milvus_search(query, search_k)
            total_end = _t()
            _log_step("search_recipes 합계", t_total_start, total_end)
            
            docs = [doc for doc, score in docs_with_scores]
            vector_scores = {id(doc): float(score) for doc, score in docs_with_scores}
            
            # ── 타이밍: Reranker API ──
            t_rerank_start = _t()
            reranked_results = self._rerank_documents(query, docs, top_n=k)
            _log_step("Reranker API", t_rerank_start, _t())
            
            results = []
            for doc, rerank_score in reranked_results:
                results.append({
                    "content": doc.page_content,
                    "vector_score": vector_scores.get(id(doc), 0.0),
                    "rerank_score": float(rerank_score),
                    "title": doc.metadata.get("title", "N/A"),
                    "author": doc.metadata.get("author", "N/A"),
                    "source": doc.metadata.get("source", "N/A"),
                    "cook_time": doc.metadata.get("cook_time", "N/A"),
                    "level": doc.metadata.get("level", "N/A"),
                    "recipe_id": doc.metadata.get("recipe_id", "N/A"),
                    "image": doc.metadata.get("image_url", ""),
                })
        else:
            # ── 타이밍: Milvus 검색만 (rerank 없음) ──
            t_milvus_start = _t()
            docs_with_scores = self._milvus_search(query, k)
            _log_step("Milvus 전체 (rerank 없음)", t_milvus_start, _t())

            results = []
            for doc, score in docs_with_scores:
                results.append({
                    "content": doc.page_content,
                    "vector_score": float(score),
                    "title": doc.metadata.get("title", "N/A"),
                    "author": doc.metadata.get("author", "N/A"),
                    "source": doc.metadata.get("source", "N/A"),
                    "cook_time": doc.metadata.get("cook_time", "N/A"),
                    "level": doc.metadata.get("level", "N/A"),
                    "recipe_id": doc.metadata.get("recipe_id", "N/A"),
                    "image": doc.metadata.get("image_url", ""),
                })

        _log_step("search_recipes 합계", t_total_start, _t())
        print(f"  📍 [search_recipes] 완료\n")
        return results

    def generate_answer(
        self,
        query: str,
        context_docs: List[Dict],
        system_prompt: Optional[str] = None
    ) -> str:
        """LangChain을 사용한 답변 생성"""

        print(f"  📍 [generate_answer] 시작")
        t_total_start = _t()

        if system_prompt is None:
            system_prompt = """당신은 한국 요리 전문가이자 친절한 레시피 어시스턴트입니다.

# 🚨 절대 규칙
1. **반드시 하나의 요리만 추천하세요!**
2. **여러 요리를 리스트로 나열하지 마세요!**
3. **조리법은 1~2줄로 간단히!**

# 필수 답변 형식

오늘의 추천 요리는 [요리명] 입니다.

**재료 (N인분, 조리시간):**
- 주요 재료 5~7개만 간단히 나열

**조리법:**
1~2줄로 핵심만 요약

**특징:**
한 줄로 이 요리의 매력 설명

{context}"""

        # Document 객체로 변환
        documents = []
        for doc_dict in context_docs:
            doc = Document(
                page_content=doc_dict.get("content", ""),
                metadata={
                    "title": doc_dict.get("title", "N/A"),
                    "author": doc_dict.get("author", "N/A"),
                    "source": doc_dict.get("source", "N/A"),
                }
            )
            documents.append(doc)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        # 체인 생성
        question_answer_chain = create_stuff_documents_chain(self.chat_model, prompt)

        # ── 타이밍: LLM 호출 ──
        t_llm_start = _t()
        try:
            result = question_answer_chain.invoke({
                "input": query,
                "context": documents
            })
            _log_step("LLM 호출 (generate_answer)", t_llm_start, _t())
            _log_step("generate_answer 합계", t_total_start, _t())
            print(f"  📍 [generate_answer] 완료\n")
            return result
        except Exception as e:
            _log_step("LLM 호출 (FAILED)", t_llm_start, _t())
            print(f"답변 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"

    def generate_recipe_json(
        self,
        user_message: str,
        context_docs: List[Dict],
        constraints_text: str = "",
        conversation_history: str = "",
        system_prompt: Optional[str] = None,
    ) -> dict:
        """JSON 구조화된 레시피 생성"""

        print(f"  📍 [generate_recipe_json] 시작")
        t_total_start = _t()
        
        if system_prompt is None:
            system_prompt = """당신은 한국 요리 전문가입니다. 

# 역할
주어진 레시피 데이터베이스와 **대화 히스토리**를 참고하여 사용자가 원하는 요리 레시피를 JSON 형식으로 **상세하게** 생성해주세요.

# 사용자 제약사항
{constraints_text}

# 대화 히스토리 (매우 중요!)
{conversation_history}

**중요**: 
- 대화 히스토리를 꼼꼼히 읽고 사용자의 모든 요구사항을 반영하세요
- 알레르기와 비선호 재료는 절대 사용하지 마세요

# 출력 형식
반드시 다음 JSON 형식만 출력하고, 다른 설명은 붙이지 마세요:
{{{{
"title": "요리 이름",
"intro": "한 줄 소개",
"cook_time": "예: 10~15분",
"level": "예: 초급",
"servings": "예: 2인분",
"ingredients": [
    {{{{"name": "재료명", "amount": "양", "note": "선택사항"}}}}
],
"steps": [
    {{{{"no": 1, "desc": "구체적이고 상세한 설명"}}}},
    {{{{"no": 2, "desc": "..."}}}}
],
}}}}

{{context}}"""

        # 시스템 프롬프트 포맷팅
        formatted_system_prompt = system_prompt.format(
            constraints_text=constraints_text if constraints_text else "없음",
            conversation_history=conversation_history if conversation_history else "없음",
            context="{context}"
        )

        # Document 객체로 변환
        documents = []
        for doc_dict in context_docs:
            doc = Document(
                page_content=doc_dict.get("content", ""),
                metadata={
                    "title": doc_dict.get("title", "N/A"),
                    "author": doc_dict.get("author", "N/A"),
                    "source": doc_dict.get("source", "N/A"),
                }
            )
            documents.append(doc)

        # 프롬프트 생성
        prompt = ChatPromptTemplate.from_messages([
            ("system", formatted_system_prompt),
            ("human", "{input}"),
        ])

        # 체인 생성
        question_answer_chain = create_stuff_documents_chain(self.chat_model, prompt)

        # ── 타이밍: LLM 호출 ──
        t_llm_start = _t()
        try:
            result = question_answer_chain.invoke({
                "input": user_message,
                "context": documents,
            })
            _log_step("LLM 호출 (generate_recipe_json)", t_llm_start, _t())

            response_text = result if isinstance(result, str) else str(result)

        except Exception as e:
            _log_step("LLM 호출 (FAILED)", t_llm_start, _t())
            print(f"LLM 호출 오류: {e}")
            _log_step("generate_recipe_json 합계", t_total_start, _t())
            return self._get_default_recipe()

        # ── 타이밍: JSON 파싱 ──
        t_parse_start = _t()
        try:
            clean_result = response_text.strip()
            if clean_result.startswith("```json"):
                clean_result = clean_result[7:]
            if clean_result.startswith("```"):
                clean_result = clean_result[3:]
            if clean_result.endswith("```"):
                clean_result = clean_result[:-3]

            parsed_json = json.loads(clean_result.strip())
            _log_step("JSON 파싱", t_parse_start, _t())
            print(f"✅ 레시피 JSON 생성 성공: {parsed_json.get('title', 'N/A')}")
            _log_step("generate_recipe_json 합계", t_total_start, _t())
            print(f"  📍 [generate_recipe_json] 완료\n")
            return parsed_json

        except json.JSONDecodeError as e:
            _log_step("JSON 파싱 (FAILED)", t_parse_start, _t())
            print(f"JSON 파싱 오류: {e}")
            _log_step("generate_recipe_json 합계", t_total_start, _t())
            return self._get_default_recipe()

    def _get_default_recipe(self) -> dict:
        """기본 레시피 반환 (오류 시)"""
        return {
            "title": "레시피 생성 실패",
            "intro": "레시피를 생성하는 중 오류가 발생했습니다.",
            "cook_time": "N/A",
            "level": "N/A",
            "servings": "N/A",
            "ingredients": [],
            "steps": [],
        }

    def query(
        self,
        question: str,
        top_k: int = 5,
        use_rerank: bool = None,
        return_references: bool = True
    ) -> Dict[str, Any]:
        """질문에 대한 답변 생성 (검색 + 생성 통합)"""

        print(f"\n{'='*50}")
        print(f"  🔍 [query] 시작: \"{question[:40]}...\"")
        print(f"{'='*50}")
        t_query_start = _t()

        # 1. 검색
        retrieved_docs = self.search_recipes(question, k=top_k, use_rerank=use_rerank)

        # 2. 답변 생성
        answer = self.generate_answer(question, retrieved_docs)

        result = {
            "question": question,
            "answer": answer,
        }

        if return_references:
            result["references"] = retrieved_docs
            result["num_references"] = len(retrieved_docs)

        _log_step("query() 전체 합계", t_query_start, _t())
        print(f"{'='*50}\n")
        return result