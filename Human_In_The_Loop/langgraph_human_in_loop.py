"""
LangGraph Human-in-the-Loop 예시
버전: 0.6+ (interrupt, Command 사용)

interrupt(): 그래프 실행을 일시 중지하고 사용자 입력 대기
Command: 그래프 재개 및 제어 (resume, goto, update)
"""

from typing import TypedDict, Annotated, List, Literal
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
import uuid

print("=" * 60)
print("LangGraph Human-in-the-Loop (HIL) 기능 데모")
print("=" * 60)

# ========================================
# 예시 1: 기본 interrupt - 사용자 승인
# ========================================
print("\n### 예시 1: Tool 실행 전 사용자 승인")

class ApprovalState(TypedDict):
    query: str
    tool_to_call: str
    approved: bool
    result: str

def select_tool_node(state: ApprovalState) -> dict:
    """도구 선택 (목업)"""
    query = state["query"]
    
    if "날씨" in query:
        tool = "weather_api"
    elif "검색" in query:
        tool = "search_api"
    else:
        tool = "calculator"
    
    print(f"→ 선택된 도구: {tool}")
    return {"tool_to_call": tool}

def approval_node(state: ApprovalState) -> Command[Literal["execute_tool", "reject"]]:
    """사용자에게 승인 요청"""
    print(f"\n⚠️  승인 필요!")
    
    # interrupt로 실행 중지하고 사용자 입력 대기
    user_response = interrupt({
        "message": f"'{state['tool_to_call']}' 도구를 실행하시겠습니까?",
        "tool": state["tool_to_call"],
        "query": state["query"]
    })
    
    # Command로 다음 노드 결정
    if user_response == "yes":
        print("✅ 승인됨")
        return Command(
            update={"approved": True},
            goto="execute_tool"
        )
    else:
        print("❌ 거절됨")
        return Command(
            update={"approved": False},
            goto="reject"
        )

def execute_tool_node(state: ApprovalState) -> dict:
    """도구 실행"""
    tool = state["tool_to_call"]
    print(f"🔧 {tool} 실행 중...")
    
    # 목업 결과
    results = {
        "weather_api": "오늘 날씨: 맑음, 22도",
        "search_api": "검색 결과: Python은 프로그래밍 언어입니다",
        "calculator": "계산 결과: 42"
    }
    
    return {"result": results.get(tool, "Unknown tool")}

def reject_node(state: ApprovalState) -> dict:
    """거절 처리"""
    return {"result": "사용자가 도구 실행을 거절했습니다"}

# 그래프 구성
workflow1 = StateGraph(ApprovalState)
workflow1.add_node("select_tool", select_tool_node)
workflow1.add_node("approval", approval_node)
workflow1.add_node("execute_tool", execute_tool_node)
workflow1.add_node("reject", reject_node)

workflow1.set_entry_point("select_tool")
workflow1.add_edge("select_tool", "approval")
# approval 노드는 Command로 직접 라우팅
workflow1.add_edge("execute_tool", END)
workflow1.add_edge("reject", END)

# Checkpointer 필수!
checkpointer1 = InMemorySaver()
app1 = workflow1.compile(checkpointer=checkpointer1)

# 실행 시뮬레이션
config1 = {"configurable": {"thread_id": str(uuid.uuid4())}}
print("\n💬 질문: 오늘 날씨 알려줘")

# 첫 실행 (interrupt까지)
result1 = app1.invoke({"query": "오늘 날씨 알려줘"}, config1)
print(f"🔸 Interrupt 상태: {result1.get('__interrupt__', [])}")

# 사용자 응답으로 재개
print("\n👤 사용자 응답: yes")
final1 = app1.invoke(Command(resume="yes"), config1)
print(f"📊 최종 결과: {final1['result']}")

# ========================================
# 예시 2: State 수정 요청
# ========================================
print("\n" + "=" * 60)
print("### 예시 2: State 수정 요청 (문서 검토/수정)")

class EditState(TypedDict):
    content: str
    reviewed: bool
    edits: List[str]

def draft_node(state: EditState) -> dict:
    """초안 생성"""
    draft = "LangGraph는 에이전트를 그래프로 구성하는 프레임워크입니다."
    print(f"📝 초안 생성: {draft}")
    return {"content": draft}

def review_node(state: EditState) -> dict:
    """사용자 검토 및 수정"""
    print("\n🔍 검토 요청")
    
    # 사용자에게 현재 내용 보여주고 수정 요청
    user_edit = interrupt({
        "action": "review_and_edit",
        "current_content": state["content"],
        "instruction": "내용을 검토하고 수정사항을 입력하세요"
    })
    
    if user_edit and user_edit != "ok":
        # 수정사항 적용
        edited_content = f"{state['content']} {user_edit}"
        return {
            "content": edited_content,
            "reviewed": True,
            "edits": [user_edit]
        }
    
    return {"reviewed": True}

def finalize_node(state: EditState) -> dict:
    """최종 처리"""
    print(f"✅ 최종 문서: {state['content']}")
    if state.get("edits"):
        print(f"📌 적용된 수정사항: {state['edits']}")
    return state

workflow2 = StateGraph(EditState)
workflow2.add_node("draft", draft_node)
workflow2.add_node("review", review_node)
workflow2.add_node("finalize", finalize_node)

workflow2.set_entry_point("draft")
workflow2.add_edge("draft", "review")
workflow2.add_edge("review", "finalize")
workflow2.add_edge("finalize", END)

checkpointer2 = InMemorySaver()
app2 = workflow2.compile(checkpointer=checkpointer2)

config2 = {"configurable": {"thread_id": str(uuid.uuid4())}}
print("\n📄 문서 생성 시작")

# 첫 실행
result2 = app2.invoke({"content": "", "reviewed": False, "edits": []}, config2)

# 사용자 수정으로 재개
print("\n👤 사용자 수정: '또한 Human-in-the-Loop을 지원합니다.'")
final2 = app2.invoke(
    Command(resume="또한 Human-in-the-Loop을 지원합니다."), 
    config2
)

# ========================================
# 예시 3: 멀티턴 대화 (반복 interrupt)
# ========================================
print("\n" + "=" * 60)
print("### 예시 3: 멀티턴 대화 (정보 수집)")

class FormState(TypedDict):
    name: str
    age: int
    email: str
    complete: bool

def collect_info_node(state: FormState) -> dict:
    """단계별 정보 수집"""
    print("\n📋 정보 수집 시작")
    
    # 이름 수집
    if not state.get("name"):
        name = interrupt("이름을 입력하세요:")
        state["name"] = name
        print(f"→ 이름: {name}")
    
    # 나이 수집
    if not state.get("age"):
        age = interrupt("나이를 입력하세요:")
        state["age"] = int(age) if age.isdigit() else 0
        print(f"→ 나이: {state['age']}")
    
    # 이메일 수집
    if not state.get("email"):
        email = interrupt("이메일을 입력하세요:")
        state["email"] = email
        print(f"→ 이메일: {email}")
    
    state["complete"] = True
    return state

def summary_node(state: FormState) -> dict:
    """수집된 정보 요약"""
    print(f"""
📊 수집된 정보:
- 이름: {state['name']}
- 나이: {state['age']}
- 이메일: {state['email']}
    """)
    return state

workflow3 = StateGraph(FormState)
workflow3.add_node("collect", collect_info_node)
workflow3.add_node("summary", summary_node)

workflow3.set_entry_point("collect")
workflow3.add_edge("collect", "summary")
workflow3.add_edge("summary", END)

checkpointer3 = InMemorySaver()
app3 = workflow3.compile(checkpointer=checkpointer3)

config3 = {"configurable": {"thread_id": str(uuid.uuid4())}}
print("\n🚀 폼 입력 시작")

# 단계별 실행
initial_state = {"name": "", "age": 0, "email": "", "complete": False}

# 첫 번째 interrupt (이름)
result3_1 = app3.invoke(initial_state, config3)
print("👤 사용자: 홍길동")
result3_2 = app3.invoke(Command(resume="홍길동"), config3)

# 두 번째 interrupt (나이)
print("👤 사용자: 25")
result3_3 = app3.invoke(Command(resume="25"), config3)

# 세 번째 interrupt (이메일)
print("👤 사용자: hong@example.com")
final3 = app3.invoke(Command(resume="hong@example.com"), config3)

# ========================================
# 예시 4: Command의 고급 사용
# ========================================
print("\n" + "=" * 60)
print("### 예시 4: Command 고급 기능 (goto + update)")

class WorkflowState(TypedDict):
    stage: str
    data: str
    skip_validation: bool

def entry_node(state: WorkflowState) -> Command[Literal["validation", "processing"]]:
    """진입점 - 조건부 라우팅"""
    print(f"🎯 진입점 - 데이터: {state['data']}")
    
    # 사용자에게 검증 스킵 여부 확인
    skip = interrupt("검증을 건너뛸까요? (yes/no)")
    
    if skip == "yes":
        # goto와 update를 동시에 사용
        return Command(
            update={
                "skip_validation": True,
                "stage": "직접처리"
            },
            goto="processing"  # validation 노드 건너뜀
        )
    else:
        return Command(
            update={"stage": "검증중"},
            goto="validation"
        )

def validation_node(state: WorkflowState) -> dict:
    """데이터 검증"""
    print("✔️ 데이터 검증 중...")
    return {"stage": "검증완료"}

def processing_node(state: WorkflowState) -> dict:
    """데이터 처리"""
    if state.get("skip_validation"):
        print("⚡ 빠른 처리 모드 (검증 스킵됨)")
    else:
        print("🔄 정상 처리 모드")
    
    return {"stage": "처리완료", "data": f"처리된_{state['data']}"}

workflow4 = StateGraph(WorkflowState)
workflow4.add_node("entry", entry_node)
workflow4.add_node("validation", validation_node)
workflow4.add_node("processing", processing_node)

workflow4.set_entry_point("entry")
# entry에서 Command로 직접 라우팅
workflow4.add_edge("validation", "processing")
workflow4.add_edge("processing", END)

checkpointer4 = InMemorySaver()
app4 = workflow4.compile(checkpointer=checkpointer4)

config4 = {"configurable": {"thread_id": str(uuid.uuid4())}}
print("\n🔧 워크플로우 시작")

# 검증 스킵 시나리오
result4 = app4.invoke(
    {"stage": "시작", "data": "raw_data", "skip_validation": False}, 
    config4
)
print("👤 사용자: yes (검증 스킵)")
final4 = app4.invoke(Command(resume="yes"), config4)
print(f"📊 최종 상태: {final4}")

print("\n" + "=" * 60)
print("💡 Human-in-the-Loop 핵심 개념:")
print("1. interrupt(): 실행 중지 & 사용자 입력 대기")
print("2. Command(resume=...): 입력 전달 & 재개")
print("3. Command(goto=...): 동적 라우팅")
print("4. Command(update=...): 상태 업데이트")
print("5. Checkpointer 필수: 상태 저장/복원")
print("=" * 60)
