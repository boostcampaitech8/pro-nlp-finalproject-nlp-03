# backend/features/chat/agent.py
"""
Chat Agent - Adaptive RAG (네이버 검색 API 사용)
"""
from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, END
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

# prompts.py에서 프롬프트 import
from .prompts import REWRITE_PROMPT, GRADE_PROMPT, GENERATE_PROMPT


class ChatAgentState(TypedDict):
    """Agent 상태"""
    question: str               # 현재 질문 (재작성된)
    original_question: str      # 원래 질문
    chat_history: List[str]     # 대화 기록
    documents: List[Document]   # 검색된 문서
    generation: str             # 최종 답변
    web_search_needed: str      # "yes" or "no"
    user_constraints: dict
    constraint_warning: str


def create_chat_agent(rag_system):
    """Chat Agent 생성 - Adaptive RAG + 네이버 검색"""
    
    # ===== 노드 함수 =====
    
    def rewrite_query(state: ChatAgentState) -> ChatAgentState:
        """1. 쿼리 재작성"""
        print("[Agent] 1. 쿼리 재작성 중...")
        
        question = state["question"]
        history = state.get("chat_history", [])
        
        formatted_history = "\n".join(history[-5:]) if isinstance(history, list) else str(history)
        
        try:
            chain = REWRITE_PROMPT | rag_system.chat_model | StrOutputParser()
            better_question = chain.invoke({
                "history": formatted_history,
                "question": question
            })
            
            print(f"   원본: {question}")
            print(f"   재작성: {better_question}")
            
            return {
                "question": better_question,
                "original_question": question
            }
            
        except Exception as e:
            print(f"   재작성 실패: {e}")
            return {
                "question": question,
                "original_question": question
            }
    
    def retrieve(state: ChatAgentState) -> ChatAgentState:
        """2. RAG 검색 (Reranker 사용)"""
        print("[Agent] 2. RAG 검색 중...")
        
        question = state["question"]
        
        results = rag_system.search_recipes(question, k=5, use_rerank=True)
        
        documents = [
            Document(
                page_content=doc.get("content", ""),
                metadata={
                    "title": doc.get("title", ""),
                    "cook_time": doc.get("cook_time", ""),
                    "level": doc.get("level", "")
                }
            )
            for doc in results
        ]
        
        print(f"   검색 결과: {len(documents)}개")
        for i, doc in enumerate(documents[:3], 1):
            print(f"   {i}. {doc.metadata.get('title', '')[:40]}...")
        
        return {"documents": documents}
    
    def check_constraints(state: ChatAgentState) -> ChatAgentState:
            """2.5. 제약 조건 체크 (알레르기, 비선호 음식)"""
            print("[Agent] 2.5. 제약 조건 체크 중...")
            
            question = state["question"]
            history = state.get("chat_history", [])
            
            # WebSocket으로 전달된 사용자 제약사항 가져오기
            # (router.py에서 chat_sessions에 저장된 정보)
            # 일단 state에 없으면 스킵
            user_constraints = state.get("user_constraints", {})
            
            if not user_constraints:
                print("   제약 조건 없음 → 스킵")
                return {"constraint_warning": ""}
            
            dislikes = user_constraints.get("dislikes", [])
            allergies = user_constraints.get("allergies", [])
            
            # 질문에 비선호 재료가 포함되어 있는지 확인
            question_lower = question.lower()
            
            warning_parts = []

            for allergy in allergies:
                if allergy.lower() in question_lower:
                    warning_parts.append(f"**{allergy}**는 알레르기 재료입니다!")
            
            for dislike in dislikes:
                if dislike.lower() in question_lower:
                    warning_parts.append(f"**{dislike}**는 싫어하는 음식입니다.")
        
            if warning_parts:
                warning_msg = "\n".join(warning_parts)
                print(f"   제약 조건 위반 감지!")
                print(f"   {warning_msg}")
                return {"constraint_warning": warning_msg}
            else:
                print("   제약 조건 통과")
                return {"constraint_warning": ""}

    def grade_documents(state: ChatAgentState) -> ChatAgentState:
        """3. 문서 관련성 평가 (엄격하게)"""
        print("[Agent] 3. 관련성 평가 중...")
        
        question = state["question"]
        documents = state["documents"]
        
        if not documents:
            print("   문서 없음 → 웹 검색")
            return {"web_search_needed": "yes"}
        
        try:
            # 정확한 매칭 확인
            question_lower = question.lower()
            
            # 문서 제목에서 핵심 키워드 확인
            found_exact_match = False
            for doc in documents[:3]:
                title = doc.metadata.get("title", "").lower()
                # 질문의 핵심 단어가 제목에 있는지
                if question_lower in title or any(
                    word in title 
                    for word in question_lower.split() 
                    if len(word) > 1
                ):
                    found_exact_match = True
                    break
            
            if not found_exact_match:
                print("   제목 매칭 실패 → 웹 검색")
                return {"web_search_needed": "yes"}
            
            # LLM으로 2차 검증
            context_text = "\n".join([
                f"- {doc.page_content[:200]}"
                for doc in documents[:3]
            ])
            
            chain = GRADE_PROMPT | rag_system.chat_model | StrOutputParser()
            score = chain.invoke({
                "question": question,
                "context": context_text
            })
            
            print(f"   평가: {score}")
            
            if "yes" in score.lower():
                print("   DB 충분 → 생성")
                return {"web_search_needed": "no"}
            else:
                print("   DB 부족 → 웹 검색")
                return {"web_search_needed": "yes"}
                
        except Exception as e:
            print(f"   평가 실패: {e}")
            # 에러 시 웹 검색으로 (안전하게)
            return {"web_search_needed": "yes"}
    
    def web_search(state: ChatAgentState) -> ChatAgentState:
        """4. 네이버 검색 API (블로그)"""
        print("[Agent] 4. 네이버 검색 API 실행 중...")
        
        question = state["question"]
        
        try:
            import os
            import requests
            
            client_id = os.getenv("NAVER_CLIENT_ID")
            client_secret = os.getenv("NAVER_CLIENT_SECRET")
            
            if not client_id or not client_secret:
                print("   네이버 API 키 없음")
                return {
                    "documents": [Document(
                        page_content="웹 검색을 위해 네이버 API 키가 필요합니다.",
                        metadata={"source": "config_error"}
                    )]
                }
            
            url = "https://openapi.naver.com/v1/search/blog.json"
            headers = {
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret
            }
            params = {
                "query": f"{question} 레시피 재료",
                "display": 10,
                "sort": "sim"
            }
            
            print(f"   검색 쿼리: {params['query']}")
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                print(f"   검색 성공: {len(items)}개")
                
                if items:
                    def clean_html(text):
                        import re
                        text = re.sub('<[^<]+?>', '', text)
                        text = text.replace('&quot;', '"')
                        text = text.replace('&apos;', "'")
                        text = text.replace('&amp;', '&')
                        text = text.replace('&lt;', '<')
                        text = text.replace('&gt;', '>')
                        return text
                    
                    # 검색 결과 상세 로깅
                    web_content_parts = []
                    for i, item in enumerate(items[:5], 1):
                        title = clean_html(item.get('title', ''))
                        description = clean_html(item.get('description', ''))
                        link = item.get('link', '')
                        
                        print(f"\n   [검색 결과 {i}]")
                        print(f"   제목: {title}")
                        print(f"   내용: {description}...")
                        print(f"   링크: {link}")
                        
                        web_content_parts.append(
                            f"[검색 결과 {i}]\n제목: {title}\n\n상세 내용:\n{description}\n\n링크: {link}"
                        )
                    
                    web_content = "\n\n".join(web_content_parts)
                    
                    # 전체 내용도 출력 (파일로 저장 가능)
                    print(f"\n   전체 검색 결과 ({len(web_content)}자):")
                    print("="*80)
                    print(web_content)
                    print("="*80 + "\n")
                    
                    return {
                        "documents": [Document(
                            page_content=web_content,
                            metadata={"source": "naver_blog_api"}
                        )]
                    }
                else:
                    print("   검색 결과 없음")
                    return {
                        "documents": [Document(
                            page_content=f"'{question}'에 대한 검색 결과가 없습니다.",
                            metadata={"source": "naver_blog_empty"}
                        )]
                    }
            
            elif response.status_code == 429:
                print("   API 호출 제한 초과")
                return {
                    "documents": [Document(
                        page_content="API 호출 제한을 초과했습니다. 잠시 후 다시 시도해주세요.",
                        metadata={"source": "rate_limit"}
                    )]
                }
            
            else:
                print(f"   API 에러: {response.status_code}")
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('errorMessage', '알 수 없는 오류')
                print(f"   에러 내용: {error_msg}")
                
                return {
                    "documents": [Document(
                        page_content=f"검색 중 오류가 발생했습니다: {error_msg}",
                        metadata={"source": "api_error"}
                    )]
                }
        
        except requests.Timeout:
            print("   ⏱️ 검색 타임아웃")
            return {
                "documents": [Document(
                    page_content="검색 시간이 초과되었습니다. 다시 시도해주세요.",
                    metadata={"source": "timeout"}
                )]
            }
        
        except Exception as e:
            print(f"   검색 실패: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "documents": [Document(
                    page_content=f"웹 검색 중 오류가 발생했습니다: {str(e)}",
                    metadata={"source": "exception"}
                )]
            }
    
    def generate(state: ChatAgentState) -> ChatAgentState:
        """5. 답변 생성 (대화 히스토리 반영)"""
        print("[Agent] 5. 답변 생성 중...")
        
        question = state["original_question"]
        documents = state["documents"]
        history = state.get("chat_history", [])
        constraint_warning = state.get("constraint_warning", "")
        user_constraints = state.get("user_constraints", {})
        
        # 히스토리 포맷
        formatted_history = "\n".join(history[-10:]) if isinstance(history, list) else str(history)
        
        # 문서 결합
        context_text = "\n\n".join([
            doc.page_content[:800]
            for doc in documents
        ])
        
        #  제약 조건 경고가 있으면 먼저 표시
        if constraint_warning:
            # 경고 + 대체 제안
            try:
                # 대체 재료 제안 프롬프트
                alt_prompt = f"""{constraint_warning}

그래도 레시피를 원하시나요? 
아니면 비슷한 다른 재료로 대체할까요?

예: "가지 → 호박", "땅콩 → 아몬드"

답변:"""
                
                from langchain_core.messages import HumanMessage
                result = rag_system.chat_model.invoke([HumanMessage(content=alt_prompt)])
                answer = f"{constraint_warning}\n\n{result.content.strip()}"
                
                print(f"   제약 조건 경고 포함 생성 완료")
                return {"generation": answer}
                
            except Exception as e:
                print(f"   경고 생성 실패: {e}")
                # Fallback
                return {"generation": f"{constraint_warning}\n\n다른 요리를 추천해드릴까요?"}
        
        try:
            # 제약 조건을 컨텍스트에 명시
            if user_constraints:
                allergies = user_constraints.get("allergies", [])
                dislikes = user_constraints.get("dislikes", [])
                
                constraints_text = ""
                if allergies:
                    constraints_text += f"\n알레르기 재료 (절대 사용 금지): {', '.join(allergies)}"
                if dislikes:
                    constraints_text += f"\n비선호 음식 (피해야 함): {', '.join(dislikes)}"
                
                # 강화된 컨텍스트
                enhanced_context = f"""{constraints_text}

{context_text}"""
            else:
                enhanced_context = context_text
            
            chain = GENERATE_PROMPT | rag_system.chat_model | StrOutputParser()
            answer = chain.invoke({
                "context": enhanced_context,
                "question": question,
                "history": formatted_history
            })
            
            # 3단계: 생성 후 재료 체크
            if user_constraints:
                allergies = user_constraints.get("allergies", [])
                dislikes = user_constraints.get("dislikes", [])
                
                answer_lower = answer.lower()
                found_issues = []
                
                # 알레르기 재료 체크
                for allergy in allergies:
                    if allergy.lower() in answer_lower:
                        found_issues.append(f"**{allergy}** (알레르기)")
                
                # 비선호 음식 체크
                for dislike in dislikes:
                    if dislike.lower() in answer_lower:
                        found_issues.append(f"**{dislike}** (싫어함)")
                
                if found_issues:
                    print(f"   생성된 레시피에 문제 발견: {found_issues}")
                    
                    # 경고 추가
                    issues_text = ", ".join(found_issues)
                    warning = f"\n\n---\n**주의**: 이 레시피에 {issues_text}가 포함되어 있습니다!\n다른 재료로 대체하거나 다른 레시피를 추천해드릴까요?"
                    
                    answer = answer + warning
            
            print(f"   생성 완료: {answer[:50]}...")
            return {"generation": answer}
            
        except Exception as e:
            print(f"   생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"generation": "답변 생성에 실패했습니다."}
    
    # ===== 그래프 구성 =====
    
    def decide_to_generate(state: ChatAgentState) -> Literal["web_search", "generate"]:
        if state.get("web_search_needed") == "yes":
            return "web_search"
        else:
            return "generate"
    
    workflow = StateGraph(ChatAgentState)
    
    workflow.add_node("rewrite", rewrite_query)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("check_constraints", check_constraints)
    workflow.add_node("grade", grade_documents)
    workflow.add_node("web_search", web_search)
    workflow.add_node("generate", generate)
    
    workflow.set_entry_point("rewrite")
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("retrieve", "check_constraints")
    workflow.add_edge("check_constraints", "grade")
    workflow.add_conditional_edges(
        "grade",
        decide_to_generate,
        {
            "web_search": "web_search",
            "generate": "generate"
        }
    )
    workflow.add_edge("web_search", "generate")
    workflow.add_edge("generate", END)
    
    compiled = workflow.compile()
    
    print("[Agent] Adaptive RAG Agent 생성 완료 (네이버 검색 API)")
    return compiled