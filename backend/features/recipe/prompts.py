# # backend/features/recipe/prompts.py
# """
# Recipe 생성 프롬프트
# """

# RECIPE_QUERY_EXTRACTION_PROMPT = """다음 대화를 분석하여 레시피 검색에 최적화된 키워드를 추출하세요.

# # 대화 내용
# {conversation}

# # 제약 조건
# - 인원: {servings}명
# - 알레르기: {allergies}
# - 제외: {dislikes}

# # 출력 형식
# 요리 종류와 특징을 나타내는 3-5개의 핵심 키워드만 출력하세요.
# 예: "매운 찌개 김치"
# 예: "담백한 국물 요리"
# 예: "간단한 볶음"

# 키워드:"""


# RECIPE_GENERATION_PROMPT = """당신은 전문 요리사입니다.

# # 대화 내용
# {conversation}

# # 사용자 정보
# - 인원: {servings}명
# - 알레르기 (절대 포함 금지): {allergies}
# - 제외 재료: {dislikes}
# - 사용 가능 조리도구: {tools}

# # 참고 레시피
# {context}

# # 임무
# 위 대화 내용과 사용자 요구사항을 **모두 반영**하여 상세한 레시피를 JSON으로 작성하세요.

# **대화 반영 규칙:**
# - "매운 거" → 고춧가루 양 증가 (예: 2큰술 → 4큰술)
# - "덜 짜게" → 소금/간장 50% 줄이기
# - "덜 달게" → 설탕 50% 줄이기
# - "간단하게" → 단계 5개 이하로 최소화
# - "빨리" → 조리시간 30분 이내
# - 인원에 맞게 재료 양 자동 조절

# **제약 조건 (필수!):**
# - 알레르기 재료는 **절대 포함 금지**
# - 제외 재료는 가능한 피하기
# - 조리도구 목록에 없는 도구 필요한 레시피 제외

# # 출력 형식 (JSON만, 설명 없이!)
# {{
#   "title": "요리명",
#   "intro": "한 줄 소개 (특징과 맛 설명)",
#   "cook_time": "30분",
#   "level": "초급",
#   "servings": "{servings}인분",
#   "ingredients": [
#     {{"name": "재료명", "amount": "양 (숫자+단위)", "note": "선택사항"}}
#   ],
#   "steps": [
#     {{"no": 1, "desc": "구체적인 설명 (불 세기, 시간, 팁 포함)"}}
#   ],
#   "tips": ["유용한 팁1", "유용한 팁2"]
# }}

# JSON:"""

# backend/features/recipe/prompts.py
"""
Recipe 생성 프롬프트
"""

# RECIPE_QUERY_EXTRACTION_PROMPT = """다음 대화를 분석하여 레시피 검색 키워드를 추출하세요.

# # 대화
# {conversation}

# # 제약
# - 알레르기: {allergies}
# - 제외: {dislikes}

# # 출력
# 3-5개 핵심 키워드만 (예: "매운 찌개 김치")

# 키워드:"""


# RECIPE_REFINE_PROMPT = """전문 요리사입니다. 기본 레시피에 조건을 반영하여 JSON으로 출력하세요.

# # 기본 레시피
# {base_recipe}

# # 사용자 요구사항
# {last_request}

# # 제약 (필수 적용)
# - 인원: {servings}명
# - 알레르기 (포함 금지): {allergies}
# - 제외 재료: {dislikes}
# - 조리도구: {tools}

# # 조건 반영 규칙
# - "덜 맵게" → 고춧가루/고추 줄이기
# - "더 달게" → 설탕/꿀 추가
# - "간단하게" → 단계 5개 이하
# - "빨리" → 조리시간 30분 이내
# - 인원수에 맞게 재료 양 조절

# # 출력 (JSON만!)
# {{
#   "title": "요리명",
#   "intro": "한 줄 소개",
#   "cook_time": "조리시간",
#   "level": "초급/중급/고급",
#   "servings": "{servings}인분",
#   "ingredients": [{{"name": "재료명", "amount": "양", "note": "비고"}}],
#   "steps": [{{"no": 1, "desc": "단계 설명"}}],
#   "tips": ["팁"]
# }}"""
RECIPE_QUERY_EXTRACTION_PROMPT = """다음 대화에서 레시피 검색 키워드만 추출하세요.

# 대화
{conversation}

# 제약
- 알레르기: {allergies}
- 제외: {dislikes}

# 출력
핵심 키워드 3개 이내 (예: "매운 김치찌개")

키워드:"""

RECIPE_REFINE_PROMPT = """전문 요리사입니다. 기본 레시피에 조건을 반영해 JSON으로 출력하세요.

# 기본 레시피
{base_recipe}

# 사용자 요구사항
{last_request}

# 제약 (필수 적용)
- 인원: {servings}명
- 알레르기 (포함 금지): {allergies}
- 제외 재료: {dislikes}
- 조리도구: {tools}

# 조건 반영 규칙
- "덜 맵게" → 고춧가루/고추 줄이기
- "더 달게" → 설탕/꿀 추가
- "간단하게" → 단계 5개 이하
- "빨리" → 조리시간 30분 이내
- 인원수에 맞게 재료 양 조절

# 출력 (JSON만!)
{
  "title": "요리명",
  "intro": "한 줄 소개(짧게)",
  "cook_time": "조리시간",
  "level": "초급/중급/고급",
  "servings": "{servings}인분",
  "ingredients": [{"name": "재료명", "amount": "양", "note": "비고"}],
  "steps": [{"no": 1, "desc": "단계 설명"}],
  "tips": ["팁"]
}"""