# 필요한 라이브러리를 가져옵니다.
from typing import TypedDict
from langgraph.graph import StateGraph, END

# --- 1. State 정의 ---
# 그래프 전체에서 공유될 데이터의 형태를 정의합니다.
class GradeReportState(TypedDict):
    raw_input: str  # 사용자의 원본 입력 (예: "국어 85")
    subject: str    # 분석된 과목명
    score: int      # 분석된 점수
    result: str     # 최종 평가 결과

# --- 2. Node 함수들 정의 ---

def input_parser_node(state: GradeReportState) -> dict:
    """사용자 입력을 '과목'과 '점수'로 분리하는 노드"""
    print("🧠 1. 입력 분석 노드 실행!")
    raw_input = state['raw_input']
    
    try:
        # 공백을 기준으로 입력을 분리합니다.
        parts = raw_input.split()
        subject = parts[0]
        score = int(parts[1])
        print(f"   - 분석 완료: 과목='{subject}', 점수={score}")
        return {"subject": subject, "score": score}
    except (IndexError, ValueError):
        # "국어 85" 형식이 아닐 경우 에러 처리
        return {"subject": "error", "result": "입력 형식 오류입니다. '과목 점수' 형태로 입력해주세요."}

def evaluate_korean_node(state: GradeReportState) -> dict:
    """'국어' 과목의 점수를 평가하는 노드"""
    print("✍️ 3. 국어 점수 평가 노드 실행!")
    score = state['score']
    
    # 과목별로 다른 평가 기준을 적용 (if/else)
    if score >= 80:
        return {"result": "국어 과목 통과입니다! 훌륭해요."}
    else:
        return {"result": "국어 과목은 재시험이 필요합니다."}

def evaluate_math_node(state: GradeReportState) -> dict:
    """'수학' 과목의 점수를 평가하는 노드"""
    print("🧮 3. 수학 점수 평가 노드 실행!")
    score = state['score']

    # 과목별로 다른 평가 기준을 적용 (if/else)
    if score >= 50:
        return {"result": "수학 과목 통과입니다! 잘했습니다."}
    else:
        return {"result": "수학 과목은 보충 학습이 필요합니다."}

# --- 3. Conditional Edge(라우터) 함수 정의 ---

def router(state: GradeReportState) -> str:
    """State의 'subject' 값에 따라 다음 노드를 결정합니다."""
    subject = state['subject']
    print(f"📌 2. 라우터 실행: '{subject}' 과목에 따라 경로를 결정합니다.")
    
    if subject == "국어":
        return "korean_node"
    elif subject == "수학":
        return "math_node"
    else:
        # 지원하지 않는 과목이거나 입력 오류일 경우 바로 종료
        return "__end__"

# --- 4. 그래프 구성 ---
workflow = StateGraph(GradeReportState)

# 1단계: 노드들을 그래프에 추가합니다.
workflow.add_node("parser", input_parser_node)
workflow.add_node("korean_node", evaluate_korean_node)
workflow.add_node("math_node", evaluate_math_node)

# 2단계: 그래프의 시작점을 설정합니다.
workflow.set_entry_point("parser")

# 3단계: 조건부 엣지를 추가합니다.
# 'parser' 노드가 끝난 후, 'router' 함수의 결정에 따라 다음 노드로 분기합니다.
workflow.add_conditional_edges(
    "parser",
    router,
    {
        "korean_node": "korean_node",
        "math_node": "math_node",
        "__end__": END # router가 '__end__'를 반환하면 그래프 종료
    }
)

# 4단계: 마지막 노드들을 종료(END) 지점에 연결합니다.
workflow.add_edge("korean_node", END)
workflow.add_edge("math_node", END)

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