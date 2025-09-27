from langgraph.graph import StateGraph, START, END
from typing import TypedDict

# 1. State 정의
class State(TypedDict):
    input: str
    output: str
    step: int

# 2. Node 함수 정의 (깔끔한 버전 - 출력 없음)
def process_node(state: State) -> State:
    return {"input": state["input"], "output": "처리 완료", "step": 1}

def validate_node(state: State) -> State:
    return {"input": state["input"], "output": "검증 완료", "step": 2}

def format_node(state: State) -> State:
    return {"input": state["input"], "output": "포맷 완료", "step": 3}

# 3. Graph 생성
workflow = StateGraph(State)

# 4. Node 추가
workflow.add_node("process", process_node)
workflow.add_node("validate", validate_node)
workflow.add_node("format", format_node)

# 5. Edge 정의 (순차 실행 - Sequential)
workflow.add_edge(START, "process")
workflow.add_edge("process", "validate")
workflow.add_edge("validate", "format")
workflow.add_edge("format", END)

# 6. Compile
app = workflow.compile()

# 7. 실행 및 결과 출력
if __name__ == "__main__":
    # 초기 상태 설정
    initial_state = {"input": "시작하자", "output": "", "step": 0}
    
    # 실행
    result = app.invoke(initial_state)
    
    # 결과만 깔끔하게 출력
    print("=" * 50)
    print("🎯 실행 결과")
    print("=" * 50)
    print(f"입력: {result['input']}")
    print(f"출력: {result['output']}")
    print(f"최종 단계: {result['step']}")
    print("=" * 50)
