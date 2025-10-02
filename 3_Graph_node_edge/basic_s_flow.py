from langgraph.graph import StateGraph, START, END
from typing import TypedDict

# 1. State 정의: 워크플로우 전체에서 공유될 데이터 구조를 정의합니다.
class State(TypedDict):
    """
    워크플로우의 상태를 나타냅니다.
    - input: 초기 입력값
    - output: 각 노드를 거치며 업데이트될 결과값
    - step: 현재 진행 단계를 표시
    """
    input: str
    output: str
    step: int

# 2. Node 함수 정의: 그래프의 각 단계를 수행할 함수들을 정의합니다.
def process_node(state: State) -> State:
    """첫 번째 단계: 데이터를 처리합니다."""
    print("--- 1. 처리 노드 실행 ---")
    return {"output": "처리 완료", "step": 1}

def validate_node(state: State) -> State:
    """두 번째 단계: 처리된 데이터를 검증합니다."""
    print("--- 2. 검증 노드 실행 ---")
    return {"output": "검증 완료", "step": 2}

def format_node(state: State) -> State:
    """세 번째 단계: 최종 결과를 포맷팅합니다."""
    print("--- 3. 포맷 노드 실행 ---")
    return {"output": "포맷 완료", "step": 3}

# 3. Graph 생성: StateGraph 객체를 생성하고 상태(State)를 정의합니다.
workflow = StateGraph(State)

# 4. Node 추가: 그래프에 각 노드를 이름과 함께 추가합니다.
workflow.add_node("process", process_node)
workflow.add_node("validate", validate_node)
workflow.add_node("format", format_node)

# 5. Edge 정의: 노드 간의 실행 순서를 정의합니다.
workflow.add_edge(START, "process")       # 시작하면 process 노드로 이동
workflow.add_edge("process", "validate")  # process가 끝나면 validate 노드로 이동
workflow.add_edge("validate", "format")   # validate가 끝나면 format 노드로 이동
workflow.add_edge("format", END)          # format이 끝나면 종료

# 6. Compile: 워크플로우를 실행 가능한 객체로 컴파일합니다.
app = workflow.compile()

# 7. 실행 및 결과 출력
# 이 스크립트 파일이 직접 실행될 때만 아래 코드를 실행합니다.
if __name__ == "__main__":
    # 워크플로우를 시작할 초기 상태를 설정합니다.
    initial_state = {"input": "순차 실행 테스트", "output": "", "step": 0}

    # 워크플로우를 실행하고 최종 상태를 반환받습니다.
    # .stream()을 사용하면 각 단계별 State 변화를 모두 확인할 수 있습니다.
    print("🚀 워크플로우 실행 시작!")
    final_result = app.invoke(initial_state)

    # 최종 결과만 깔끔하게 출력합니다.
    print("\n" + "=" * 50)
    print("🎯 최종 실행 결과")
    print("=" * 50)
    print(f"  - 입력: {final_result['input']}")
    print(f"  - 최종 출력: {final_result['output']}")
    print(f"  - 최종 단계: {final_result['step']}")
    print("=" * 50)