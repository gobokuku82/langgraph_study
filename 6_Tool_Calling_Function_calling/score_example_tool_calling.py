# 필요한 라이브러리를 가져옵니다.
from typing import TypedDict, Annotated, Sequence, Dict, Any
import operator
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage

# --- 1. Tool 정의 ---
# @tool 데코레이터를 사용하여 LLM이 이해할 수 있는 함수(Tool)를 정의합니다.
# 함수의 설명(docstring)은 LLM이 어떤 Tool을 선택할지 결정하는 중요한 근거가 됩니다.

@tool
def evaluate_korean(score: int) -> str:
    """'국어' 과목의 점수를 평가할 때 사용합니다. 'score' 인자가 반드시 필요합니다."""
    print("🛠️  Tool 실행: [evaluate_korean]")
    if score >= 80:
        return "국어 과목 통과입니다! 훌륭해요."
    else:
        return "국어 과목은 재시험이 필요합니다."

@tool
def evaluate_math(score: int) -> str:
    """'수학' 과목의 점수를 평가할 때 사용합니다. 'score' 인자가 반드시 필요합니다."""
    print("🛠️  Tool 실행: [evaluate_math]")
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

# --- 3. Agent 및 라우터 함수 정의 ---

def agent_node(state: AgentState) -> dict:
    """
    사용자 입력을 바탕으로 시스템 프롬프트에 따라 적절한 Tool을 결정하는 Agent 노드.
    """
    
    SYSTEM_PROMPT = """
    You are an assistant that evaluates student scores. Based on the user's input, 
    you must select the correct tool ('evaluate_korean' or 'evaluate_math') 
    to evaluate the score for the given subject.
    """
    
    # 당신은 학생들의 점수를 평가하는 어시스턴트입니다. 
    # 사용자의 입력을 바탕으로, 주어진 과목의 점수를 평가하기 위해 올바른 도구
    # ('evaluate_korean' 또는 'evaluate_math')를 반드시 선택해야 합니다.

    print("🤖 1. Agent: 사용자 입력을 분석하여 필요한 Tool을 결정합니다.")
    last_message = state['messages'][-1]
    raw_input = last_message.content
    
    try:
        parts = raw_input.split()
        subject = parts[0]
        score = int(parts[1])

        tool_to_call = None
        if subject == "국어":
            # 시스템 프롬프트와 Tool 설명을 바탕으로 'evaluate_korean'을 선택했다고 가정
            print(f"   - 분석: 입력된 과목 '{subject}'는 'evaluate_korean' Tool의 설명과 일치합니다.")
            tool_to_call = ToolMessage(
                tool_call_id="1", 
                name="evaluate_korean", 
                content="", 
                additional_kwargs={"arguments": {"score": score}}
            )
        elif subject == "수학":
            # 시스템 프롬프트와 Tool 설명을 바탕으로 'evaluate_math'를 선택했다고 가정
            print(f"   - 분석: 입력된 과목 '{subject}'는 'evaluate_math' Tool의 설명과 일치합니다.")
            tool_to_call = ToolMessage(
                tool_call_id="1", 
                name="evaluate_math", 
                content="", 
                additional_kwargs={"arguments": {"score": score}}
            )
        
        if tool_to_call:
            # Tool 호출이 필요하다고 판단되면 AIMessage에 tool_calls 정보를 담아 반환
            return {"messages": [AIMessage(content="", tool_calls=[tool_to_call])]}
        else:
            # 적절한 Tool이 없다고 판단되면 일반 메시지 반환
            return {"messages": [AIMessage(content=f"'{subject}' 과목은 지원하지 않습니다.")]}

    except (IndexError, ValueError):
        # 입력 형식 오류일 경우 일반 메시지 반환
        return {"messages": [AIMessage(content="입력 형식 오류입니다. '과목 점수' 형태로 입력해주세요.")]}


def tool_executor_node(state: AgentState) -> dict:
    """Agent가 호출하기로 결정한 Tool을 실제로 실행하는 노드"""
    print("⚙️ 3. Tool 실행 노드 실행!")
    last_message = state['messages'][-1]
    tool_call = last_message.tool_calls[0]
    
    # ToolExecutor를 사용하여 이름에 맞는 Tool을 실행
    output = tool_executor.invoke(tool_call)
    
    # Tool 실행 결과를 ToolMessage 형태로 반환
    return {"messages": [ToolMessage(content=str(output), tool_call_id=tool_call.id)]}


def tool_router(state: AgentState) -> str:
    """Agent의 결정에 따라 Tool을 실행할지, 종료할지 경로를 분기합니다."""
    print("📌 2. 라우터 실행: Tool 호출 여부를 확인합니다.")
    last_message = state['messages'][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
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
        "__end__": END
    }
)
workflow.add_edge("execute_tool", END)

app = workflow.compile()

# --- 5. 터미널에서 입력받아 실행 ---
while True:
    user_input = input("과목과 점수를 입력하세요 (예: 국어 85, 종료: exit): ")
    if user_input.lower() == 'exit':
        break

    # 사용자 입력을 HumanMessage에 담아 그래프를 실행합니다.
    initial_state = {"messages": [HumanMessage(content=user_input)]}
    final_state = app.invoke(initial_state)
    
    # 최종 결과는 마지막 메시지에 담겨 있습니다.
    final_message = final_state['messages'][-1]
    
    # ToolMessage의 content 또는 AIMessage의 content를 최종 결과로 사용합니다.
    print(f"✨ 최종 결과: {final_message.content}\n")

