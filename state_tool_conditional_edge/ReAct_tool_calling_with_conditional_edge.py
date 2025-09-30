from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

# State 정의
class GraphState(TypedDict):
    query: str  # human message
    tool: str   # 사용할 tool 이름
    output: str # tool의 답변

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

# Node 2-1: Weather tool 실행
def weather_tool_node(state: GraphState) -> GraphState:
    print(f"날씨 도구 실행중...")
    state["output"] = "오늘 날씨는 맑고 기온은 20도입니다."
    return state

# Node 2-2: Calculator tool 실행
def calculator_tool_node(state: GraphState) -> GraphState:
    print(f"계산기 도구 실행중...")
    state["output"] = "계산 결과: 42"
    return state

# Node 2-3: Search tool 실행
def search_tool_node(state: GraphState) -> GraphState:
    print(f"검색 도구 실행중...")
    state["output"] = "검색 결과: Python은 프로그래밍 언어입니다."
    return state

# Node 3: 결과 출력
def output_node(state: GraphState) -> GraphState:
    print(f"\n=== 최종 결과 ===")
    print(f"질문: {state['query']}")
    print(f"답변: {state['output']}")
    return state

# Conditional function: 어떤 tool node로 갈지 결정
def route_to_tool(state: GraphState) -> str:
    """선택된 tool에 따라 다음 노드를 결정"""
    tool_name = state["tool"]
    
    if tool_name == "weather":
        return "weather_tool"
    elif tool_name == "calculator":
        return "calculator_tool"
    else:
        return "search_tool"

# Graph 구성 (Conditional Edge 사용)
def create_graph_with_conditional():
    workflow = StateGraph(GraphState)
    
    # Node 추가
    workflow.add_node("select_tool", select_tool_node)
    workflow.add_node("weather_tool", weather_tool_node)
    workflow.add_node("calculator_tool", calculator_tool_node)
    workflow.add_node("search_tool", search_tool_node)
    workflow.add_node("output", output_node)
    
    # Entry point 설정
    workflow.set_entry_point("select_tool")
    
    # Conditional Edge 추가 - tool 선택에 따라 다른 노드로 분기
    workflow.add_conditional_edges(
        "select_tool",  # 시작 노드
        route_to_tool,  # 라우팅 함수
        {
            "weather_tool": "weather_tool",
            "calculator_tool": "calculator_tool",
            "search_tool": "search_tool"
        }
    )
    
    # 각 tool 노드에서 output 노드로 연결
    workflow.add_edge("weather_tool", "output")
    workflow.add_edge("calculator_tool", "output")
    workflow.add_edge("search_tool", "output")
    workflow.add_edge("output", END)
    
    return workflow.compile()

# 실행 예시
if __name__ == "__main__":
    print("="*60)
    print("1. IF/ELSE 버전 (단일 노드 내부에서 분기)")
    print("="*60)
    
    # IF/ELSE 버전을 위한 간단한 구현
    def execute_with_if_else(query: str):
        state = {"query": query, "tool": "", "output": ""}
        
        # Tool 선택
        if "날씨" in query:
            state["tool"] = "weather"
        elif "계산" in query or "더하기" in query:
            state["tool"] = "calculator"
        else:
            state["tool"] = "search"
        
        print(f"선택된 도구: {state['tool']}")
        
        # Tool 실행 (단일 노드 내에서 if/else)
        if state["tool"] == "weather":
            state["output"] = "오늘 날씨는 맑고 기온은 20도입니다."
        elif state["tool"] == "calculator":
            state["output"] = "계산 결과: 42"
        else:
            state["output"] = "검색 결과: Python은 프로그래밍 언어입니다."
        
        print(f"답변: {state['output']}\n")
    
    # IF/ELSE 테스트
    execute_with_if_else("오늘 날씨 어때?")
    
    print("="*60)
    print("2. CONDITIONAL EDGE 버전 (그래프 구조에서 분기)")
    print("="*60)
    
    # Conditional Edge Graph 생성
    app = create_graph_with_conditional()
    
    # 테스트 케이스들
    test_queries = [
        "오늘 날씨 어때?",
        "100 더하기 200은?",
        "Python이 뭐야?"
    ]
    
    for query in test_queries:
        print(f"\n입력: {query}")
        print(f"-"*40)
        
        # 초기 state
        initial_state = {
            "query": query,
            "tool": "",
            "output": ""
        }
        
        # Graph 실행
        result = app.invoke(initial_state)
        print()

print("\n" + "="*60)
print("🔍 IF/ELSE vs CONDITIONAL EDGE 차이점 분석")
print("="*60)

print("""
1. IF/ELSE (단일 노드 내부 분기)
   - ✅ 장점:
     • 단순하고 직관적
     • 성능이 빠름 (함수 호출 한 번)
     • 디버깅이 쉬움
     • 메모리 효율적
   
   - ❌ 단점:
     • 재사용성이 낮음
     • 복잡한 로직일수록 코드가 길어짐
     • 각 분기를 독립적으로 테스트하기 어려움

2. CONDITIONAL EDGE (그래프 구조 분기)
   - ✅ 장점:
     • 모듈화가 잘 되어있음 (각 tool이 독립적인 노드)
     • 재사용성이 높음
     • 시각화가 가능 (그래프 구조를 그릴 수 있음)
     • 각 노드를 독립적으로 테스트 가능
     • 복잡한 워크플로우에 유리
     • 동적으로 그래프 수정 가능
   
   - ❌ 단점:
     • 오버헤드가 있음 (노드 간 전환 비용)
     • 간단한 로직에는 과도할 수 있음
     • 초기 학습 곡선이 있음

3. 언제 무엇을 사용할까?
   - IF/ELSE: 간단한 분기, 성능이 중요한 경우, 빠른 프로토타입
   - CONDITIONAL EDGE: 복잡한 워크플로우, 재사용이 필요한 경우, 
                       시각화가 필요한 경우, 각 단계를 독립적으로
                       관리해야 하는 경우
""")
