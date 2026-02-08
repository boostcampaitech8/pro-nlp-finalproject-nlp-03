# backend/features/recipe/prompts.py
"""
Recipe 생성 프롬프트
"""

RECIPE_QUERY_EXTRACTION_PROMPT = """다음 대화를 분석하여 레시피 검색에 최적화된 키워드를 추출하세요.

# 대화 내용
{conversation}

# 제약 조건
- 인원: {servings}명
- 알레르기: {allergies}
- 제외: {dislikes}

# 출력 형식
요리 종류와 특징을 나타내는 3-5개의 핵심 키워드만 출력하세요.
예: "매운 찌개 김치"
예: "담백한 국물 요리"
예: "간단한 볶음"

키워드:"""


RECIPE_GENERATION_PROMPT = """당신은 전문 요리사입니다.

# 대화 내용
{conversation}

# 참고 레시피
{context}

# 임무
위 대화 내용과 사용자 요구사항을 **모두 반영**하여 상세한 레시피를 JSON으로 작성하세요.

**제약 조건 (필수!):**
- 알레르기 재료는 **절대 포함 금지**
- 제외 재료는 가능한 피하기
- 조리도구 목록에 없는 도구 필요한 레시피 제외

# 출력 형식 (JSON만, 설명 없이!)
{{
  "title": "요리명",
  "intro": "한 줄 소개 (특징과 맛 설명)",
  "cook_time": "30분",
  "level": "초급",
  "servings": "{servings}인분",
  "ingredients": [
    {{"name": "재료명", "amount": "양 (숫자+단위)", "note": "선택사항"}}
  ],
  "steps": [
    {{"no": 1, "desc": "구체적인 설명 (불 세기, 시간, 팁 포함)"}}
  ],
}}

JSON:"""


RECIPE_DETAIL_EXPANSION_PROMPT = """당신은 전문 요리사입니다.

# 기존 레시피 (채팅에서 선택된 레시피)
{recipe_content}

# 제약 조건
- 인원: {servings}명
- 사용 가능한 도구: {tools}

# 임무
위 레시피를 바탕으로 **상세한 조리 과정**을 JSON으로 작성하세요.
**중요:** 재료는 위 레시피에 있는 것만 사용하고, 알레르기/비선호 재료는 이미 제거되어 있으므로 그대로 사용하세요.

# 출력 형식 (JSON만, 설명 없이!)
{{
  "title": "요리명",
  "intro": "한 줄 소개 (특징과 맛 설명)",
  "cook_time": "30분",
  "level": "초급",
  "servings": "{servings}인분",
  "ingredients": [
    {{"name": "재료명", "amount": "양 (숫자+단위)", "note": "선택사항"}}
  ],
  "steps": [
    {{"no": 1, "desc": "구체적인 설명 (불 세기, 시간, 팁 포함)"}}
  ],
}}

JSON:"""