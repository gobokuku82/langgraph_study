"""
실전 예시: AI 어시스턴트 with Human-in-the-Loop
실제 사용 가능한 통합 예시 - 문서 작성 어시스턴트
"""

from typing import TypedDict, Annotated, List, Dict, Optional, Literal
from operator import add
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from datetime import datetime
import json

print("=" * 60)
print("📝 AI 문서 작성 어시스턴트 (HIL 통합)")
print("=" * 60)

# ========================================
# 커스텀 리듀서 정의
# ========================================

def merge_sections_reducer(current: Dict, new: Dict) -> Dict:
    """문서 섹션 병합 리듀서"""
    if current is None:
        return new
    result = current.copy()
    result.update(new)
    return result

def quality_score_reducer(current: float, new: float) -> float:
    """품질 점수 평균 리듀서"""
    if current is None:
        return new
    return (current + new) / 2

# ========================================
# State 정의
# ========================================

class DocumentState(TypedDict):
    # 기본 정보
    topic: str
    document_type: str  # blog, report, email, proposal
    target_audience: str
    
    # 문서 컨텐츠
    outline: List[str]
    sections: Annotated[Dict[str, str], merge_sections_reducer]
    
    # 작업 히스토리
    messages: Annotated[List[str], add]
    revisions: Annotated[List[Dict], add]
    
    # 품질 관리
    quality_score: Annotated[float, quality_score_reducer]
    approved_sections: List[str]
    
    # 워크플로우 제어
    current_section: Optional[str]
    requires_research: bool
    final_approved: bool

# ========================================
# 노드 구현
# ========================================

def intake_node(state: DocumentState) -> Dict:
    """요구사항 수집"""
    print("\n📋 문서 요구사항 수집")
    
    # 문서 타입별 필요 정보 수집
    required_info = []
    
    if not state.get("topic"):
        topic = interrupt("문서 주제를 입력하세요:")
        required_info.append(("topic", topic))
    
    if not state.get("document_type"):
        doc_type = interrupt("문서 타입을 선택하세요 (blog/report/email/proposal):")
        required_info.append(("document_type", doc_type))
    
    if not state.get("target_audience"):
        audience = interrupt("대상 독자를 입력하세요:")
        required_info.append(("target_audience", audience))
    
    # 수집된 정보로 상태 업데이트
    updates = {key: value for key, value in required_info}
    updates["messages"] = [f"요구사항 수집 완료: {len(required_info)}개 항목"]
    
    print(f"✅ 수집 완료: {updates}")
    return updates

def research_decision_node(state: DocumentState) -> Command[Literal["research", "outline"]]:
    """리서치 필요성 판단"""
    print("\n🔍 리서치 필요성 분석")
    
    # 복잡한 주제인지 자동 판단 (실제로는 LLM 사용)
    complex_topics = ["기술", "과학", "경제", "정책", "분석"]
    needs_research = any(word in state["topic"].lower() for word in complex_topics)
    
    if needs_research:
        # 사용자에게 확인
        user_decision = interrupt({
            "type": "research_decision",
            "topic": state["topic"],
            "recommendation": "리서치 권장",
            "message": "이 주제는 리서치가 필요해 보입니다. 진행하시겠습니까? (yes/no)"
        })
        
        if user_decision == "yes":
            print("→ 리서치 진행")
            return Command(
                update={
                    "requires_research": True,
                    "messages": ["리서치 시작"]
                },
                goto="research"
            )
    
    print("→ 리서치 스킵")
    return Command(
        update={"requires_research": False},
        goto="outline"
    )

def research_node(state: DocumentState) -> Dict:
    """리서치 수행 (시뮬레이션)"""
    print("\n📚 리서치 수행 중...")
    
    # 여러 소스에서 정보 수집 (시뮬레이션)
    sources = ["학술 자료", "뉴스 기사", "전문가 의견"]
    research_data = []
    
    for source in sources:
        confirm = interrupt(f"{source}를 검색하시겠습니까? (yes/skip):")
        if confirm == "yes":
            # 실제로는 검색 API 호출
            research_data.append(f"{source}: 관련 정보 발견")
            print(f"  ✓ {source} 검색 완료")
    
    return {
        "messages": [f"리서치 완료: {len(research_data)}개 소스"],
        "quality_score": 0.7 if research_data else 0.5
    }

def outline_node(state: DocumentState) -> Dict:
    """아웃라인 생성"""
    print("\n📝 문서 아웃라인 생성")
    
    # 문서 타입별 기본 구조 (시뮬레이션)
    outlines = {
        "blog": ["제목", "서론", "본문1", "본문2", "결론"],
        "report": ["요약", "서론", "방법론", "결과", "논의", "결론"],
        "email": ["인사", "본문", "요청사항", "마무리"],
        "proposal": ["개요", "목표", "방법", "일정", "예산", "결론"]
    }
    
    suggested_outline = outlines.get(state["document_type"], ["서론", "본문", "결론"])
    
    # 사용자 검토 및 수정
    user_feedback = interrupt({
        "type": "outline_review",
        "suggested": suggested_outline,
        "message": "아웃라인을 검토하세요. 수정사항이 있으면 입력하세요 (OK면 진행):"
    })
    
    if user_feedback and user_feedback != "OK":
        # 사용자가 수정한 아웃라인 파싱
        if isinstance(user_feedback, list):
            suggested_outline = user_feedback
        else:
            # 간단한 파싱 (콤마 구분)
            suggested_outline = [s.strip() for s in user_feedback.split(",")]
    
    print(f"✅ 최종 아웃라인: {suggested_outline}")
    
    return {
        "outline": suggested_outline,
        "messages": [f"아웃라인 확정: {len(suggested_outline)}개 섹션"]
    }

def section_writer_node(state: DocumentState) -> Command[Literal["section_writer", "review"]]:
    """섹션별 작성"""
    print("\n✍️ 섹션 작성")
    
    # 작성되지 않은 섹션 찾기
    unwritten_sections = [
        section for section in state["outline"]
        if section not in state.get("sections", {})
    ]
    
    if not unwritten_sections:
        print("→ 모든 섹션 작성 완료")
        return Command(goto="review")
    
    # 다음 섹션 선택
    current_section = unwritten_sections[0]
    print(f"📄 현재 섹션: {current_section}")
    
    # AI 초안 생성 (시뮬레이션)
    ai_draft = f"""
    [{current_section}]
    주제: {state['topic']}
    대상: {state['target_audience']}
    
    이것은 {current_section} 섹션의 AI 생성 초안입니다.
    실제 구현에서는 LLM이 고품질 콘텐츠를 생성합니다.
    """
    
    # 사용자 검토 및 편집
    edited_content = interrupt({
        "type": "section_edit",
        "section": current_section,
        "draft": ai_draft,
        "message": f"{current_section} 섹션을 검토하고 수정하세요:"
    })
    
    if edited_content:
        final_content = edited_content if edited_content != "OK" else ai_draft
    else:
        final_content = ai_draft
    
    # 품질 점수 계산 (시뮬레이션)
    quality = 0.8 if edited_content else 0.6
    
    return Command(
        update={
            "sections": {current_section: final_content},
            "current_section": current_section,
            "quality_score": quality,
            "messages": [f"섹션 작성: {current_section}"],
            "revisions": [{
                "section": current_section,
                "timestamp": datetime.now().isoformat(),
                "edited": bool(edited_content)
            }]
        },
        goto="section_writer"  # 다음 섹션으로 계속
    )

def review_node(state: DocumentState) -> Command[Literal["section_writer", "finalize", "intake"]]:
    """전체 문서 검토"""
    print("\n📖 전체 문서 검토")
    
    # 문서 조합
    full_document = "\n\n".join([
        f"[{section}]\n{content}"
        for section, content in state["sections"].items()
    ])
    
    # 품질 점수 표시
    print(f"📊 품질 점수: {state.get('quality_score', 0):.2f}/1.0")
    
    # 사용자 최종 검토
    final_decision = interrupt({
        "type": "final_review",
        "document": full_document,
        "quality_score": state.get("quality_score", 0),
        "stats": {
            "sections": len(state["sections"]),
            "revisions": len(state.get("revisions", [])),
            "research": state.get("requires_research", False)
        },
        "message": "최종 검토: approve(승인)/revise(수정)/restart(다시 시작)"
    })
    
    if final_decision == "approve":
        print("✅ 문서 승인됨")
        return Command(
            update={
                "final_approved": True,
                "messages": ["문서 최종 승인"]
            },
            goto="finalize"
        )
    elif final_decision == "revise":
        section_to_revise = interrupt("수정할 섹션 이름을 입력하세요:")
        # 해당 섹션 삭제하고 다시 작성
        if section_to_revise in state["sections"]:
            del state["sections"][section_to_revise]
        return Command(
            update={
                "messages": [f"섹션 재작성: {section_to_revise}"]
            },
            goto="section_writer"
        )
    else:  # restart
        print("🔄 처음부터 다시 시작")
        return Command(
            update={
                "messages": ["문서 작성 재시작"],
                "sections": {},
                "outline": []
            },
            goto="intake"
        )

def finalize_node(state: DocumentState) -> Dict:
    """문서 완성 및 포맷팅"""
    print("\n🎉 문서 완성!")
    
    # 최종 포맷팅
    formatted_doc = f"""
    ========================================
    제목: {state['topic']}
    타입: {state['document_type']}
    대상: {state['target_audience']}
    품질: {state.get('quality_score', 0):.2f}/1.0
    작성일: {datetime.now().strftime('%Y-%m-%d')}
    ========================================
    
    """
    
    for section, content in state["sections"].items():
        formatted_doc += f"\n## {section}\n{content}\n"
    
    formatted_doc += f"""
    ========================================
    통계:
    - 섹션 수: {len(state['sections'])}
    - 수정 횟수: {len(state.get('revisions', []))}
    - 리서치 수행: {'예' if state.get('requires_research') else '아니오'}
    ========================================
    """
    
    print(formatted_doc)
    
    # 파일로 저장할지 확인
    save_decision = interrupt("문서를 파일로 저장하시겠습니까? (yes/no):")
    
    if save_decision == "yes":
        filename = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        print(f"💾 저장됨: {filename}")
        
        return {
            "messages": [f"문서 완성 및 저장: {filename}"]
        }
    
    return {
        "messages": ["문서 완성 (저장하지 않음)"]
    }

# ========================================
# 그래프 구성
# ========================================

def create_document_assistant():
    """문서 작성 어시스턴트 그래프 생성"""
    
    workflow = StateGraph(DocumentState)
    
    # 노드 추가
    workflow.add_node("intake", intake_node)
    workflow.add_node("research_decision", research_decision_node)
    workflow.add_node("research", research_node)
    workflow.add_node("outline", outline_node)
    workflow.add_node("section_writer", section_writer_node)
    workflow.add_node("review", review_node)
    workflow.add_node("finalize", finalize_node)
    
    # 엣지 구성
    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "research_decision")
    workflow.add_edge("research", "outline")
    workflow.add_edge("outline", "section_writer")
    workflow.add_edge("finalize", END)
    
    # 컴파일
    checkpointer = InMemorySaver()
    return workflow.compile(checkpointer=checkpointer)

# ========================================
# 실행 시뮬레이션
# ========================================

if __name__ == "__main__":
    import uuid
    
    print("\n🚀 AI 문서 작성 어시스턴트 시작")
    print("="*60)
    
    # 어시스턴트 생성
    assistant = create_document_assistant()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    # 초기 상태
    initial_state = {
        "topic": "",
        "document_type": "",
        "target_audience": "",
        "outline": [],
        "sections": {},
        "messages": [],
        "revisions": [],
        "quality_score": 0.0,
        "approved_sections": [],
        "current_section": None,
        "requires_research": False,
        "final_approved": False
    }
    
    # 시뮬레이션 실행
    print("\n📝 새 문서 작성 시작")
    print("-"*40)
    
    # Step 1: 요구사항 수집
    result = assistant.invoke(initial_state, config)
    print("👤 주제: LangGraph 소개")
    result = assistant.invoke(Command(resume="LangGraph 소개"), config)
    print("👤 타입: blog")
    result = assistant.invoke(Command(resume="blog"), config)
    print("👤 대상: 개발자")
    result = assistant.invoke(Command(resume="개발자"), config)
    
    # Step 2: 리서치 결정
    print("👤 리서치: no")
    result = assistant.invoke(Command(resume="no"), config)
    
    # Step 3: 아웃라인
    print("👤 아웃라인: OK")
    result = assistant.invoke(Command(resume="OK"), config)
    
    # Step 4: 섹션 작성 (여러 번 반복)
    sections = ["제목", "서론", "본문1", "본문2", "결론"]
    for i, section in enumerate(sections):
        print(f"👤 {section} 작성: [사용자 편집된 내용 {i+1}]")
        result = assistant.invoke(
            Command(resume=f"이것은 {section}의 편집된 내용입니다."), 
            config
        )
    
    # Step 5: 최종 검토
    print("👤 최종 검토: approve")
    result = assistant.invoke(Command(resume="approve"), config)
    
    # Step 6: 저장
    print("👤 저장: yes")
    final = assistant.invoke(Command(resume="yes"), config)
    
    print("\n" + "="*60)
    print("✅ 문서 작성 완료!")
    print(f"📊 최종 통계:")
    print(f"  - 메시지 수: {len(final['messages'])}")
    print(f"  - 섹션 수: {len(final['sections'])}")
    print(f"  - 품질 점수: {final.get('quality_score', 0):.2f}")
    print("="*60)
