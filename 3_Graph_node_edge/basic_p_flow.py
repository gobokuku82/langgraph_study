from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
import operator

# 1. State 정의: 각 병렬 브랜치의 결과를 별도로 저장하도록 State를 수정합니다.
class State(TypedDict):
    """
    워크플로우의 상태를 나타냅니다.
    - input: 초기 입력값
    - validate_output: validate 노드의 결과가 저장될 공간
    - format_output: format 노드의 결과가 저장될 공간
    - output: 최종 병합 결과가 저장될 공간
    """
    input: str
    validate_output: str
    format_output: str
    output: str

# 2. Node 함수 정의: 각 노드는 이제 State의 다른 부분을 수정합니다.
def process_node(state: State) -> State:
    """데이터를 처리하고 병렬 실행을 준비합니다."""
    print("--- 1. 처리 노드 실행 ---")
    # 실제 반환값이 없어도 State는 다음 노드로 전달됩니다.
    return {}

def validate_node(state: State) -> State:
    """'validate' 브랜치를 처리하고 결과를 'validate_output'에 저장합니다."""
    print("--- 2-A. 검증 노드 실행 ---")
    return {"validate_output": "검증 완료"}

def format_node(state: State) -> State:
    """'format' 브랜치를 처리하고 결과를 'format_output'에 저장합니다."""
    print("--- 2-B. 포맷 노드 실행 ---")
    return {"format_output": "포맷 완료"}

# Fan-in을 위한 병합 노드: 이제 두 브랜치의 결과를 실제로 합칩니다.
def merge_node(state: State) -> State:
    """두 병렬 브랜치의 결과를 병합합니다."""
    print("--- 3. 병합 노드 실행 ---")
    
    # validate와 format 노드에서 온 결과를 합칩니다.
    merged_result = f"병합 결과: [{state['validate_output']}] + [{state['format_output']}]"
    
    return {"output": merged_result}

# 3. Graph 생성
workflow = StateGraph(State)

# 4. Node 추가
workflow.add_node("process", process_node)
workflow.add_node("validate", validate_node)
workflow.add_node("format", format_node)
workflow.add_node("merge", merge_node)

# 5. Edge 정의 (Fan-out -> Fan-in)
# 'process' 노드 이후 'validate'와 'format'이 병렬로 실행됩니다.
workflow.add_edge(START, "process")
workflow.add_edge("process", "validate")
workflow.add_edge("process", "format")

# 'validate'와 'format'이 모두 끝나면 'merge' 노드가 실행됩니다.
workflow.add_edge("validate", "merge")
workflow.add_edge("format", "merge")
workflow.add_edge("merge", END)

# 6. Compile: 워크플로우를 실행 가능한 객체로 컴파일합니다.
app = workflow.compile()

# 7. 실행 및 결과 출력
if __name__ == "__main__":
    # 초기 State 설정 시, 새로 추가된 필드들도 비워둡니다.
    initial_state = {
        "input": "병렬 처리 테스트",
        "validate_output": "",
        "format_output": "",
        "output": ""
    }

    print("🚀 워크플로우 실행 시작!")
    final_result = app.invoke(initial_state)

    print("\n" + "=" * 50)
    print("🎯 최종 실행 결과")
    print("=" * 50)
    print(f"  - 입력: {final_result['input']}")
    print(f"  - 검증 브랜치 결과: {final_result['validate_output']}")
    print(f"  - 포맷 브랜치 결과: {final_result['format_output']}")
    print(f"  - 최종 병합 출력: {final_result['output']}")
    print("=" * 50)