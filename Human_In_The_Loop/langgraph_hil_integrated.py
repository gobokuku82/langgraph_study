"""
LangGraph Human-in-the-Loop 통합 예시
이전 개념들(Conditional Edge, Reducer)과 함께 사용하는 완전한 예시
"""

from typing import TypedDict, Annotated, List, Literal, Optional
from operator import add
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
import uuid
import json
from datetime import datetime

print("=" * 60)
print("🚀 LangGraph HIL + 이전 개념 통합 데모")
print("=" * 60)

# ========================================
# 통합 예시 1: Conditional Edge + HIL
# ========================================
print("\n### 통합 예시 1: Tool 선택 → 승인 → 실행")

class IntegratedState(TypedDict):
    messages: Annotated[List[str], add]  # 리듀서 사용
    query: str
    selected_tool: str
    tool_approved: bool
    tool_result: str
    execution_history: Annotated[List[dict], add]  # 실행 로그

def analyze_query_node(state: IntegratedState) -> dict:
    """쿼리 분석 및 도구 선택"""
    query = state["query"]
    print(f"\n📝 쿼리 분석: {query}")
    
    # 간단한 규칙 기반 도구 선택
    if "날씨" in query:
        tool = "weather_api"
    elif "뉴스" in query:
        tool = "news_api"
    elif "계산" in query:
        tool = "calculator"
    else:
        tool = "general_search"
    
    print(f"→ 선택된 도구: {tool}")
    
    return {
        "messages": [f"도구 선택: {tool}"],
        "selected_tool": tool,
        "execution_history": [{
            "step": "analyze",
            "tool": tool,
            "timestamp": datetime.now().isoformat()
        }]
    }

def approval_node(state: IntegratedState) -> Command[Literal["weather", "news", "calculator", "search", "denied"]]:
    """사용자 승인 및 라우팅"""
    print(f"\n⚠️  승인 요청")
    
    # interrupt로 사용자 승인 요청
    approval_data = interrupt({
        "type": "tool_approval",
        "tool": state["selected_tool"],
        "query": state["query"],
        "message": f"'{state['selected_tool']}'를 사용하여 '{state['query']}'를 처리하시겠습니까?",
        "options": ["approve", "deny", "change_tool"]
    })
    
    # 응답에 따른 처리
    if isinstance(approval_data, dict):
        action = approval_data.get("action", "deny")
        new_tool = approval_data.get("new_tool")
    else:
        action = approval_data
        new_tool = None
    
    # Command로 동적 라우팅 + 상태 업데이트
    if action == "approve":
        print(f"✅ 승인됨: {state['selected_tool']}")
        
        # 도구별 노드로 라우팅
        tool_node_map = {
            "weather_api": "weather",
            "news_api": "news",
            "calculator": "calculator",
            "general_search": "search"
        }
        
        return Command(
            update={
                "tool_approved": True,
                "messages": ["도구 실행 승인됨"],
                "execution_history": [{
                    "step": "approved",
                    "timestamp": datetime.now().isoformat()
                }]
            },
            goto=tool_node_map.get(state["selected_tool"], "search")
        )
    
    elif action == "change_tool" and new_tool:
        print(f"🔄 도구 변경: {state['selected_tool']} → {new_tool}")
        # 도구를 변경하고 다시 승인 노드로
        return Command(
            update={
                "selected_tool": new_tool,
                "messages": [f"도구 변경: {new_tool}"],
            },
            goto="approval"  # 재승인 요청
        )
    
    else:  # deny
        print("❌ 거절됨")
        return Command(
            update={
                "tool_approved": False,
                "messages": ["도구 실행 거절됨"],
                "execution_history": [{
                    "step": "denied",
                    "timestamp": datetime.now().isoformat()
                }]
            },
            goto="denied"
        )

# 개별 도구 노드들
def weather_node(state: IntegratedState) -> dict:
    print("🌤️ 날씨 API 실행")
    result = "맑음, 기온 22도, 습도 45%"
    return {
        "tool_result": result,
        "messages": [f"날씨 정보: {result}"]
    }

def news_node(state: IntegratedState) -> dict:
    print("📰 뉴스 API 실행")
    result = "오늘의 주요 뉴스: AI 기술 발전, 경제 동향"
    return {
        "tool_result": result,
        "messages": [f"뉴스: {result}"]
    }

def calculator_node(state: IntegratedState) -> dict:
    print("🔢 계산기 실행")
    result = "계산 결과: 42"
    return {
        "tool_result": result,
        "messages": [f"계산: {result}"]
    }

def search_node(state: IntegratedState) -> dict:
    print("🔍 일반 검색 실행")
    result = f"'{state['query']}'에 대한 검색 결과"
    return {
        "tool_result": result,
        "messages": [f"검색: {result}"]
    }

def denied_node(state: IntegratedState) -> dict:
    print("🚫 요청 거절 처리")
    return {
        "tool_result": "사용자가 도구 실행을 거절했습니다",
        "messages": ["실행 취소됨"]
    }

def result_review_node(state: IntegratedState) -> dict:
    """결과 검토 및 수정 (HIL)"""
    print("\n📊 결과 검토")
    
    if state.get("tool_result"):
        # 사용자에게 결과 검토 요청
        review_response = interrupt({
            "type": "result_review",
            "result": state["tool_result"],
            "message": "결과를 검토하시고, 수정이 필요하면 입력하세요 (OK면 그대로 진행)"
        })
        
        if review_response and review_response != "OK":
            print(f"✏️ 결과 수정: {review_response}")
            return {
                "tool_result": review_response,
                "messages": ["결과가 사용자에 의해 수정됨"]
            }
    
    return state

# 그래프 구성
workflow = StateGraph(IntegratedState)

# 노드 추가
workflow.add_node("analyze", analyze_query_node)
workflow.add_node("approval", approval_node)
workflow.add_node("weather", weather_node)
workflow.add_node("news", news_node)
workflow.add_node("calculator", calculator_node)
workflow.add_node("search", search_node)
workflow.add_node("denied", denied_node)
workflow.add_node("review", result_review_node)

# 엣지 설정
workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "approval")

# 각 도구 노드는 review로
workflow.add_edge("weather", "review")
workflow.add_edge("news", "review")
workflow.add_edge("calculator", "review")
workflow.add_edge("search", "review")
workflow.add_edge("denied", "review")

workflow.add_edge("review", END)

# 컴파일 (Checkpointer 필수!)
checkpointer = InMemorySaver()
app = workflow.compile(checkpointer=checkpointer)

# 실행 시뮬레이션
print("\n" + "="*40)
print("💬 시나리오 1: 날씨 조회 (승인)")
print("="*40)

config1 = {"configurable": {"thread_id": str(uuid.uuid4())}}
initial_state = {
    "messages": [],
    "query": "오늘 날씨 어때?",
    "selected_tool": "",
    "tool_approved": False,
    "tool_result": "",
    "execution_history": []
}

# Step 1: 분석 및 중단
result1 = app.invoke(initial_state, config1)
print(f"\n🔸 현재 상태 - 대기 중")

# Step 2: 승인으로 재개
print("\n👤 사용자: approve")
result2 = app.invoke(Command(resume="approve"), config1)

# Step 3: 결과 검토
print("\n👤 사용자: OK (결과 수정 없음)")
final = app.invoke(Command(resume="OK"), config1)

print(f"\n📋 최종 결과:")
print(f"  - 메시지 히스토리: {final['messages']}")
print(f"  - 도구 결과: {final['tool_result']}")

# ========================================
# 통합 예시 2: 복잡한 워크플로우 with 리듀서
# ========================================
print("\n" + "="*60)
print("### 통합 예시 2: 데이터 수집 → 검증 → 처리")

def create_validation_reducer(min_score: float):
    """검증 점수 리듀서 생성"""
    def reducer(current: float, new: float) -> float:
        if current is None:
            return new
        # 최소 점수 이상만 유지
        if new >= min_score:
            return max(current, new)
        return current
    return reducer

validation_reducer = create_validation_reducer(0.7)

class DataPipelineState(TypedDict):
    raw_data: List[str]
    processed_data: Annotated[List[str], add]
    validation_score: Annotated[float, validation_reducer]
    human_feedback: List[str]
    pipeline_complete: bool

def collect_data_node(state: DataPipelineState) -> dict:
    """데이터 수집 (멀티 소스)"""
    print("\n📥 데이터 수집 중...")
    
    # 여러 번 interrupt로 데이터 수집
    sources = ["source1", "source2", "source3"]
    collected = []
    
    for source in sources:
        data = interrupt(f"Enter data from {source} (or 'skip'):")
        if data and data != "skip":
            collected.append(f"{source}: {data}")
            print(f"  ✓ {source} 수집 완료")
    
    return {
        "raw_data": collected,
        "processed_data": [f"수집됨: {len(collected)}개 소스"]
    }

def validate_node(state: DataPipelineState) -> Command[Literal["process", "recollect"]]:
    """데이터 검증 with HIL"""
    print("\n🔍 데이터 검증 중...")
    
    # 자동 검증 점수 계산 (목업)
    score = 0.8 if len(state["raw_data"]) >= 2 else 0.5
    print(f"  자동 검증 점수: {score}")
    
    # 사용자 검증
    human_validation = interrupt({
        "type": "validation",
        "data": state["raw_data"],
        "auto_score": score,
        "message": "데이터를 검토하고 진행 여부를 결정하세요 (proceed/recollect/modify)"
    })
    
    if human_validation == "proceed":
        return Command(
            update={
                "validation_score": score,
                "human_feedback": ["검증 통과"],
                "processed_data": ["검증 완료"]
            },
            goto="process"
        )
    elif human_validation == "recollect":
        return Command(
            update={
                "human_feedback": ["재수집 요청"],
                "processed_data": ["검증 실패 - 재수집"]
            },
            goto="recollect"
        )
    else:  # modify
        modified_data = interrupt("수정할 데이터를 입력하세요:")
        return Command(
            update={
                "raw_data": state["raw_data"] + [modified_data],
                "validation_score": 0.9,
                "human_feedback": ["데이터 수정됨"],
                "processed_data": ["사용자 수정 적용"]
            },
            goto="process"
        )

def process_node(state: DataPipelineState) -> dict:
    """데이터 처리"""
    print("\n⚙️ 데이터 처리 중...")
    
    processed = []
    for data in state["raw_data"]:
        processed.append(f"PROCESSED_{data.upper()}")
    
    return {
        "processed_data": processed,
        "pipeline_complete": True
    }

def recollect_node(state: DataPipelineState) -> dict:
    """데이터 재수집"""
    print("\n🔄 데이터 재수집...")
    
    additional = interrupt("추가 데이터를 입력하세요:")
    
    return {
        "raw_data": state["raw_data"] + [f"additional: {additional}"],
        "processed_data": ["재수집 완료"]
    }

# 파이프라인 그래프
pipeline = StateGraph(DataPipelineState)
pipeline.add_node("collect", collect_data_node)
pipeline.add_node("validate", validate_node)
pipeline.add_node("process", process_node)
pipeline.add_node("recollect", recollect_node)

pipeline.set_entry_point("collect")
pipeline.add_edge("collect", "validate")
pipeline.add_edge("recollect", "validate")
pipeline.add_edge("process", END)

checkpointer2 = InMemorySaver()
pipeline_app = pipeline.compile(checkpointer=checkpointer2)

print("\n🚀 데이터 파이프라인 시작")
config2 = {"configurable": {"thread_id": str(uuid.uuid4())}}

# 시뮬레이션
print("\n📥 데이터 수집 단계")
pipeline_state = {
    "raw_data": [],
    "processed_data": [],
    "validation_score": 0.0,
    "human_feedback": [],
    "pipeline_complete": False
}

result = pipeline_app.invoke(pipeline_state, config2)
print("👤 Source1: data_A")
result = pipeline_app.invoke(Command(resume="data_A"), config2)
print("👤 Source2: data_B")
result = pipeline_app.invoke(Command(resume="data_B"), config2)
print("👤 Source3: skip")
result = pipeline_app.invoke(Command(resume="skip"), config2)

print("\n🔍 검증 단계")
print("👤 검증 결과: proceed")
final_result = pipeline_app.invoke(Command(resume="proceed"), config2)

print(f"\n📊 파이프라인 완료:")
print(f"  - 원본 데이터: {final_result['raw_data']}")
print(f"  - 처리된 데이터: {final_result['processed_data']}")
print(f"  - 검증 점수: {final_result['validation_score']}")

# ========================================
# 통합 예시 3: 에러 처리 및 복구
# ========================================
print("\n" + "="*60)
print("### 통합 예시 3: 에러 처리 with HIL")

class RobustState(TypedDict):
    task: str
    attempts: Annotated[List[dict], add]
    max_attempts: int
    success: bool
    error_log: Annotated[List[str], add]

def risky_operation_node(state: RobustState) -> Command[Literal["success", "error_handler"]]:
    """위험한 작업 실행"""
    print(f"\n⚡ 위험한 작업 시도: {state['task']}")
    
    attempt_num = len(state["attempts"]) + 1
    
    # 시뮬레이션: 50% 확률로 실패
    import random
    success = random.random() > 0.5
    
    if success:
        print("✅ 작업 성공!")
        return Command(
            update={
                "attempts": [{"attempt": attempt_num, "result": "success"}],
                "success": True
            },
            goto="success"
        )
    else:
        print("❌ 작업 실패!")
        
        # 최대 시도 횟수 확인
        if attempt_num >= state["max_attempts"]:
            # 사용자에게 어떻게 할지 물어봄
            user_decision = interrupt({
                "type": "error_recovery",
                "error": "Maximum attempts reached",
                "attempts": attempt_num,
                "message": "최대 시도 횟수 도달. 어떻게 하시겠습니까? (retry/skip/abort)"
            })
            
            if user_decision == "retry":
                # 시도 횟수 리셋하고 재시도
                return Command(
                    update={
                        "attempts": [],  # 리셋
                        "error_log": [f"사용자가 재시도 요청 (시도 {attempt_num}회 후)"]
                    },
                    goto="error_handler"
                )
            elif user_decision == "skip":
                return Command(
                    update={
                        "success": False,
                        "error_log": ["사용자가 작업 건너뜀"]
                    },
                    goto="success"  # 성공으로 처리
                )
            else:  # abort
                return Command(
                    update={
                        "error_log": ["사용자가 작업 중단"]
                    },
                    goto=END
                )
        
        return Command(
            update={
                "attempts": [{"attempt": attempt_num, "result": "failed"}],
                "error_log": [f"시도 {attempt_num} 실패"]
            },
            goto="error_handler"
        )

def error_handler_node(state: RobustState) -> dict:
    """에러 처리 및 재시도 준비"""
    print(f"🔧 에러 처리 중... (시도: {len(state['attempts'])}/{state['max_attempts']})")
    
    # 자동 복구 로직
    import time
    time.sleep(0.5)  # 대기
    
    return state  # 다시 risky_operation으로

def success_node(state: RobustState) -> dict:
    """성공 처리"""
    if state["success"]:
        print("🎉 작업 완료!")
    else:
        print("⚠️ 작업 건너뜀")
    
    return state

# 에러 처리 그래프
robust_workflow = StateGraph(RobustState)
robust_workflow.add_node("risky_operation", risky_operation_node)
robust_workflow.add_node("error_handler", error_handler_node)
robust_workflow.add_node("success", success_node)

robust_workflow.set_entry_point("risky_operation")
robust_workflow.add_edge("error_handler", "risky_operation")  # 재시도
robust_workflow.add_edge("success", END)

checkpointer3 = InMemorySaver()
robust_app = robust_workflow.compile(checkpointer=checkpointer3)

print("\n🚀 에러 처리 워크플로우 시작")
config3 = {"configurable": {"thread_id": str(uuid.uuid4())}}

robust_state = {
    "task": "중요한 API 호출",
    "attempts": [],
    "max_attempts": 2,
    "success": False,
    "error_log": []
}

# 실행 (실패 시나리오 시뮬레이션)
result = robust_app.invoke(robust_state, config3)

# 만약 interrupt가 발생했다면
if "__interrupt__" in result:
    print("\n👤 사용자 결정: retry")
    final = robust_app.invoke(Command(resume="retry"), config3)
    
    # 재시도 후 또 실패할 수 있음
    if "__interrupt__" in final:
        print("\n👤 사용자 최종 결정: skip")
        final = robust_app.invoke(Command(resume="skip"), config3)

print("\n" + "="*60)
print("💡 통합 예시 핵심 포인트:")
print("1. Conditional Edge + HIL = 동적이고 유연한 라우팅")
print("2. Reducer + HIL = 상태 누적과 사용자 검증 결합")
print("3. Error Handling + HIL = 복구 전략을 사용자가 결정")
print("4. Multi-interrupt = 복잡한 대화형 워크플로우")
print("5. Command의 goto/update = 강력한 제어 메커니즘")
print("="*60)
