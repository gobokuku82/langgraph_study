from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

# Tools 정의
@tool
def add(a: int, b: int) -> int:
    """두 숫자를 더합니다."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """두 숫자를 곱합니다."""
    return a * b

@tool
def search_db(query: str) -> str:
    """데이터베이스에서 정보를 검색합니다."""
    db = {
        "사용자1": "김철수, 나이: 30세",
        "사용자2": "이영희, 나이: 25세"
    }
    return db.get(query, "정보 없음")

tools = [add, multiply, search_db]


# Agent 노드 (context에서 LLM 가져옴)
def agent(state: MessagesState):
    """LLM이 다음 행동을 결정"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# 라우팅 함수
def should_continue(state: MessagesState):
    """tool 호출이 필요한지 판단"""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


# 그래프 구성
graph = StateGraph(MessagesState)

graph.add_node("agent", agent)
graph.add_node("tools", ToolNode(tools))

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, ["tools", END])
graph.add_edge("tools", "agent")

app = graph.compile()


# 케이스 1: 단순 계산
print("=== 케이스 1: 단순 tool 호출 ===")
result = app.invoke({
    "messages": [HumanMessage(content="5 더하기 3은?")]
})
print(result["messages"][-1].content)


# 케이스 2: 다중 tool 사용
print("\n=== 케이스 2: 여러 tool 순차 실행 ===")
result = app.invoke({
    "messages": [HumanMessage(content="10 더하기 5를 계산하고, 그 결과에 2를 곱해줘")]
})
for msg in result["messages"]:
    if hasattr(msg, 'content') and msg.content:
        print(f"- {msg.content}")


# 케이스 3: DB 검색
print("\n=== 케이스 3: 데이터 검색 ===")
result = app.invoke({
    "messages": [HumanMessage(content="사용자1의 정보를 알려줘")]
})
print(result["messages"][-1].content)


# 케이스 4: 복잡한 multi-step
print("\n=== 케이스 4: 복잡한 multi-step 작업 ===")
result = app.invoke({
    "messages": [
        HumanMessage(content="3 곱하기 4를 계산하고, 그 결과에 10을 더한 다음, 사용자2 정보도 알려줘")
    ]
})
print(result["messages"][-1].content)


# 케이스 5: 스트리밍으로 중간 과정 확인
print("\n=== 케이스 5: 스트리밍 실행 ===")
for event in app.stream({
    "messages": [HumanMessage(content="7 더하기 8을 계산하고 2를 곱해줘")]
}):
    for node_name, node_state in event.items():
        print(f"[{node_name}]")
        if "messages" in node_state:
            last_msg = node_state["messages"][-1]
            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                print(f"  Tool 호출: {last_msg.tool_calls}")
            elif hasattr(last_msg, 'content'):
                print(f"  내용: {last_msg.content}")


# 케이스 6: 시스템 메시지로 제약 추가
print("\n=== 케이스 6: 시스템 프롬프트로 동작 제어 ===")
result = app.invoke({
    "messages": [
        SystemMessage(content="당신은 계산 결과를 항상 한글로 자세히 설명해야 합니다."),
        HumanMessage(content="100 곱하기 5는?")
    ]
})
print(result["messages"][-1].content)