from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

# State 정의
class GraphState(TypedDict):
    query: str  # human message
    tool: str   # 사용할 tool 이름
    output: str # tool의 답변

# Mock Tools
def weather_tool(query: str) -> str:
    return f"오늘 날씨는 맑고 기온은 20도입니다."

def calculator_tool(query: str) -> str:
    return f"계산 결과: 42"

def search_tool(query: str) -> str:
    return f"검색 결과: Python은 프로그래밍 언어입니다."

# Node 1: LLM이 tool을 선택 (Mock)
def select_tool_node(state: GraphState) -> GraphState:
    query = state["query"]
    
    # 실제로는 LLM이 선택하지만, 여기서는 간단한 규칙으로 대체
    if "날씨" in query:
        state["tool"] = "weather"
    elif "계산" in query or "더하기" in query:
        state["tool"] = "calculator"
    else:
        state["tool"] = "search"
    
    print(f"선택된 도구: {state['tool']}")
    return state

# Node 2: Tool 실행
def execute_tool_node(state: GraphState) -> GraphState:
    tool_name = state["tool"]
    query = state["query"]
    
    # if-else로 tool 실행
    if tool_name == "weather":
        result = weather_tool(query)
    elif tool_name == "calculator":
        result = calculator_tool(query)
    else:  # search
        result = search_tool(query)
    
    state["output"] = result
    return state

# Node 3: 결과 출력
def output_node(state: GraphState) -> GraphState:
    print(f"\n=== 최종 결과 ===")
    print(f"질문: {state['query']}")
    print(f"답변: {state['output']}")
    return state

# Graph 구성
def create_graph():
    workflow = StateGraph(GraphState)
    
    # Node 추가
    workflow.add_node("select_tool", select_tool_node)
    workflow.add_node("execute_tool", execute_tool_node)
    workflow.add_node("output", output_node)
    
    # Edge 추가 (순서대로 실행)
    workflow.set_entry_point("select_tool")
    workflow.add_edge("select_tool", "execute_tool")
    workflow.add_edge("execute_tool", "output")
    workflow.add_edge("output", END)
    
    return workflow.compile()

# 실행 예시
if __name__ == "__main__":
    # Graph 생성
    app = create_graph()
    
    # 테스트 케이스들
    test_queries = [
        "오늘 날씨 어때?",
        "100 더하기 200은?",
        "Python이 뭐야?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*40}")
        print(f"입력: {query}")
        print(f"{'='*40}")
        
        # 초기 state
        initial_state = {
            "query": query,
            "tool": "",
            "output": ""
        }
        
        # Graph 실행
        result = app.invoke(initial_state)
