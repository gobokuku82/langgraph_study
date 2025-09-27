from langgraph.graph import StateGraph, START, END
from typing import TypedDict

# 1. State 정의
class State(TypedDict):
    input: str
    output: str
    step: int

# 2. Node 함수 정의
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
workflow.add_edge("process", "validate")    # 직렬 연결
workflow.add_edge("validate", "format")     # 직렬 연결
workflow.add_edge("format", END)

# 6. Compile
app = workflow.compile()

# 7. Execute
def run_graph():
    result = app.invoke({"input": "테스트", "output": "", "step": 0})
    return result

print(run_graph())