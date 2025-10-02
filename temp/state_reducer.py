from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from operator import add

# State 정의 (history 추가로 과정 추적)
class State(TypedDict):
    input: str
    output: str
    step: int
    history: Annotated[list, add]  # 실행 과정 기록

# Node 함수들 - 실행 과정을 출력
def process_node(state: State) -> State:

    new_state = {
        "output": "처리 완료",
        "step": state['step'] + 1,
        "history": [f"Step {state['step']+1}: Process 노드에서 '{state['input']}' 처리"]
    }
        
    return new_state

def validate_node(state: State) -> State:
    print(f"\n✅ [Validate Node 실행]")
    print(f"  📥 받은 State:")
    print(f"     - input: '{state['input']}'")
    print(f"     - output: '{state['output']}'")
    print(f"     - step: {state['step']}")
    
    new_state = {
        "output": "검증 완료",
        "step": state['step'] + 1,
        "history": [f"Step {state['step']+1}: Validate 노드에서 '{state['output']}' 검증"]
    }
    
    print(f"  📤 반환 State:")
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
        "step": state['step'] + 1,
        "history": [f"Step {state['step']+1}: Format 노드에서 '{state['output']}' 포맷팅"]
    }
    
    print(f"  📤 반환 State:")
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
    print("🚀 LangGraph State 전달 과정 시각화")
    print("=" * 60)
    
    # 초기 상태
    initial_state = {
        "input": "과정을더해라",
        "output": "",
        "step": 0,
        "history": []
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
    
    # 최종 결과
    print("\n" + "=" * 60)
    print("🎯 최종 결과")
    print("=" * 60)
    print(f"입력: {result['input']}")
    print(f"출력: {result['output']}")
    print(f"최종 단계: {result['step']}")
    
    print("\n📜 실행 히스토리:")
    for item in result['history']:
        print(f"  • {item}")
    print("=" * 60)
