from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from operator import add

# State 정의 (step에 add reducer 적용, history 삭제)
class State(TypedDict):
    input: str
    output: str
    step: Annotated[int, add]  # 각 노드의 반환값을 더함

# Node 함수들 - step을 1씩 반환하여 누적
def process_node(state: State) -> State:
    print(f"\n🔄 [Process Node 실행]")
    print(f"  📥 받은 State:")
    print(f"     - input: '{state['input']}'")
    print(f"     - output: '{state['output']}'")
    print(f"     - step: {state['step']}")

    # 현재 노드는 1만큼의 step을 기여
    new_state = {
        "output": "처리 완료",
        "step": 1
    }

    print(f"  📤 반환 State (step은 1을 반환하여 누적시킴):")
    print(f"     - output: '{new_state['output']}'")
    print(f"     - step: {new_state['step']}")

    return new_state

def validate_node(state: State) -> State:
    print(f"\n✅ [Validate Node 실행]")
    print(f"  📥 받은 State:")
    print(f"     - input: '{state['input']}'")
    print(f"     - output: '{state['output']}'")
    print(f"     - step: {state['step']}")

    new_state = {
        "output": "검증 완료",
        "step": 1
    }

    print(f"  📤 반환 State (step은 1을 반환하여 누적시킴):")
    print(f"     - output: '{new_state['output']}'")
    print(f"     - step: {new_state['step']}")

    return new_state

def format_node(state: State) -> State:
    print(f"\n📝 [Format Node 실행]")
    print(f"  📥 받은 State:")
    print(f"     - input: '{state['input']}'")
    print(f"     - output: '{state['output']}'")
    print(f"     - step: {state['step']}")

    new_state = {
        "output": "포맷 완료",
        "step": 1
    }

    print(f"  📤 반환 State (step은 1을 반환하여 누적시킴):")
    print(f"     - output: '{new_state['output']}'")
    print(f"     - step: {new_state['step']}")

    return new_state

# Graph 생성
workflow = StateGraph(State)

# Node 추가
workflow.add_node("process", process_node)
workflow.add_node("validate", validate_node)
workflow.add_node("format", format_node)

# Edge 정의
workflow.add_edge(START, "process")
workflow.add_edge("process", "validate")
workflow.add_edge("validate", "format")
workflow.add_edge("format", END)

# Compile
app = workflow.compile()

# 실행
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 LangGraph State Reducer 시각화 (step 누적)")
    print("=" * 60)

    # 초기 상태 (history 삭제)
    initial_state = {
        "input": "리듀서를사용해라",
        "output": "",
        "step": 0
    }

    print(f"\n📌 초기 State:")
    print(f"   - input: '{initial_state['input']}'")
    print(f"   - output: '{initial_state['output']}'")
    print(f"   - step: {initial_state['step']}")

    print("\n" + "─" * 60)
    print("실행 과정:")
    print("─" * 60)

    # 실행
    result = app.invoke(initial_state)

    # 최종 결과 (history 출력 부분 삭제)
    print("\n" + "=" * 60)
    print("🎯 최종 결과")
    print("=" * 60)
    print(f"입력: {result['input']}")
    print(f"출력: {result['output']}")
    print(f"최종 단계: {result['step']}")
    print("=" * 60)