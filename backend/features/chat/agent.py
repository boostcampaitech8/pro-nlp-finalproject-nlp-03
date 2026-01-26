# backend/features/chat/agent.py
"""
Chat Agent (LangGraph)
"""
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END


class ChatAgentState(TypedDict):
    """Agent 상태"""
    messages: List[dict]
    user_constraints: dict
    search_query: str
    retrieved_recipes: List[dict]
    filtered_recipes: List[dict]
    selected_recipe: dict
    response: str
    step: str


def create_chat_agent(rag_system):
    """Chat Agent 생성"""
    
    def understand_intent(state: ChatAgentState) -> ChatAgentState:
        """의도 파악"""
        print("[Agent] 의도 파악 중...")
        
        last_msg = state["messages"][-1] if state["messages"] else {}
        user_input = last_msg.get("content", "")
        
        state["search_query"] = user_input
        state["step"] = "understood"
        return state
    
    def search_recipes(state: ChatAgentState) -> ChatAgentState:
        """레시피 검색"""
        print("[Agent] 레시피 검색 중...")
        
        query = state["search_query"]
        
        # RAG 검색
        results = rag_system.search_recipes(query, k=5, use_rerank=False)
        
        state["retrieved_recipes"] = results
        state["step"] = "searched"
        return state
    
    def filter_by_constraints(state: ChatAgentState) -> ChatAgentState:
        """제약 조건 필터링"""
        print("[Agent] 제약 조건 필터링 중...")
        
        recipes = state["retrieved_recipes"]
        
        # 상위 3개 선택
        filtered = recipes[:3]
        
        state["filtered_recipes"] = filtered
        state["step"] = "filtered"
        return state
    
    def generate_recommendation(state: ChatAgentState) -> ChatAgentState:
        """간단 추천 생성"""
        print("[Agent] 간단 추천 생성 중...")
        
        query = state["search_query"]
        context_docs = state["filtered_recipes"]
        
        # 간단 추천 프롬프트
        simple_prompt = """당신은 한국 요리 추천 전문가입니다.

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

# 예시

오늘의 추천 요리는 김치찌개 입니다.

**재료 (2인분, 30분):**
- 신김치 2컵, 돼지고기 150g, 두부 1/2모, 대파, 양파, 고춧가루, 마늘

**조리법:**
김치와 돼지고기를 볶다가 물을 넣고 끓인 후, 두부와 양념을 넣어 마무리합니다.

**특징:**
얼큰하고 구수한 한국의 대표 찌개입니다.

{context}"""
        
        # RAG로 답변 생성
        try:
            answer = rag_system.generate_answer(
                query, 
                context_docs,
                system_prompt=simple_prompt
            )
        except Exception as e:
            print(f"[ERROR] 답변 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            answer = "죄송합니다. 레시피 추천 중 오류가 발생했습니다."
        
        state["response"] = answer
        state["step"] = "generated"
        
        # 첫 번째 레시피 정보 저장
        if context_docs:
            first_recipe = context_docs[0]
            state["selected_recipe"] = {
                "title": first_recipe.get("title", "추천 레시피"),
                "cook_time": first_recipe.get("cook_time", "N/A"),
                "level": first_recipe.get("level", "N/A"),
            }
        
        return state
    
    # 그래프 생성
    workflow = StateGraph(ChatAgentState)
    
    # 노드 추가
    workflow.add_node("understand", understand_intent)
    workflow.add_node("search", search_recipes)
    workflow.add_node("filter", filter_by_constraints)
    workflow.add_node("generate", generate_recommendation)
    
    # 엣지 추가
    workflow.set_entry_point("understand")
    workflow.add_edge("understand", "search")
    workflow.add_edge("search", "filter")
    workflow.add_edge("filter", "generate")
    workflow.add_edge("generate", END)
    
    # 컴파일 (중요!)
    compiled_agent = workflow.compile()
    
    print("[Agent] Chat Agent 생성 완료")
    return compiled_agent 