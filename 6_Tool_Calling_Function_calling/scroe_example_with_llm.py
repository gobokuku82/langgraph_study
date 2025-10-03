# 필요한 라이브러리를 가져옵니다.
import operator
from typing import Annotated, Sequence, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolExecutor

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# --- 1. Tool 정의 ---
# @tool 데코레이터를 사용하여 LLM이 이해할 수 있는 함수(Tool)를 정의합니다.
# 함수의 설명(docstring)은 LLM이 어떤 Tool을 선택할지 결정하는 중요한 근거가 됩니다.


@tool
def evaluate_korean(score: int) -> str:
    """'국어' 과목의 점수를 평가할 때 사용합니다. 'score' 인자가 반드시 필요합니다."""
    print("🛠️ Tool 실행: [evaluate_korean]")
    if score >= 80:
        return "국어 과목 통과입니다! 훌륭해요."
    else:
        return "국어 과목은 재시험이 필요합니다."


@tool
def evaluate_math(score: int) -> str:
    """'수학' 과목의 점수를 평가할 때 사용합니다. 'score' 인자가 반드시 필요합니다."""
    print("🛠️ Tool 실행: [evaluate_math]")
    if score >= 50:
        return "수학 과목 통과입니다! 잘했습니다."
    else:
        return "수학 과목은 보충 학습이 필요합니다."


# --- 2. State 및 Tool Executor 정의 ---
# Agent의 상태를 정의합니다. 대화 기록(messages)을 통해 상태를 관리합니다.
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


# 정의된 Tool들을 실행할 실행기를 생성합니다.
tools = [evaluate_korean, evaluate_math]
tool_executor = ToolExecutor(tools)

# --- 3. LLM 및 Agent, 라우터 함수 정의 ---

# gpt-4o-mini 모델을 사용하고, 정의된 도구들을 모델에 바인딩합니다.
# 이를 통해 LLM은 도구의 설명과 인자를 이해하고 상황에 맞게 호출할 수 있습니다.
model = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools)


def agent_node(state: AgentState) -> dict:
    """
    사용자 입력을 바탕으로 LLM을 호출하여 적절한 Tool을 결정하는 Agent 노드.
    """
    print("🤖 1. Agent: 사용자 입력을 분석하여 필요한 Tool을 결정합니다.")
    # 현재 대화 기록을 모델에 전달하여 다음 행동을 결정하게 합니다.
    response = model.invoke(state["messages"])
    # 모델의 응답을 새로운 메시지로 추가하여 상태를 업데이트합니다.
    return {"messages": [response]}


def tool_executor_node(state: AgentState) -> dict:
    """Agent가 호출하기로 결정한 Tool을 실제로 실행하는 노드"""
    print("⚙️ 3. Tool 실행 노드 실행!")
    # 마지막 메시지(AIMessage)에서 tool_calls 정보를 추출합니다.
    tool_calls = state["messages"][-1].tool_calls
    # 각 tool_call을 실행하고 결과를 리스트에 저장합니다.
    tool_messages = []
    for tool_call in tool_calls:
        output = tool_executor.invoke(tool_call)
        tool_messages.append(
            ToolMessage(content=str(output), tool_call_id=tool_call["id"])
        )
    # Tool 실행 결과를 ToolMessage 형태로 반환합니다.
    return {"messages": tool_messages}


def tool_router(state: AgentState) -> str:
    """Agent의 결정에 따라 Tool을 실행할지, 종료할지 경로를 분기합니다."""
    print("📌 2. 라우터 실행: Tool 호출 여부를 확인합니다.")
    # 마지막 메시지에 tool_calls가 있는지 확인합니다.
    if state["messages"][-1].tool_calls:
        # 호출할 Tool이 있으면 'execute_tool' 경로로 이동
        return "execute_tool"
    else:
        # 호출할 Tool이 없으면 바로 종료
        return "__end__"


# --- 4. 그래프 구성 ---
workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("execute_tool", tool_executor_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    tool_router,
    {
        "execute_tool": "execute_tool",
        "__end__": END,
    },
)
workflow.add_edge("execute_tool", "agent")  # Tool 실행 후 다시 Agent를 호출하여 결과를 사용자에게 전달

app = workflow.compile()

# --- 5. 터미널에서 입력받아 실행 ---
while True:
    user_input = input("과목과 점수를 입력하세요 (예: 국어 85, 종료: exit): ")
    if user_input.lower() == "exit":
        break

    # 사용자 입력을 HumanMessage에 담아 그래프를 실행합니다.
    initial_state = {"messages": [HumanMessage(content=user_input)]}

    # stream()을 사용하여 중간 과정을 확인할 수 있습니다.
    for event in app.stream(initial_state):
        # event에서 'agent' 또는 'execute_tool' 키를 찾아 출력합니다.
        if "agent" in event:
            print("--- Agent의 응답 ---")
            print(event["agent"]["messages"][-1])
        elif "execute_tool" in event:
            print("--- Tool 실행 결과 ---")
            print(event["execute_tool"]["messages"][-1])
        print("-" * 30)

    # 최종 결과는 마지막 메시지에 담겨 있습니다.
    final_state = app.invoke(initial_state)
    final_message = final_state["messages"][-1]
    print(f"✨ 최종 결과: {final_message.content}\n")