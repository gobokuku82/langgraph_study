from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Literal
import operator

# Tools
@tool
def calculate(expression: str) -> float:
    """수식을 계산합니다."""
    try:
        return eval(expression)
    except:
        return None

@tool
def check_balance(user_id: str) -> int:
    """사용자 잔액을 확인합니다."""
    balances = {"user1": 50000, "user2": 30000, "user3": 100000}
    return balances.get(user_id, 0)


# ============================================
# State 정의 (타입 체크와 검증)
# ============================================
class AppState(TypedDict):
    messages: Annotated[list, operator.add]  # 메시지 누적
    user_id: str  # 사용자 ID
    balance: int  # 잔액
    purchase_amount: int  # 구매 금액
    calculation_history: Annotated[list, operator.add]  # 계산 이력
    error_count: int  # 오류 횟수
    max_errors: int  # 최대 오류 허용
    is_verified: bool  # 검증 완료 여부


# ============================================
# 노드 1: 사용자 확인 (State 읽기 + 업데이트)
# ============================================
def verify_user(state: AppState):
    """State에서 user_id를 읽고 잔액 조회"""
    user_id = state["user_id"]
    balance = check_balance.invoke({"user_id": user_id})

    return {
        "messages": [AIMessage(content=f"사용자 {user_id} 확인 완료")],
        "balance": balance,
        "is_verified": True
    }


# ============================================
# 노드 2: 잔액 검증 (State 검증)
# ============================================
def validate_balance(state: AppState):
    """State 값 검증 및 조건 체크"""
    balance = state["balance"]
    purchase_amount = state["purchase_amount"]

    # 타입 체크
    if not isinstance(balance, int) or not isinstance(purchase_amount, int):
        return {
            "messages": [AIMessage(content="잘못된 데이터 타입입니다")],
            "error_count": state["error_count"] + 1
        }

    # 유효성 검증
    if balance < 0 or purchase_amount < 0:
        return {
            "messages": [AIMessage(content="금액은 0 이상이어야 합니다")],
            "error_count": state["error_count"] + 1
        }

    if balance >= purchase_amount:
        return {
            "messages": [AIMessage(content=f"잔액 충분: {balance}원 >= {purchase_amount}원")]
        }
    else:
        return {
            "messages": [AIMessage(content=f"잔액 부족: {balance}원 < {purchase_amount}원")],
            "error_count": state["error_count"] + 1
        }


# ============================================
# 노드 3: 구매 처리 (State 부분 업데이트)
# ============================================
def process_purchase(state: AppState):
    """State 일부만 업데이트"""
    balance = state["balance"]
    purchase_amount = state["purchase_amount"]
    new_balance = balance - purchase_amount

    # 부분 업데이트: balance만 변경
    return {
        "messages": [AIMessage(content=f"구매 완료! 남은 잔액: {new_balance}원")],
        "balance": new_balance
    }


# ============================================
# 노드 4: 할인 적용 (State 기반 계산)
# ============================================
def apply_discount(state: AppState):
    """State 값을 기반으로 계산 후 업데이트"""
    purchase_amount = state["purchase_amount"]
    balance = state["balance"]

    # 잔액이 10만원 이상이면 10% 할인
    if balance >= 100000:
        discount = int(purchase_amount * 0.1)
        new_amount = purchase_amount - discount
        return {
            "messages": [AIMessage(content=f"VIP 할인 적용! {purchase_amount}원 → {new_amount}원")],
            "purchase_amount": new_amount,
            "calculation_history": [f"할인: -{discount}원"]
        }
    else:
        return {
            "messages": [AIMessage(content="할인 없음")]
        }


# ============================================
# 노드 5: 오류 처리
# ============================================
def handle_error(state: AppState):
    """오류 횟수 확인"""
    error_count = state["error_count"]
    return {
        "messages": [AIMessage(content=f"오류 발생 ({error_count}회)")]
    }


# ============================================
# 조건 분기: State 기반
# ============================================
def route_after_verify(state: AppState) -> Literal["discount", "error"]:
    """검증 완료 여부에 따라 분기"""
    if state["is_verified"]:
        return "discount"
    else:
        return "error"


def route_after_discount(state: AppState) -> Literal["validate", "error"]:
    """할인 적용 후 검증으로 이동"""
    return "validate"


def route_after_validate(state: AppState) -> Literal["purchase", "error", "end"]:
    """State 값 기반 조건 분기"""
    balance = state["balance"]
    purchase_amount = state["purchase_amount"]
    error_count = state["error_count"]
    max_errors = state["max_errors"]

    # 오류 횟수 초과
    if error_count >= max_errors:
        return "error"

    # 잔액 충분
    if balance >= purchase_amount:
        return "purchase"

    # 잔액 부족
    return "end"


# ============================================
# 그래프 구성
# ============================================
graph = StateGraph(AppState)

graph.add_node("verify", verify_user)
graph.add_node("discount", apply_discount)
graph.add_node("validate", validate_balance)
graph.add_node("purchase", process_purchase)
graph.add_node("error", handle_error)

graph.add_edge(START, "verify")
graph.add_conditional_edges("verify", route_after_verify)
graph.add_conditional_edges("discount", route_after_discount)
graph.add_conditional_edges("validate", route_after_validate)
graph.add_edge("purchase", END)
graph.add_edge("error", END)

app = graph.compile()


# ============================================
# 실행 예제
# ============================================
print("=== 케이스 1: 정상 구매 (VIP 할인) ===")
result = app.invoke({
    "messages": [],
    "user_id": "user3",
    "balance": 0,
    "purchase_amount": 80000,
    "calculation_history": [],
    "error_count": 0,
    "max_errors": 3,
    "is_verified": False
})

for msg in result["messages"]:
    print(f"  {msg.content}")
print(f"  최종 잔액: {result['balance']}원")
print(f"  계산 이력: {result['calculation_history']}\n")


print("=== 케이스 2: 잔액 부족 ===")
result = app.invoke({
    "messages": [],
    "user_id": "user2",
    "balance": 0,
    "purchase_amount": 50000,
    "calculation_history": [],
    "error_count": 0,
    "max_errors": 3,
    "is_verified": False
})

for msg in result["messages"]:
    print(f"  {msg.content}")
print(f"  오류 횟수: {result['error_count']}\n")


print("=== 케이스 3: 일반 구매 (할인 없음) ===")
result = app.invoke({
    "messages": [],
    "user_id": "user1",
    "balance": 0,
    "purchase_amount": 30000,
    "calculation_history": [],
    "error_count": 0,
    "max_errors": 3,
    "is_verified": False
})

for msg in result["messages"]:
    print(f"  {msg.content}")
print(f"  최종 잔액: {result['balance']}원")