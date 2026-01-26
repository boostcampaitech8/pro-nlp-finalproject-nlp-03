# backend/features/recipe/service.py
"""
Recipe 비즈니스 로직
"""
from typing import List, Dict, Any

class RecipeService:
    def __init__(self, rag_system, recipe_db, user_profile=None):
        self.rag = rag_system
        self.db = recipe_db
        self.user_profile = user_profile or {}
    
    async def generate_recipe(
        self, 
        recipe_title: str, 
        chat_history: List[Dict[str, str]],
        member_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """상세 레시피 생성 (대화 히스토리 반영)"""
        
        print(f"[RecipeService] 레시피 생성: {recipe_title}")
        print(f"[RecipeService] 대화 개수: {len(chat_history)}")
        print(f"[RecipeService] 가족 정보: {member_info}")
        
        # 전체 대화 히스토리 출력 (디버깅)
        print(f"[RecipeService] 전체 대화 히스토리:")
        for i, msg in enumerate(chat_history):
            role = msg.get('role', '?')
            content = msg.get('content', '')
            preview = content[:80] + '...' if len(content) > 80 else content
            print(f"  [{i}] {role}: {preview}")
        
        # 1. 대화 히스토리 텍스트로 변환 (전체!)
        history_lines = []
        for msg in chat_history:  # ← 전체 대화!
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if content:
                role_name = '사용자' if role == 'user' else '어시스턴트'
                history_lines.append(f"{role_name}: {content}")
        
        history_text = "\n".join(history_lines)
        
        # 2. 인분 계산 (names 개수 기준)
        servings = len(member_info.get('names', [])) if member_info else 1
        
        # 3. 제약 조건 텍스트 생성
        constraints_parts = []
        
        if member_info:
            if member_info.get('names'):
                constraints_parts.append(f"대상: {', '.join(member_info['names'])} ({servings}인분)")
            if member_info.get('allergies'):
                constraints_parts.append(f"알레르기 (절대 포함 금지): {', '.join(member_info['allergies'])}")
            if member_info.get('dislikes'):
                constraints_parts.append(f"비선호 재료 (절대 포함 금지): {', '.join(member_info['dislikes'])}")
            if member_info.get('cooking_tools'):
                constraints_parts.append(f"사용 가능 조리도구: {', '.join(member_info['cooking_tools'])}")
        
        constraints_text = "\n".join(constraints_parts) if constraints_parts else "없음"
        
        print(f"[RecipeService] 제약 조건:\n{constraints_text}")
        print(f"[RecipeService] 대화 히스토리 길이: {len(history_text)} 글자")
        print(f"[RecipeService] 인분: {servings}인분")
        
        # 4. 레시피 검색
        print(f"[RecipeService] RAG 검색 시작...")
        retrieved_docs = self.rag.search_recipes(recipe_title, k=5, use_rerank=False)
        print(f"[RecipeService] 검색 완료: {len(retrieved_docs)}개 문서")
        
        # 5. 상세 레시피 생성
        print(f"[RecipeService] 상세 레시피 생성 중...")
        recipe_json = self.rag.generate_recipe_json(
            user_message=f"{recipe_title} 레시피를 {servings}인분 기준으로, 대화 내용을 모두 반영하여 상세하게 작성해주세요.",
            context_docs=retrieved_docs,
            constraints_text=constraints_text,
            conversation_history=history_text  # ← 전체 대화!
        )
        
        # 6. 인분 정보 추가
        if 'servings' not in recipe_json or not recipe_json['servings']:
            recipe_json['servings'] = f"{servings}인분"
        
        print(f"[RecipeService] 레시피 생성 완료: {recipe_json.get('title', 'N/A')}")
        
        # 7. DB 저장
        if self.db:
            try:
                recipe_id = self.db.save_recipe(
                    user_id=member_info.get('names', ['사용자'])[0] if member_info else '사용자',
                    recipe=recipe_json,
                    constraints=member_info or {}
                )
                print(f"[RecipeService] DB 저장 완료: ID={recipe_id}")
                recipe_json['recipe_id'] = recipe_id
            except Exception as e:
                print(f"[RecipeService] DB 저장 실패: {e}")
        
        return recipe_json
    
    def _extract_constraints(self, chat_history: List[Dict]) -> List[str]:
        """대화에서 제약 조건 추출"""
        constraints = []
        
        for msg in chat_history:
            if msg.get("role") == "user":
                content = msg.get("content", "").lower().replace(" ", "")
                
                if any(k in content for k in ["간단", "쉬운", "초보"]):
                    if "쉬운" not in constraints:
                        constraints.append("쉬운")
                
                if any(k in content for k in ["빠른", "빨리", "금방"]):
                    if "빠른" not in constraints:
                        constraints.append("빠른")
                
                if any(k in content for k in ["다이어트", "건강", "저칼로리"]):
                    if "건강한" not in constraints:
                        constraints.append("건강한")
                
                if any(k in content for k in ["매운", "매콤", "얼큰"]):
                    if "매운" not in constraints:
                        constraints.append("매운")
                
                if any(k in content for k in ["담백", "안매운", "순한"]):
                    if "순한" not in constraints:
                        constraints.append("순한")
        
        return constraints