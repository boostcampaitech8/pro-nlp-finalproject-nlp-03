"""
rag_baseline_upgraded.py
레시피 RAG 시스템 - LangChain + CLOVA X + 테스트
- ClovaXEmbeddings (bge-m3) 사용
- ChatClovaX (HCX-003) 사용
- Reranker 지원 (bge-reranker-v2-m3)
- Naive/Advanced RAG 테스트 + 로그 저장 통합
"""

import json
import os
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# LangChain CLOVA X
try:
    from langchain_naver import ChatClovaX, ClovaXEmbeddings
except ImportError:
    from langchain_community.chat_models import ChatClovaX
    from langchain_community.embeddings import ClovaXEmbeddings

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

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

# 환경변수 로드
load_dotenv()

# 테스트 쿼리 세트
NAIVE_TEST_QUERIES = [
    "아 맞다, 저기 있잖아. 오늘 저녁에 남편이랑 된장찌개나 좀 끓여 먹으려고 하는데 맛있게 만드는 방법 좀 자세히 알려줄래?",
    "아니 글쎄 시골에서 감자를 한 박스나 보내주셔서... 감자가 집에 너무 많거든. 이거 처치 곤란인데 감자조림 만드는 거 좀 찾아줘 봐.",
    "어휴, 어제 술을 너무 많이 마셨나 봐. 콩나물국 시원하게 끓이는 법 좀 알려줄래? 속 풀리게 해장용으로 말이야.",
    "날씨가 쌀쌀해지니까 뜨끈한 김치찌개가 생각나네. 돼지고기 팍팍 넣고 제대로 깊은 맛 나게 만드는 비법 좀 알려줘.",
    "아까 마트 갔더니 고등어가 싱싱해 보이더라고. 고등어조림 하려는데 비린내 안 나고 매콤하게 만드는 황금 레시피 좀.",
    "비도 오고 그래서 부침개가 확 땡기네. 김치전 바삭바삭하게 만드는 게 은근 어렵더라고. 눅눅하지 않게 만드는 팁 좀 알려줘.",
    "오늘 비빔밥 해 먹을 건데, 그 비빔장 양념 있지? 식당에서 파는 것처럼 새콤달콤하게 만드는 비율 좀 가르쳐줄래?",
]

ADVANCED_TEST_QUERIES = [
    "우리 애들 오늘 일찍 오는데, 간식으로 떡볶이 좀 해주려고. 근데 애들이라 너무 매우면 못 먹으니까 안 맵게 만드는 법 있을까?",
    "오늘 저녁 메뉴는 제육볶음으로 정했는데, 내가 고기 비린내에 좀 민감해서... 고기 잡내 하나도 안 나게 하는 법 위주로 알려줄래?",
    "나 지금 바로 미역국 끓여야 되는데 냉장고 보니까 고기가 없네? 소고기 없이도 맛있게 하는 법 있으면 빨리 좀 알려줘.",
    "요즘 계속 배달만 시켜 먹었더니 지겨워서... 그냥 혼자 대충 먹을 거거든. 계란말이 아주 간단하게 하는 법 없을까?",
    "음... 갑자기 꾸덕한 크림 파스타 같은 게 막 먹고 싶네. 요리 초보도 집에서 쉽게 따라 할 수 있는 법 좀 가르쳐줘.",
    "저기 그... 어디서 들었는데 카레 할 때 사과를 넣으면 풍미가 확 산다며? 사과를 언제 어떻게 넣어야 하는지 알려줄 수 있어?",
    "출출한데 간식으로 샌드위치나 한번 만들어 볼까 싶어서. 냉장고에 있는 재료로 대충 만들 수 있는 레시피 좀 보여줘.",
    "아 맞다, 나 지금 다이어트 중인 거 깜빡했네! 닭가슴살로 할 수 있는 요리 중에 칼로리 낮고 맛있는 거 뭐 없을까?",
    "친구들이 갑자기 집으로 온다는데 어떡하지? 한 20분 안에 후다닥 만들 수 있는 근사한 손님 초대 요리 좀 추천해 줄래?",
    "저기, 혹시 집에 오븐 없어도 에어프라이어로 통삼겹 구이 할 수 있어? 온도랑 시간 설정 같은 거 어떻게 하는지 알려줘.",
    "요즘 채소를 너무 안 먹는 것 같아서 말이야. 시금치나물 같은 거 밑반찬으로 좀 해두려고 하는데, 색깔 안 변하게 무치는 법 알아?",
    "주말 아침이라 좀 귀찮긴 한데... 브런치 느낌으로다가 프렌치토스트 좀 해먹으려고. 설탕 적게 쓰고 달콤하게 만드는 법 있을까?",
    "아이고, 집에 간장이 다 떨어졌네? 간장 대신 소금이나 다른 걸로 간 맞춰서 잡채 만드는 법 혹시 알 수 있을까?",
    "애기 이유식 시작하려고 하는데, 초기 이유식으로 단호박 미음 만드는 거 좀 알려줘. 알레르기 주의사항 같은 것도 있으면 좋고.",
    "어제 먹다 남은 치킨이 처치 곤란이라... 이거 활용해서 치킨마요 덮밥 같은 거 만들 수 있나? 남은 음식 활용법 좀 알려줘.",
    "와이프 생일이라 미역국이랑 갈비찜 좀 해주려고 하는데, 소갈비찜 부드럽게 하는 법이 제일 중요해. 압력솥 없는데 가능할까?",
    "저기요, 제가 요리를 아예 못하는 소위 '요알못'이거든요. 라면만큼 쉬운 볶음밥 레시피 딱 하나만 골라줘 봐요.",
    "요즘 건강 생각해서 저염식 하려고 노력 중이거든. 된장찌개 끓일 때 짜지 않게, 그러면서도 맛은 있게 하는 방법 있을까?",
    "아, 캠핑 왔는데 삼겹살 말고 좀 특별한 거 해 먹고 싶어서. 캠핑장에서 그리들 하나로 끝낼 수 있는 요리 좀 추천해 줄래?",
    "명절에 쓰고 남은 나물들이 냉장고에 가득해. 이거 한꺼번에 다 넣고 비빔밥 말고 좀 색다르게 먹는 법 없을까?",
    "아침에 바빠 죽겠는데 빈속으로 가긴 좀 그렇고... 5분 안에 빨리 먹고 나갈 수 있는 초간단 아침 식사 메뉴 좀 알려줄래?",
]


class RecipeRAGLangChain:
    """
    LangChain + CLOVA X 기반 레시피 RAG 시스템

    Features:
    - ClovaXEmbeddings (bge-m3) for vector search
    - ChatClovaX (HCX-003) for answer generation
    - Optional Reranker (bge-reranker-v2-m3)
    - Naive/Advanced RAG testing with logging
    """

    def __init__(
        self,
        milvus_host: str,
        milvus_port: str,
        collection_name: str,
        use_reranker: bool = False,
        reranker_model: str = "BAAI/bge-reranker-v2-m3",
        chat_model: str = "HCX-003",
        embedding_model: str = "bge-m3",
        temperature: float = 0.2,
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
        print(f"\n[1/4] CLOVA X Embeddings 초기화 중 (model: {embedding_model})")
        self.embeddings = ClovaXEmbeddings(model=embedding_model)
        print("[OK] Embeddings 초기화 완료")

        # 2. CLOVA X Chat 모델 초기화
        print(f"\n[2/4] CLOVA X Chat 모델 초기화 중 (model: {chat_model})")
        self.chat_model = ChatClovaX(
            model=chat_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        print("[OK] Chat 모델 초기화 완료")

        # 3. Reranker 초기화 (옵션)
        print("[3/4] Reranker 모델 로딩 중 (model: BAAI/bge-reranker-v2-m3)")
        try:
            from langchain_community.document_compressors import CrossEncoderReranker
            from langchain_community.cross_encoders import HuggingFaceCrossEncoder
            
            # Reranker 모델 로드
            model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")
            
            # Reranker 생성
            self.reranker = CrossEncoderReranker(
                model=model,
                top_n=5  # 상위 5개만 선택
            )
            
            print("[OK] Reranker 초기화 완료")
            
        except ImportError as e:
            print(f"[WARNING] Reranker 로딩 실패: {e}")
            print("          sentence-transformers 설치 필요: pip install sentence-transformers")
            print("          Reranker 없이 계속 진행합니다.")
            self.reranker = None
        except Exception as e:
            print(f"[WARNING] Reranker 로딩 실패: {e}")
            print("          Reranker 없이 계속 진행합니다.")
            self.reranker = None

        # 4. Milvus Vectorstore 연결
        print(f"\n[4/4] Milvus 연결 중 ({self.milvus_uri})")
        self.vectorstore = None
        self._connect_milvus()

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

    def load_recipes(self, json_path: str) -> List[Dict]:
        """레시피 JSON 파일 로드"""
        print(f"\n레시피 파일 로드 중: {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            recipes = json.load(f)
        print(f"[OK] 레시피 {len(recipes)}개 로드 완료")
        return recipes

    def process_recipe(self, recipe: Dict) -> str:
        """레시피를 텍스트로 변환 (검색 최적화)"""
        content_parts = [
            f"제목: {recipe.get('title', '')}",
            f"소개: {recipe.get('intro', '')}",
            f"분량: {recipe.get('portion', '')}",
            f"조리시간: {recipe.get('cook_time', '')}",
            f"난이도: {recipe.get('level', '')}"
        ]

        # 재료
        ingredients = recipe.get('ingredients', [])
        if ingredients:
            content_parts.append("\n재료:")
            for ing in ingredients:
                name = ing.get('name', '')
                amount = ing.get('amount', '')
                desc = ing.get('desc', '')
                ing_text = f"- {name}"
                if amount:
                    ing_text += f" {amount}"
                if desc:
                    ing_text += f" ({desc})"
                content_parts.append(ing_text)

        # 조리법
        steps = recipe.get('steps', [])
        if steps:
            content_parts.append("\n조리법:")
            for i, step in enumerate(steps, 1):
                step_desc = step.get('desc', '')
                if step_desc:
                    content_parts.append(f"{i}. {step_desc}")

        # 태그
        tags = recipe.get('tags', [])
        if tags:
            content_parts.append(f"\n태그: {', '.join(tags)}")

        return '\n'.join(content_parts)

    def index_recipes(self, recipes: List[Dict], batch_size: int = 100):
        """레시피 인덱싱 (LangChain + Milvus)"""
        print("\n" + "="*60)
        print("레시피 인덱싱 시작")
        print("="*60)

        # Document 객체 생성
        print("\n[1/3] Document 객체 생성 중...")
        documents = []
        for i, recipe in enumerate(recipes, 1):
            if i % 100 == 0:
                print(f"   진행: {i}/{len(recipes)}")

            content = self.process_recipe(recipe)

            metadata = {
                "recipe_id": str(recipe.get('recipe_id', '')),
                "title": recipe.get('title', ''),
                "author": recipe.get('author', ''),
                "source": recipe.get('detail_url', ''),
                "portion": recipe.get('portion', ''),
                "cook_time": recipe.get('cook_time', ''),
                "level": recipe.get('level', ''),
            }

            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)

        print(f"[OK] Document {len(documents)}개 생성 완료")

        # 기존 컬렉션 삭제
        print("\n[2/3] 기존 컬렉션 확인 및 삭제...")
        connections.connect(host=self.milvus_host, port=self.milvus_port)
        if utility.has_collection(self.collection_name):
            print(f"      기존 컬렉션 삭제: {self.collection_name}")
            utility.drop_collection(self.collection_name)

        # Milvus에 인덱싱
        print("\n[3/3] Milvus 인덱싱 중 (시간이 걸릴 수 있습니다)")
        self.vectorstore = Milvus.from_documents(
            documents,
            self.embeddings,
            collection_name=self.collection_name,
            connection_args={"uri": self.milvus_uri},
        )

        print("\n" + "="*60)
        print(f"인덱싱 완료: 총 {len(recipes)}개 레시피")
        print("="*60 + "\n")

    def search_recipes(
        self,
        query: str,
        k: int = 5,
        use_rerank: bool = None
    ) -> List[Dict]:
        """레시피 검색 (with optional reranking)"""
        use_rerank = use_rerank if use_rerank is not None else self.use_reranker

        # 벡터 검색
        if use_rerank and self.reranker:
            # Reranker 사용 시 더 많이 검색 후 rerank
            search_k = k * 3
            docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=search_k)

            # Rerank
            items = []
            for doc, vec_score in docs_with_scores:
                text_short = doc.page_content[:1200]
                rerank_score = float(self.reranker.score([query, text_short]))

                items.append({
                    "document": doc,
                    "vector_score": float(vec_score),
                    "rerank_score": rerank_score,
                })

            # Rerank 점수로 정렬 후 상위 k개
            items = sorted(items, key=lambda x: x["rerank_score"], reverse=True)[:k]

            # 결과 포맷팅
            results = []
            for item in items:
                doc = item["document"]
                results.append({
                    "content": doc.page_content,
                    "vector_score": item["vector_score"],
                    "rerank_score": item["rerank_score"],
                    "title": doc.metadata.get("title", "N/A"),
                    "author": doc.metadata.get("author", "N/A"),
                    "source": doc.metadata.get("source", "N/A"),
                    "cook_time": doc.metadata.get("cook_time", "N/A"),
                    "level": doc.metadata.get("level", "N/A"),
                })

        else:
            # 일반 벡터 검색만
            docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=k)

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
                })

        return results

    def generate_answer(
        self,
        query: str,
        context_docs: List[Dict],
        system_prompt: Optional[str] = None
    ) -> str:
        """LangChain을 사용한 답변 생성"""
        if system_prompt is None:
            system_prompt = """당신은 한국 요리 전문가이자 친절한 레시피 어시스턴트입니다.

    # 🚨 절대 규칙 (위반 시 심각한 오류!)
    1. **반드시 하나의 요리만 추천하세요!**
    2. **여러 요리를 리스트로 나열하지 마세요!** (1., 2., 3. 형식 금지!)
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

        # 실행
        try:
            result = question_answer_chain.invoke({
                "input": query,
                "context": documents
            })
            return result
        except Exception as e:
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
    - 예: "매콤하게" → 고춧가루 양 증가
    - 예: "간단하게" → 단계 수 최소화
    - 예: "빨리" → 조리 시간 단축
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
        {{{{"no": 1, "desc": "구체적이고 상세한 설명 (불 세기, 시간, 순서 포함)"}}}},
        {{{{"no": 2, "desc": "..."}}}}
    ],
    "tips": ["실용적인 팁1", "실패 방지 팁2", "응용 팁3"]
    }}}}

    # 조리법 작성 규칙
    - 각 단계는 매우 구체적으로 작성 (예: "중불에서 5분간", "황금색이 될 때까지")
    - 초보자도 따라할 수 있도록 친절하게 설명
    - 중요한 타이밍이나 주의사항 명시
    - 최소 5단계 이상 작성

    {{context}}"""

        # 시스템 프롬프트 먼저 포맷팅 (constraints_text, conversation_history 채우기)
        formatted_system_prompt = system_prompt.format(
            constraints_text=constraints_text if constraints_text else "없음",
            conversation_history=conversation_history if conversation_history else "없음",
            context="{context}"  # 이건 LangChain이 채울 거라 남겨둠
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

        # 실행
        try:
            result = question_answer_chain.invoke({
                "input": user_message,
                "context": documents,
            })

            # 응답 텍스트 추출
            response_text = result if isinstance(result, str) else str(result)

        except Exception as e:
            print(f"LLM 호출 오류: {e}")
            import traceback
            traceback.print_exc()
            return self._get_default_recipe()

        # JSON 파싱
        try:
            # 마크다운 코드 블록 제거
            clean_result = response_text.strip()
            if clean_result.startswith("```json"):
                clean_result = clean_result[7:]
            if clean_result.startswith("```"):
                clean_result = clean_result[3:]
            if clean_result.endswith("```"):
                clean_result = clean_result[:-3]

            parsed_json = json.loads(clean_result.strip())
            print(f"✅ 레시피 JSON 생성 성공: {parsed_json.get('title', 'N/A')}")
            return parsed_json

        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            print(f"응답 내용 (처음 500자):\n{response_text[:500]}...")
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
            "tips": []
        }

    def query(
        self,
        question: str,
        top_k: int = 5,
        use_rerank: bool = None,
        return_references: bool = True
    ) -> Dict[str, Any]:
        """질문에 대한 답변 생성 (검색 + 생성 통합)"""
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

        return result

    # ========================================
    # 테스트 기능 통합
    # ========================================

    def save_test_log(self, log_data: dict, test_type: str, log_dir: str = "./test_logs"):
        """테스트 결과를 JSON과 TXT로 저장"""
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON 저장
        json_filename = f"{log_dir}/{test_type}_{timestamp}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

        # TXT 저장
        txt_filename = f"{log_dir}/{test_type}_{timestamp}.txt"
        with open(txt_filename, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(f"{test_type.upper().replace('_', ' ')} 테스트 결과\n")
            f.write(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            for result in log_data.get("results", []):
                f.write(f"\n{'='*80}\n")
                f.write(f"질문: {result.get('question', result.get('query',''))}\n")
                f.write(f"{'='*80}\n\n")
                f.write("답변:\n")
                f.write(f"{result.get('answer','')}\n\n")

                refs = result.get("references", [])
                f.write(f"참조 레시피 (총 {len(refs)}개):\n")
                f.write("-" * 80 + "\n")

                for i, ref in enumerate(refs, 1):
                    title = ref.get("title", "N/A")
                    author = ref.get("author", "N/A")
                    cook_time = ref.get("cook_time", "N/A")
                    level = ref.get("level", "N/A")
                    source = ref.get("source", "N/A")

                    f.write(f"\n[Rank {i}] {title}\n")
                    if 'rerank_score' in ref:
                        f.write(f"  Rerank Score: {ref['rerank_score']:.4f}\n")
                    if 'vector_score' in ref:
                        f.write(f"  Vector Score: {ref['vector_score']:.4f}\n")
                    f.write(f"  작성자: {author}\n")
                    f.write(f"  난이도: {level} | 조리시간: {cook_time}\n")
                    f.write(f"  URL: {source}\n")
                    f.write("-" * 80 + "\n")

        print(f"\n[로그 저장 완료]")
        print(f"  JSON: {json_filename}")
        print(f"  TXT:  {txt_filename}")
        return json_filename, txt_filename

    def test_naive_rag(self, queries: List[str] = None, log_dir: str = "./test_logs"):
        """Naive RAG 테스트 (LangChain RAG Chain 사용)"""
        if queries is None:
            queries = NAIVE_TEST_QUERIES

        print("\n" + "="*80)
        print("Naive RAG 테스트 시작")
        print(f"총 {len(queries)}개 질문")
        print("="*80)

        log_results = []

        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] {query[:50]}...")

            try:
                result = self.query(query, top_k=5, use_rerank=False)
                log_results.append(result)

                # 답변 미리보기
                answer_preview = result['answer'][:150].replace('\n', ' ')
                print(f"답변: {answer_preview}...")

            except Exception as e:
                print(f"[ERROR] {e}")
                log_results.append({
                    "question": query,
                    "answer": f"오류 발생: {str(e)}",
                    "references": [],
                    "num_references": 0
                })

        # 로그 저장
        log_data = {
            "test_type": "Naive RAG",
            "timestamp": datetime.now().isoformat(),
            "num_queries": len(queries),
            "results": log_results,
        }
        self.save_test_log(log_data, "naive_rag", log_dir)

        print("\n" + "="*80)
        print("Naive RAG 테스트 완료!")
        print("="*80)

        return log_data

    def test_advanced_rag(self, queries: List[str] = None, log_dir: str = "./test_logs"):
        """Advanced RAG 테스트 (Reranker 사용)"""
        if queries is None:
            queries = ADVANCED_TEST_QUERIES

        if not self.use_reranker or not self.reranker:
            print("\n[WARNING] Reranker가 활성화되지 않았습니다.")
            print("          use_reranker=True로 초기화해주세요.")
            return None

        print("\n" + "="*80)
        print("Advanced RAG 테스트 시작 (Reranker 사용)")
        print(f"총 {len(queries)}개 질문")
        print("="*80)

        log_results = []

        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] {query[:50]}...")

            try:
                result = self.query(query, top_k=5, use_rerank=True)
                log_results.append(result)

                # 답변 미리보기
                answer_preview = result['answer'][:150].replace('\n', ' ')
                print(f"답변: {answer_preview}...")

            except Exception as e:
                print(f"[ERROR] {e}")
                log_results.append({
                    "question": query,
                    "answer": f"오류 발생: {str(e)}",
                    "references": [],
                    "num_references": 0
                })

        # 로그 저장
        log_data = {
            "test_type": "Advanced RAG (Reranker)",
            "timestamp": datetime.now().isoformat(),
            "num_queries": len(queries),
            "results": log_results,
        }
        self.save_test_log(log_data, "advanced_rag", log_dir)

        print("\n" + "="*80)
        print("Advanced RAG 테스트 완료!")
        print("="*80)

        return log_data


def main():
    """메인 함수"""
    MILVUS_HOST = "136.113.251.237"
    MILVUS_PORT = "19530"
    COLLECTION_NAME = "recipe_docs"

    print("="*80)
    print("Recipe RAG System")
    print("="*80)

    # API 키 확인
    if not os.getenv("CLOVASTUDIO_API_KEY"):
        print("\n[ERROR] CLOVASTUDIO_API_KEY 환경변수가 설정되지 않았습니다.")
        return

    # RAG 시스템 초기화
    rag = RecipeRAGLangChain(
        milvus_host=MILVUS_HOST,
        milvus_port=MILVUS_PORT,
        collection_name=COLLECTION_NAME,
        use_reranker=True,  # Reranker 사용
    )

    # 메뉴
    print("\n메뉴:")
    print("1. 단일 질문 테스트")
    print("2. Naive RAG 테스트 (7개)")
    print("3. Advanced RAG 테스트 (21개)")
    print("4. 전체 테스트 (28개)")

    choice = input("\n선택 (1-4): ").strip()

    if choice == "1":
        query = input("\n질문: ")
        result = rag.query(query, top_k=5, use_rerank=True)
        print(f"\n답변:\n{result['answer']}")
        print(f"\n참조 레시피 ({result['num_references']}개):")
        for i, ref in enumerate(result['references'], 1):
            print(f"  [{i}] {ref['title']}")

    elif choice == "2":
        rag.test_naive_rag()

    elif choice == "3":
        rag.test_advanced_rag()

    elif choice == "4":
        rag.test_naive_rag()
        rag.test_advanced_rag()

    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()