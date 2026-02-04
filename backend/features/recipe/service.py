# # backend/features/recipe/service.py
# """
# Recipe 비즈니스 로직
# """
# import os
# from pymongo import MongoClient
# from typing import List, Dict, Any
# from .prompts import RECIPE_QUERY_EXTRACTION_PROMPT, RECIPE_GENERATION_PROMPT

# class RecipeService:
#     def __init__(self, rag_system, recipe_db, user_profile=None):
#         mongo_uri = os.getenv("MONGO_URI", "mongodb://root:RootPassword123@136.113.251.237:27017/admin")
#         self.mongo_client = MongoClient(mongo_uri)
#         self.recipe_db = self.mongo_client["recipe_db"]
#         self.recipes_collection = self.recipe_db["recipes"]
#         self.rag = rag_system
#         self.db = recipe_db
#         self.user_profile = user_profile or {}
    
#     async def generate_recipe(
#         self, 
#         chat_history: List[Dict[str, str]],
#         member_info: Dict[str, Any] = None
#     ) -> Dict[str, Any]:
#         """상세 레시피 생성 (대화 기반) + 이미지 URL"""
        
#         print(f"[RecipeService] 레시피 생성 시작")
#         print(f"[RecipeService] 대화 개수: {len(chat_history)}")
#         print(f"[RecipeService] 가족 정보: {member_info}")
        
#         # 1. LLM으로 대화 분석 + 검색 쿼리 생성
#         search_query = self._extract_search_query_with_llm(chat_history, member_info)
        
#         print(f"[RecipeService] 생성된 검색 쿼리: {search_query}")
        
#         # 2. RAG 검색
#         retrieved_docs = self.rag.search_recipes(search_query, k=10, use_rerank=True)
        
#         print(f"[RecipeService] RAG 검색 결과: {len(retrieved_docs)}개")
        
#         # 3. 알레르기/비선호 필터링
#         filtered_docs = self._filter_by_constraints(retrieved_docs, member_info)
        
#         print(f"[RecipeService] 필터링 후: {len(filtered_docs)}개")
        
#         # 4. LLM으로 최종 레시피 생성
#         recipe_json = self._generate_final_recipe_with_llm(
#             chat_history=chat_history,
#             member_info=member_info,
#             context_docs=filtered_docs
#         )
        
#         print(f"[RecipeService] 레시피 생성 완료: {recipe_json.get('title')}")
        
#         # 5. 생성된 레시피 제목으로 MongoDB에서 직접 이미지 검색!
#         recipe_title = recipe_json.get('title', '')
#         best_image = ""
        
#         if recipe_title:
#             best_image = self._find_image_by_title(recipe_title)
        
#         # 실패하면 원본 검색 결과에서
#         if not best_image:
#             print(f"[RecipeService] 제목 검색 실패 → 원본 검색 결과 사용")
#             best_image = self._get_best_image(filtered_docs)
        
#         print(f"[RecipeService] 선택된 이미지: {best_image or '없음'}")
        
#         # 6. 이미지 URL 추가
#         recipe_json['image'] = best_image
#         recipe_json['img_url'] = best_image
        
#         # 7. 인원수 설정
#         servings = len(member_info.get('names', [])) if member_info and member_info.get('names') else 1
#         if 'servings' not in recipe_json or not recipe_json['servings']:
#             recipe_json['servings'] = f"{servings}인분"
        
#         print(f"[RecipeService] 최종 레시피: {recipe_json.get('title')}")
#         print(f"[RecipeService] 인원수: {recipe_json['servings']}")
#         print(f"[RecipeService] 이미지: {recipe_json.get('image', 'None')[:60]}...")
        
#         return recipe_json
    
#     def _find_image_by_title(self, title: str) -> str:
#         """MongoDB에서 제목으로 이미지 직접 검색 (빠름!)"""
#         try:
#             # 정확한 매칭 시도
#             recipe = self.recipes_collection.find_one(
#                 {"title": {"$regex": title, "$options": "i"}}, 
#                 {"image": 1, "recipe_id": 1, "_id": 0}
#             )
            
#             if recipe and "image" in recipe:
#                 image_url = recipe["image"]
#                 recipe_id = recipe.get("recipe_id", "")
#                 print(f"[RecipeService] MongoDB 제목 매칭: {title} → {recipe_id}")
#                 print(f"[RecipeService] 이미지: {image_url[:60]}...")
#                 return image_url
            
#             # 부분 매칭 시도 (예: "두쫀쿠" → "두바이 쫀득 쿠키")
#             # 제목의 주요 키워드 추출
#             keywords = [word for word in title.split() if len(word) > 1]
            
#             if keywords:
#                 # 키워드로 검색
#                 recipe = self.recipes_collection.find_one(
#                     {"title": {"$regex": "|".join(keywords), "$options": "i"}},
#                     {"image": 1, "recipe_id": 1, "title": 1, "_id": 0}
#                 )
                
#                 if recipe and "image" in recipe:
#                     image_url = recipe["image"]
#                     matched_title = recipe.get("title", "")
#                     print(f"[RecipeService] MongoDB 키워드 매칭: {title} → {matched_title}")
#                     print(f"[RecipeService] 이미지: {image_url[:60]}...")
#                     return image_url
            
#             print(f"[RecipeService] MongoDB 제목 검색 실패: {title}")
#             return ""
            
#         except Exception as e:
#             print(f"[RecipeService] MongoDB 제목 검색 실패: {e}")
#             return ""
    
#     def _get_image_from_mongo(self, recipe_id: str) -> str:
#         """MongoDB에서 레시피 이미지 URL 가져오기"""
#         try:
#             recipe = self.recipes_collection.find_one(
#                 {"recipe_id": recipe_id},
#                 {"image": 1, "_id": 0}
#             )
            
#             if recipe and "image" in recipe:
#                 image_url = recipe["image"]
#                 print(f"[RecipeService] MongoDB 이미지: {image_url[:50]}...")
#                 return image_url
#             else:
#                 print(f"[RecipeService] MongoDB에 이미지 없음: recipe_id={recipe_id}")
#                 return ""
                
#         except Exception as e:
#             print(f"[RecipeService] MongoDB 이미지 조회 실패: {e}")
#             return ""
    
#     def _get_best_image(self, filtered_docs: List[Dict]) -> str:
#         """필터링된 레시피 중 이미지 선택 (MongoDB 우선)"""
#         for doc in filtered_docs:
#             recipe_id = doc.get('recipe_id', '')
            
#             if recipe_id:
#                 # MongoDB에서 이미지 조회
#                 image_url = self._get_image_from_mongo(recipe_id)
#                 if image_url:
#                     return image_url
            
#             # fallback: RAG 메타데이터에서
#             image_url = doc.get('image_url', '')
#             if image_url:
#                 print(f"[RecipeService] RAG 메타데이터 이미지 사용")
#                 return image_url
        
#         print("[RecipeService] 이미지 없음")
#         return ""
    
#     def _extract_search_query_with_llm(
#         self, 
#         chat_history: List[Dict],
#         member_info: Dict
#     ) -> str:
#         """LLM으로 검색 쿼리 추출"""
        
#         conversation = "\n".join([
#             f"{msg['role']}: {msg['content']}"
#             for msg in chat_history[-10:]
#         ])
        
#         servings = len(member_info.get('names', [])) if member_info else 1
#         allergies = ', '.join(member_info.get('allergies', [])) if member_info else '없음'
#         dislikes = ', '.join(member_info.get('dislikes', [])) if member_info else '없음'
        
#         # 프롬프트 사용
#         prompt = RECIPE_QUERY_EXTRACTION_PROMPT.format(
#             conversation=conversation,
#             servings=servings,
#             allergies=allergies,
#             dislikes=dislikes
#         )
        
#         from langchain_naver import ChatClovaX
#         llm = ChatClovaX(model="HCX-003", temperature=0.1, max_tokens=50)
        
#         try:
#             result = llm.invoke(prompt)
#             query = result.content.strip()
#             print(f"[RecipeService] LLM 추출 쿼리: {query}")
#             return query
#         except Exception as e:
#             print(f"[RecipeService] 쿼리 추출 실패: {e}")
#             return self._simple_keyword_extraction(chat_history)
    
#     def _simple_keyword_extraction(self, chat_history: List[Dict]) -> str:
#         """간단한 키워드 추출 (Fallback)"""
#         food_keywords = []
        
#         for msg in chat_history:
#             if msg.get('role') == 'user':
#                 content = msg.get('content', '').lower()
#                 if any(k in content for k in ['찌개', '국', '탕', '볶음', '구이', '조림']):
#                     words = content.split()
#                     food_keywords.extend([w for w in words if len(w) > 1])
        
#         return ' '.join(food_keywords[:5]) if food_keywords else "한식 요리"
    
#     def _filter_by_constraints(
#         self,
#         recipes: List[Dict],
#         member_info: Dict
#     ) -> List[Dict]:
#         """알레르기/비선호 필터링"""
        
#         if not member_info:
#             return recipes[:5]
        
#         filtered = []
        
#         for recipe in recipes:
#             content = recipe.get("content", "").lower()
            
#             # 알레르기 체크
#             if member_info.get("allergies"):
#                 has_allergen = any(
#                     allergen.lower() in content 
#                     for allergen in member_info["allergies"]
#                 )
#                 if has_allergen:
#                     continue
            
#             # 비선호 재료 체크
#             if member_info.get("dislikes"):
#                 has_dislike = any(
#                     dislike.lower() in content 
#                     for dislike in member_info["dislikes"]
#                 )
#                 if has_dislike:
#                     continue
            
#             filtered.append(recipe)
            
#             if len(filtered) >= 5:
#                 break
        
#         if len(filtered) < 3:
#             return recipes[:3]
        
#         return filtered
    
#     def _generate_final_recipe_with_llm(
#         self,
#         chat_history: List[Dict],
#         member_info: Dict,
#         context_docs: List[Dict]
#     ) -> Dict:
#         """LLM으로 최종 레시피 JSON 생성"""
        
#         conversation = "\n".join([
#             f"{msg['role']}: {msg['content']}"
#             for msg in chat_history
#         ])
        
#         context_text = "\n\n".join([
#             f"[레시피 {i+1}] {doc.get('title')}\n{doc.get('content', '')[:800]}"
#             for i, doc in enumerate(context_docs[:5])
#         ])
        
#         servings = len(member_info.get('names', [])) if member_info else 1
#         allergies = ', '.join(member_info.get('allergies', [])) if member_info else '없음'
#         dislikes = ', '.join(member_info.get('dislikes', [])) if member_info else '없음'
#         tools = ', '.join(member_info.get('tools', [])) if member_info else '모든 도구'
        
#         # 프롬프트 사용
#         prompt = RECIPE_GENERATION_PROMPT.format(
#             conversation=conversation,
#             servings=servings,
#             allergies=allergies,
#             dislikes=dislikes,
#             tools=tools,
#             context=context_text
#         )
        
#         from langchain_naver import ChatClovaX
#         llm = ChatClovaX(model="HCX-003", temperature=0.2, max_tokens=2000)
        
#         try:
#             result = llm.invoke(prompt)
#             response_text = result.content.strip()
            
#             # JSON 추출
#             import json
#             import re
            
#             # 마크다운 코드 블록 제거
#             response_text = re.sub(r'```json\s*|\s*```', '', response_text)
            
#             recipe_json = json.loads(response_text)
            
#             print(f"[RecipeService] 레시피 생성 성공: {recipe_json.get('title')}")
#             return recipe_json
            
#         except json.JSONDecodeError as e:
#             print(f"[RecipeService] JSON 파싱 실패: {e}")
#             print(f"[RecipeService] 응답: {response_text[:200]}")
            
#             # Fallback
#             return {
#                 "title": "추천 레시피",
#                 "intro": "레시피 생성 중 오류가 발생했습니다.",
#                 "cook_time": "30분",
#                 "level": "중급",
#                 "servings": f"{servings}인분",
#                 "ingredients": [],
#                 "steps": [],
#                 "tips": []
#             }
        
#         except Exception as e:
#             print(f"[RecipeService] 레시피 생성 실패: {e}")
#             import traceback
#             traceback.print_exc()
#             raise
# backend/features/recipe/service.py
"""
Recipe 비즈니스 로직
"""
import os
import json
import re
import time
import logging
from pymongo import MongoClient
from typing import List, Dict, Any
from langchain_naver import ChatClovaX
from .prompts import RECIPE_QUERY_EXTRACTION_PROMPT, RECIPE_REFINE_PROMPT

logger = logging.getLogger(__name__)

# ── 싱글턴 LLM ──
_llm_recipe = ChatClovaX(model="HCX-003", temperature=0.2, max_tokens=800)
_llm_query  = ChatClovaX(model="HCX-003", temperature=0.1, max_tokens=50)   # title 정리에도 재사용

# ── title 정리용 프롬프트 ──
_TITLE_CLEAN_PROMPT = """다음 레시피 제목에서 순수 요리명만 추출하세요.

제목: {title}

규칙:
- 미사여구, 괄호, 느낌표, 설명 제거
- 요리명만 출력 (단어만, 설명 없이)

예시:
- "쫀득하고, 바삭하고, 고소한! [두쫀쿠!]" → 두쫀쿠
- "깔끔하고 깔끔한! (김치찌개)" → 김치찌개
- "간단하고 맛있는 된장탕" → 된장탕
- "두쫀쿠" → 두쫀쿠

요리명:"""


def _clean_title_llm(title: str) -> str:
    """LLM으로 title에서 순수 요리명 추출"""
    # 이미 깔끔한 경우 (특수문자·공백 없고 짧으면) LLM 호출 안 함
    if len(title) <= 10 and not any(c in title for c in '!?,.[](）（【】·'):
        logger.info(f"[RecipeService] title 정리 스킵 (이미 깔끔): {title}")
        return title

    try:
        prompt = _TITLE_CLEAN_PROMPT.format(title=title)
        result = _llm_query.invoke(prompt)
        cleaned = result.content.strip()
        # 혹시 여러 줄이나 부수 설명이 붙었다면 첫 줄만
        cleaned = cleaned.split('\n')[0].strip()
        logger.info(f"[RecipeService] title 정리: '{title}' → '{cleaned}'")
        return cleaned
    except Exception as e:
        logger.warning(f"[RecipeService] title LLM 정리 실패, 원본 유지: {e}")
        return title


class RecipeService:
    def __init__(self, rag_system, recipe_db, user_profile=None):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://root:RootPassword123@136.113.251.237:27017/admin")
        self.mongo_client = MongoClient(mongo_uri)
        self.recipe_db = self.mongo_client["recipe_db"]
        self.recipes_collection = self.recipe_db["recipes"]
        self.rag = rag_system
        self.db = recipe_db
        self.user_profile = user_profile or {}
        self._last_timings: List[tuple] = []

    # ─────────────────────────────────────────────
    # 캐시 경로 (메인)
    # ─────────────────────────────────────────────
    async def generate_recipe_from_cached_docs(
        self,
        chat_history: List[Dict[str, str]],
        member_info: Dict[str, Any],
        cached_documents: List[Dict[str, Any]],
        last_agent_response: str = ""
    ) -> Dict[str, Any]:
        self._last_timings = []
        logger.info("[RecipeService] 캐시된 docs로 레시피 생성 시작")

        # ── 컨텍스트 준비 ──
        t0 = time.time()
        last_request = self._get_last_user_message(chat_history)
        base_recipe  = last_agent_response if last_agent_response else cached_documents[0].get("content", "")[:600]
        self._last_timings.append(("컨텍스트 준비", (time.time() - t0) * 1000))
        logger.info(f"[RecipeService] base_recipe: {base_recipe[:60]}...")
        logger.info(f"[RecipeService] last_request: {last_request}")

        # ── LLM 레시피 생성 ──
        t0 = time.time()
        recipe_json = self._generate_recipe_from_base(
            base_recipe=base_recipe,
            last_request=last_request,
            member_info=member_info
        )
        self._last_timings.append(("LLM 생성", (time.time() - t0) * 1000))

        # ── title 정리 ──
        t0 = time.time()
        recipe_json['title'] = _clean_title_llm(recipe_json.get('title', ''))
        self._last_timings.append(("title 정리", (time.time() - t0) * 1000))
        logger.info(f"[RecipeService] 레시피 생성 완료: {recipe_json.get('title')}")

        # ── 이미지 검색 (정리된 title 사용) ──
        t0 = time.time()
        best_image = self._find_image_by_title(recipe_json['title']) if recipe_json['title'] else ""
        if not best_image:
            best_image = self._get_best_image(cached_documents[:2])
        self._last_timings.append(("이미지 검색", (time.time() - t0) * 1000))
        logger.info(f"[RecipeService] 선택된 이미지: {best_image or '없음'}")

        # ── 최종 구성 ──
        t0 = time.time()
        recipe_json['image']   = best_image
        recipe_json['img_url'] = best_image
        servings = len(member_info.get('names', [])) if member_info and member_info.get('names') else 1
        if not recipe_json.get('servings'):
            recipe_json['servings'] = f"{servings}인분"
        self._last_timings.append(("최종 구성", (time.time() - t0) * 1000))

        logger.info(f"[RecipeService] 최종 레시피: {recipe_json.get('title')}, {recipe_json['servings']}")
        return recipe_json

    # ─────────────────────────────────────────────
    # 폴백 경로 (캐시 없음)
    # ─────────────────────────────────────────────
    async def generate_recipe(
        self,
        chat_history: List[Dict[str, str]],
        member_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        self._last_timings = []
        logger.info("[RecipeService] 레시피 생성 시작 (폴백 경로)")

        # 1. 쿼리 추출
        t0 = time.time()
        search_query = self._extract_search_query_with_llm(chat_history, member_info)
        self._last_timings.append(("쿼리 추출 LLM", (time.time() - t0) * 1000))

        # 2. RAG 검색
        t0 = time.time()
        # use_rerank=None -> RAG 시스템 설정(USE_RERANKER) 따름
        retrieved_docs = self.rag.search_recipes(search_query, k=3, use_rerank=None)
        self._last_timings.append(("RAG 검색", (time.time() - t0) * 1000))

        # 3. 필터링
        t0 = time.time()
        filtered_docs = self._filter_by_constraints(retrieved_docs, member_info)
        self._last_timings.append(("필터링", (time.time() - t0) * 1000))

        # 4. LLM 생성
        t0 = time.time()
        last_request = self._get_last_user_message(chat_history)
        base_recipe  = filtered_docs[0].get("content", "")[:600] if filtered_docs else "한식 요리"
        recipe_json  = self._generate_recipe_from_base(
            base_recipe=base_recipe,
            last_request=last_request,
            member_info=member_info
        )
        self._last_timings.append(("LLM 생성", (time.time() - t0) * 1000))

        # ── title 정리 ──
        t0 = time.time()
        recipe_json['title'] = _clean_title_llm(recipe_json.get('title', ''))
        self._last_timings.append(("title 정리", (time.time() - t0) * 1000))

        # 5. 이미지
        t0 = time.time()
        best_image = self._find_image_by_title(recipe_json['title']) if recipe_json['title'] else ""
        if not best_image:
            best_image = self._get_best_image(filtered_docs)
        self._last_timings.append(("이미지 검색", (time.time() - t0) * 1000))

        # 6. 최종 구성
        t0 = time.time()
        recipe_json['image']   = best_image
        recipe_json['img_url'] = best_image
        servings = len(member_info.get('names', [])) if member_info and member_info.get('names') else 1
        if not recipe_json.get('servings'):
            recipe_json['servings'] = f"{servings}인분"
        self._last_timings.append(("최종 구성", (time.time() - t0) * 1000))

        logger.info(f"[RecipeService] 최종 레시피: {recipe_json.get('title')}")
        return recipe_json

    # ─────────────────────────────────────────────
    # 핵심: base_recipe + last_request → JSON
    # ─────────────────────────────────────────────
    def _generate_recipe_from_base(
        self,
        base_recipe: str,
        last_request: str,
        member_info: Dict
    ) -> Dict:
        servings  = len(member_info.get('names', [])) if member_info else 1
        allergies = ', '.join(member_info.get('allergies', [])) if member_info else '없음'
        dislikes  = ', '.join(member_info.get('dislikes', []))  if member_info else '없음'
        tools     = ', '.join(member_info.get('tools', []))     if member_info else '모든 도구'

        prompt = RECIPE_REFINE_PROMPT.format(
            base_recipe=base_recipe,
            last_request=last_request,
            servings=servings,
            allergies=allergies,
            dislikes=dislikes,
            tools=tools
        )

        logger.info(f"[RecipeService] 프롬프트 길이: {len(prompt)}chars")

        try:
            result = _llm_recipe.invoke(prompt)
            response_text = result.content.strip()
            response_text = re.sub(r'```json\s*|\s*```', '', response_text)
            recipe_json   = json.loads(response_text)
            logger.info(f"[RecipeService] 레시피 생성 성공: {recipe_json.get('title')}")
            return recipe_json

        except json.JSONDecodeError as e:
            logger.error(f"[RecipeService] JSON 파싱 실패: {e}")
            logger.error(f"[RecipeService] 응답: {response_text[:200]}")
            return {
                "title": "추천 레시피",
                "intro": "레시피 생성 중 오류가 발생했습니다.",
                "cook_time": "30분",
                "level": "중급",
                "servings": f"{servings}인분",
                "ingredients": [],
                "steps": [],
                "tips": []
            }
        except Exception as e:
            logger.error(f"[RecipeService] 레시피 생성 실패: {e}", exc_info=True)
            raise

    # ─────────────────────────────────────────────
    # 헬퍼
    # ─────────────────────────────────────────────
    def _get_last_user_message(self, chat_history: List[Dict]) -> str:
        for msg in reversed(chat_history):
            if msg.get('role') == 'user':
                return msg.get('content', '')
        return "레시지 생성해주세요"

    def _find_image_by_title(self, title: str) -> str:
        try:
            recipe = self.recipes_collection.find_one(
                {"title": {"$regex": title, "$options": "i"}},
                {"image": 1, "recipe_id": 1, "_id": 0}
            )
            if recipe and "image" in recipe:
                logger.info(f"[RecipeService] MongoDB 매칭: {title} → {recipe.get('recipe_id', '')}")
                return recipe["image"]

            keywords = [w for w in title.split() if len(w) > 1]
            if keywords:
                recipe = self.recipes_collection.find_one(
                    {"title": {"$regex": "|".join(keywords), "$options": "i"}},
                    {"image": 1, "recipe_id": 1, "title": 1, "_id": 0}
                )
                if recipe and "image" in recipe:
                    logger.info(f"[RecipeService] MongoDB 키워드 매칭: {title} → {recipe.get('title', '')}")
                    return recipe["image"]

            logger.info(f"[RecipeService] MongoDB 제목 검색 실패: {title}")
            return ""
        except Exception as e:
            logger.error(f"[RecipeService] MongoDB 검색 실패: {e}")
            return ""

    def _get_image_from_mongo(self, recipe_id: str) -> str:
        try:
            recipe = self.recipes_collection.find_one({"recipe_id": recipe_id}, {"image": 1, "_id": 0})
            return recipe["image"] if recipe and "image" in recipe else ""
        except Exception as e:
            logger.error(f"[RecipeService] MongoDB 이미지 조회 실패: {e}")
            return ""

    def _get_best_image(self, docs: List[Dict]) -> str:
        for doc in docs:
            recipe_id = doc.get('recipe_id', '')
            if recipe_id:
                url = self._get_image_from_mongo(recipe_id)
                if url:
                    return url
            if doc.get('image_url'):
                return doc['image_url']
        return ""

    def _extract_search_query_with_llm(self, chat_history: List[Dict], member_info: Dict) -> str:
        conversation = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history[-5:]])
        servings  = len(member_info.get('names', [])) if member_info else 1
        allergies = ', '.join(member_info.get('allergies', [])) if member_info else '없음'
        dislikes  = ', '.join(member_info.get('dislikes', []))  if member_info else '없음'

        prompt = RECIPE_QUERY_EXTRACTION_PROMPT.format(
            conversation=conversation, servings=servings,
            allergies=allergies, dislikes=dislikes
        )
        try:
            result = _llm_query.invoke(prompt)
            query  = result.content.strip()
            logger.info(f"[RecipeService] LLM 추출 쿼리: {query}")
            return query
        except Exception as e:
            logger.error(f"[RecipeService] 쿼리 추출 실패: {e}")
            return "한식 요리"

    def _filter_by_constraints(self, recipes: List[Dict], member_info: Dict) -> List[Dict]:
        if not member_info:
            return recipes[:3]
        filtered = []
        for recipe in recipes:
            content = recipe.get("content", "").lower()
            if member_info.get("allergies") and any(a.lower() in content for a in member_info["allergies"]):
                continue
            if member_info.get("dislikes") and any(d.lower() in content for d in member_info["dislikes"]):
                continue
            filtered.append(recipe)
            if len(filtered) >= 3:
                break
        return filtered if len(filtered) >= 2 else recipes[:2]
