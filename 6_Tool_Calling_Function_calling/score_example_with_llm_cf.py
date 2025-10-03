# 필요한 라이브러리를 가져옵니다.
import json
from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# --- 1. Tool 정의 (이 부분은 일반 파이썬 함수로 정의합니다) ---
# @tool 데코레이터 없이 순수한 함수로 만듭니다.
def evaluate_korean(score: int) -> str:
    """'국어' 과목의 점수를 평가할 때 사용합니다. 'score' 인자가 반드시 필요합니다."""
    print("🛠️ Tool 실행: [evaluate_korean]")
    if score >= 80:
        return "국어 과목 통과입니다! 훌륭해요."
    else:
        return "국어 과목은 재시험이 필요합니다."

def evaluate_math(score: int) -> str:
    """'수학' 과목의 점수를 평가할 때 사용합니다. 'score' 인자가 반드시 필요합니다."""
    print("🛠️ Tool 실행: [evaluate_math]")
    if score >= 50:
        return "수학 과목 통과입니다! 잘했습니다."
    else:
        return "수학 과목은 보충 학습이 필요합니다."

# --- 2. State 정의 (가장 큰 차이점) ---
# 리듀서 없이, 각 데이터를 담을 명확한 변수로 상태를 정의합니다.
class AgentState(TypedDict):
    query: str  # 사용자의 초기 질문
    tool_name: str | None  # LLM이 결정한 도구 이름
    tool_args: dict | None  # LLM이 결정한 도구 인자
    final_response: str | None  # 사용자에게 보여줄 최종 응답

# --- 3. LLM 및 Agent, 라우터 함수 정의 ---

# 일반 모델을 생성합니다.
model = ChatOpenAI(model="gpt-4o-mini")

# LLM에게 도구 사용법과 응답 형식을 직접 지시하는 시스템 프롬프트
SYSTEM_PROMPT = """
You are an assistant that evaluates student scores. You have access to the following tools:

1. `evaluate_korean`: Use this to evaluate Korean scores. It requires a `score` argument.
2. `evaluate_math`: Use this to evaluate Math scores. It requires a `score` argument.

If you decide to use a tool, you MUST respond ONLY with a JSON object in the following format.
{"tool_name": "<name_of_the_tool>", "arguments": {"<argument_name>": <value>}}

If no tool is needed or the input is invalid, just respond with a natural language message.
"""

def agent_node(state: AgentState) -> dict:
    """사용자의 query를 바탕으로 LLM을 호출하여 어떤 도구를 사용할지 결정하는 노드"""
    print(f"🤖 1. Agent: 사용자의 질문 분석 -> '{state['query']}'")
    
    # 시스템 프롬프트와 사용자 쿼리를 모델에 전달
    response = model.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=state['query'])
    ])
    
    # LLM의 텍스트 응답을 파싱
    try:
        decision = json.loads(response.content)
        print(f"   - LLM 결정 (JSON): {decision}")
        # 결정된 tool_name과 tool_args를 상태에 업데이트하기 위해 반환
        return {"tool_name": decision["tool_name"], "tool_args": decision["arguments"]}
    except json.JSONDecodeError:
        print(f"   - LLM 결정 (일반 텍스트): {response.content}")
        # 도구가 필요 없다고 판단. final_response를 상태에 업데이트하기 위해 반환
        return {"final_response": response.content}

def tool_executor_node(state: AgentState) -> dict:
    """결정된 도구를 실제로 실행하는 노드"""
    print("⚙️ 3. Tool 실행 노드 실행!")
    tool_name = state["tool_name"]
    tool_args = state["tool_args"]
    
    print(f"   - 실행할 도구: {tool_name}, 인자: {tool_args}")

    available_tools = {
        "evaluate_korean": evaluate_korean,
        "evaluate_math": evaluate_math,
    }
    
    # 이름에 맞는 함수를 찾아서 실행
    tool_to_run = available_tools[tool_name]
    output = tool_to_run(**tool_args) # **는 딕셔너리를 함수의 인자로 풀어주는 역할
    
    # 실행 결과를 final_response에 업데이트하기 위해 반환
    return {"final_response": output}

def tool_router(state: AgentState) -> str:
    """tool_name의 유무에 따라 경로를 분기합니다."""
    print("📌 2. 라우터 실행: Tool 호출 여부를 확인합니다.")
    if state.get("tool_name"):
        print("   - 결정: Tool 실행 필요. 'execute_tool'로 이동.")
        return "execute_tool"
    else:
        print("   - 결정: Tool 실행 불필요. 바로 종료.")
        return "__end__"

# --- 4. 그래프 구성 ---
workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("execute_tool", tool_executor_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    tool_router,
    {"execute_tool": "execute_tool", "__end__": END},
)
workflow.add_edge("execute_tool", END) # 도구 실행 후 바로 종료

app = workflow.compile()

# --- 5. 터미널에서 입력받아 실행 ---
while True:
    user_input = input("과목과 점수를 입력하세요 (예: 국어 85, 종료: exit): ")
    if user_input.lower() == "exit":
        break

    # 초기 상태를 query만 포함하여 설정
    initial_state = {"query": user_input}
    
    # 그래프 실행
    final_state = app.invoke(initial_state)
    
    # 최종 결과는 final_response 필드에 담겨 있음
    print(f"✨ 최종 결과: {final_state['final_response']}\n")
