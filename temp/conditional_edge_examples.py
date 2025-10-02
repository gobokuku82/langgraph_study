from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from typing import Literal

# Tools
@tool
def calculate(expression: str) -> str:
    """수식을 계산합니다."""
    try:
        result = eval(expression)
        return f"결과: {result}"
    except:
        return "계산 오류"

@tool
def check_weather(city: str) -> str:
    """날씨를 확인합니다."""
    return f"{city}의 날씨는 맑음입니다."

@tool
def search_web(query: str) -> str:
    """웹을 검색합니다."""
    return f"'{query}' 검색 결과입니다."

tools = [calculate, check_weather, search_web]


# ============================================
# 예제 1: IF-ELSE 패턴
# ============================================
print("=== 예제 1: IF-ELSE (tool 호출 여부) ===\n")

def agent_ifelse(state: MessagesState):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def route_ifelse(state: MessagesState) -> Literal["tools", "end"]:
    """IF-ELSE: tool이 필요하면 tools, 아니면 end"""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    else:
        return "end"

graph_ifelse = StateGraph(MessagesState)
graph_ifelse.add_node("agent", agent_ifelse)
graph_ifelse.add_node("tools", ToolNode(tools))

graph_ifelse.add_edge(START, "agent")
graph_ifelse.add_conditional_edges("agent", route_ifelse, {"tools": "tools", "end": END})
graph_ifelse.add_edge("tools", "agent")

app_ifelse = graph_ifelse.compile()

result = app_ifelse.invoke({"messages": [HumanMessage(content="10 + 5를 계산해줘")]})
print(f"답변: {result['messages'][-1].content}\n")


# ============================================
# 예제 2: SWITCH 패턴
# ============================================
print("=== 예제 2: SWITCH (의도 분류) ===\n")

def classify_intent(state: MessagesState) -> Literal["calculate", "weather", "search", "end"]:
    """SWITCH: 사용자 의도를 분류"""
    user_message = state["messages"][0].content.lower()

    if "계산" in user_message or "+" in user_message or "-" in user_message:
        return "calculate"
    elif "날씨" in user_message:
        return "weather"
    elif "검색" in user_message:
        return "search"
    else:
        return "end"

def calculate_node(state: MessagesState):
    tool_result = calculate.invoke({"expression": "10+5"})
    return {"messages": [AIMessage(content=f"계산 완료: {tool_result}")]}

def weather_node(state: MessagesState):
    tool_result = check_weather.invoke({"city": "서울"})
    return {"messages": [AIMessage(content=tool_result)]}

def search_node(state: MessagesState):
    tool_result = search_web.invoke({"query": "LangGraph"})
    return {"messages": [AIMessage(content=tool_result)]}

def default_node(state: MessagesState):
    return {"messages": [AIMessage(content="무엇을 도와드릴까요?")]}

graph_switch = StateGraph(MessagesState)
graph_switch.add_node("calculate", calculate_node)
graph_switch.add_node("weather", weather_node)
graph_switch.add_node("search", search_node)
graph_switch.add_node("default", default_node)

graph_switch.add_conditional_edges(
    START,
    classify_intent,
    {
        "calculate": "calculate",
        "weather": "weather",
        "search": "search",
        "end": "default"
    }
)
graph_switch.add_edge("calculate", END)
graph_switch.add_edge("weather", END)
graph_switch.add_edge("search", END)
graph_switch.add_edge("default", END)

app_switch = graph_switch.compile()

for query in ["10+5 계산해줘", "서울 날씨 알려줘", "LangGraph 검색해줘"]:
    result = app_switch.invoke({"messages": [HumanMessage(content=query)]})
    print(f"질문: {query}")
    print(f"답변: {result['messages'][-1].content}\n")


# ============================================
# 예제 3: LOOP 패턴
# ============================================
print("=== 예제 3: LOOP (재시도 로직) ===\n")

from typing import TypedDict

class LoopState(TypedDict):
    messages: list
    retry_count: int
    max_retries: int

def agent_loop(state: LoopState):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def check_loop(state: LoopState) -> Literal["tools", "retry", "end"]:
    """LOOP: 실패 시 재시도, 성공 시 종료"""
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    # 응답에 "오류"가 있고 재시도 가능하면
    if "오류" in last_message.content and state["retry_count"] < state["max_retries"]:
        return "retry"

    return "end"

def retry_node(state: LoopState):
    """재시도 카운트 증가"""
    return {
        "messages": [AIMessage(content=f"재시도 중... ({state['retry_count'] + 1}회)")],
        "retry_count": state["retry_count"] + 1
    }

graph_loop = StateGraph(LoopState)
graph_loop.add_node("agent", agent_loop)
graph_loop.add_node("tools", ToolNode(tools))
graph_loop.add_node("retry", retry_node)

graph_loop.add_edge(START, "agent")
graph_loop.add_conditional_edges(
    "agent",
    check_loop,
    {"tools": "tools", "retry": "retry", "end": END}
)
graph_loop.add_edge("tools", "agent")
graph_loop.add_edge("retry", "agent")

app_loop = graph_loop.compile()

result = app_loop.invoke({
    "messages": [HumanMessage(content="서울 날씨 알려줘")],
    "retry_count": 0,
    "max_retries": 2
})

print("실행 흐름:")
for msg in result["messages"]:
    if hasattr(msg, 'content') and msg.content:
        print(f"  - {msg.content}")
print(f"총 재시도 횟수: {result['retry_count']}")