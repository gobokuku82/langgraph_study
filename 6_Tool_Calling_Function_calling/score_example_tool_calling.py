# 필요한 라이브러리를 가져옵니다.
from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, END

# --- 1. State 재정의 (Tool Calling을 위해) ---
# Agent가 생성한 'Tool Call' 정보를 저장할 공간을 추가합니다.
class ToolCallingState(TypedDict):
    raw_input: str              # 사용자의 원본 입력
    tool_call: Optional[Dict[str, Any]] # LLM이 결정한 Tool 호출 정보
    result: str                 # 최종 실행 결과

# --- 2. "Tool" 함수들 정의 ---
# 기존의 노드 함수들을 이제 'Tool'이라고 부릅니다.
# State에서 직접 값을 읽는 대신, 인자를 받아 처리하도록 변경할 수도 있지만,
# 여기서는 State에 저장된 tool_call의 arguments를 사용합니다.

def evaluate_korean(state: ToolCallingState) -> dict:
    """'국어' 과목의 점수를 평가하는 'Tool'"""
    print("🛠️  Tool 실행: [evaluate_korean]")
    # state에 저장된 tool_call 정보에서 점수를 가져옵니다.
    score = state['tool_call']['arguments']['score']

    if score >= 80:
        return {"result": "국어 과목 통과입니다! 훌륭해요."}
    else:
        return {"result": "국어 과목은 재시험이 필요합니다."}

def evaluate_math(state: ToolCallingState) -> dict:
    """'수학' 과목의 점수를 평가하는 'Tool'"""
    print("🛠️  Tool 실행: [evaluate_math]")
    score = state['tool_call']['arguments']['score']
    
    if score >= 50:
        return {"result": "수학 과목 통과입니다! 잘했습니다."}
    else:
        return {"result": "수학 과목은 보충 학습이 필요합니다."}

# --- 3. Agent 및 라우터 함수 정의 ---

def mock_llm_agent_node(state: ToolCallingState) -> dict:
    """
    LLM의 역할을 흉내 내는 노드.
    사용자 입력을 분석하여 어떤 Tool을 호출할지 결정합니다.
    """
    print("🤖 1. Agent 노드 실행: Tool 호출을 결정합니다.")
    raw_input = state['raw_input']
    
    try:
        parts = raw_input.split()
        subject = parts[0]
        score = int(parts[1])

        tool_call = None
        if subject == "국어":
            # 국어 Tool을 호출하라고 결정
            tool_call = {
                "tool_name": "evaluate_korean",
                "arguments": {"score": score}
            }
            print(f"   - 결정: '{tool_call['tool_name']}' Tool 호출 필요")
        elif subject == "수학":
            # 수학 Tool을 호출하라고 결정
            tool_call = {
                "tool_name": "evaluate_math",
                "arguments": {"score": score}
            }
            print(f"   - 결정: '{tool_call['tool_name']}' Tool 호출 필요")
        else:
            # 지원하지 않는 과목일 경우 Tool을 호출하지 않고 바로 결과 반환
            return {"result": f"'{subject}' 과목은 지원하지 않습니다.", "tool_call": None}
        
        # 결정된 tool_call 정보를 State에 업데이트
        return {"tool_call": tool_call}

    except (IndexError, ValueError):
        # 입력 형식 오류일 경우 Tool을 호출하지 않고 바로 결과 반환
        return {"result": "입력 형식 오류입니다. '과목 점수' 형태로 입력해주세요.", "tool_call": None}


def tool_router(state: ToolCallingState) -> str:
    """Agent가 Tool 호출을 결정했는지 여부에 따라 경로를 분기합니다."""
    print("📌 2. 라우터 실행: Tool 호출 여부를 확인합니다.")
    
    if state.get("tool_call"):
        # 호출할 Tool이 있으면, 해당 Tool의 이름(경로)을 반환
        print(f"   - 경로 결정: '{state['tool_call']['tool_name']}' Tool 실행 경로로 이동")
        return state['tool_call']['tool_name']
    else:
        # 호출할 Tool이 없으면(Agent가 직접 답변을 생성한 경우), 바로 종료
        print("   - 경로 결정: Tool 호출 없음, 그래프 종료")
        return "__end__"

# --- 4. 그래프 구성 ---
workflow = StateGraph(ToolCallingState)

# 1단계: 노드들을 그래프에 추가합니다.
workflow.add_node("agent", mock_llm_agent_node)
workflow.add_node("korean_tool", evaluate_korean)
workflow.add_node("math_tool", evaluate_math)

# 2단계: 그래프의 시작점을 'agent'로 설정합니다. (가장 큰 변화)
workflow.set_entry_point("agent")

# 3단계: 조건부 엣지를 추가합니다.
# 'agent' 노드가 끝난 후, 'tool_router' 함수의 결정에 따라 다음 노드로 분기합니다.
workflow.add_conditional_edges(
    "agent",
    tool_router,
    {
        "evaluate_korean": "korean_tool", # router가 "evaluate_korean"을 반환하면 -> "korean_tool" 노드로
        "evaluate_math": "math_tool",     # router가 "evaluate_math"을 반환하면 -> "math_tool" 노드로
        "__end__": END
    }
)

# 4단계: Tool 실행이 끝난 노드들을 종료(END) 지점에 연결합니다.
workflow.add_edge("korean_tool", END)
workflow.add_edge("math_tool", END)

# 5단계: 그래프를 실행 가능한 앱으로 컴파일합니다.
app = workflow.compile()

# --- 5. 터미널에서 입력받아 실행 ---
while True:
    user_input = input("과목과 점수를 입력하세요 (예: 국어 85, 종료: exit): ")
    if user_input.lower() == 'exit':
        break

    # raw_input을 State에 담아 그래프를 실행합니다.
    final_state = app.invoke({"raw_input": user_input})
    
    # 최종 결과를 출력합니다.
    print(f"✨ 최종 결과: {final_state['result']}\n")
