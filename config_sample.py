# ==============================================================================
# 0. 필요한 라이브러리 임포트
# ==============================================================================
from typing import TypedDict, Annotated, Literal
from operator import add
from dataclasses import dataclass
from langgraph.graph import StateGraph, START, END
from langgraph.managed import Context

# ==============================================================================
# 1. 스키마 정의: State, Context
# State: 그래프의 작업 데이터. 노드를 거치며 변경되고 저장됩니다.
# Context: 그래프가 사용할 외부 도구. 실행 동안 변하지 않습니다.
# ==============================================================================

# 📜 State 정의: 온라인 주문 처리 과정을 기록할 작업 명세서
class OrderState(TypedDict):
    # 입력 데이터 (초기값으로 제공됨)
    user_id: str
    item_id: str
    
    # 작업 과정 및 결과 기록 (노드가 실행되면서 채워짐)
    inventory_status: Literal["available", "out_of_stock", ""]
    payment_status: Literal["success", "failed", ""]
    shipping_id: str
    
    # 모든 단계의 로그를 누적해서 저장
    logs: Annotated[list, add]

# 🧰 Context 정의: 그래프가 사용할 외부 도구(리소스) 모음
@dataclass
class AppContext:
    db_conn: object      # 재고 확인을 위한 데이터베이스 연결 객체
    payment_client: object # 결제를 위한 API 클라이언트

# ==============================================================================
# 2. 노드 함수 정의
# 각 노드는 State와 Context를 활용하여 자신의 작업을 수행하고,
# 변경된 State 부분을 반환합니다.
# ==============================================================================

def check_inventory(state: OrderState):
    """Context의 DB 커넥션을 사용해 재고를 확인하고 State를 업데이트합니다."""
    ctx = Context()
    db = ctx.get("db_conn") # Context에서 DB 커넥션을 꺼냄
    
    print(f"-> (1) 재고 확인 노드 실행: [{db}]에서 item '{state['item_id']}' 재고 확인 중...")
    # 실제 로직 예시: stock = db.check_stock(state['item_id'])
    
    # 작업 결과를 State에 기록하여 반환
    return {
        "inventory_status": "available", 
        "logs": ["Inventory: OK"]
    }

def process_payment(state: OrderState):
    """Context의 결제 클라이언트를 사용해 결제를 처리하고 State를 업데이트합니다."""
    ctx = Context()
    client = ctx.get("payment_client") # Context에서 결제 클라이언트를 꺼냄
    
    print(f"-> (2) 결제 처리 노드 실행: [{client}]로 user '{state['user_id']}' 결제 처리 중...")
    # 실제 로직 예시: result = client.charge(state['user_id'], amount=100)

    return {
        "payment_status": "success", 
        "logs": ["Payment: Success"]
    }
    
def start_shipping(state: OrderState):
    """배송을 시작하고 State를 업데이트합니다."""
    print("-> (3) 배송 시작 노드 실행...")
    shipping_id = "SHP-12345" # 배송 ID 생성
    
    return {
        "shipping_id": shipping_id,
        "logs": [f"Shipping started. ID: {shipping_id}"]
    }

# ==============================================================================
# 3. 그래프 구성
# State, Context 스키마를 정의하고 노드와 엣지를 연결합니다.
# ==============================================================================

def should_proceed(state: OrderState):
    """State를 보고 다음 경로를 결정하는 조건부 엣지 함수입니다."""
    print("-> (분기) 재고 상태 확인...")
    if state["inventory_status"] == "available":
        return "process_payment"  # 재고 있으면 결제 진행
    else:
        return "end_process"      # 재고 없으면 종료

# StateGraph(state_schema, context_schema)
# StateGraph의 첫 번째 인자가 state_schema, context_schema는 명시적으로 지정합니다.
workflow = StateGraph(OrderState, context_schema=AppContext)

# 노드 추가
workflow.add_node("check_inventory", check_inventory)
workflow.add_node("process_payment", process_payment)
workflow.add_node("start_shipping", start_shipping)

# 엣지 연결
workflow.add_edge(START, "check_inventory")

# 조건부 엣지 추가: check_inventory 노드 이후, should_proceed 함수의 결과에 따라 경로가 나뉩니다.
workflow.add_conditional_edges(
    "check_inventory",
    should_proceed,
    {
        "process_payment": "process_payment", # "process_payment" 문자열이 반환되면 process_payment 노드로 이동
        "end_process": END                    # "end_process" 문자열이 반환되면 그래프 종료
    }
)

workflow.add_edge("process_payment", "start_shipping")
workflow.add_edge("start_shipping", END)

# 그래프 컴파일
app = workflow.compile()


# ==============================================================================
# 4. 실행
# State, Config, Context를 각각의 인자로 주입하여 그래프를 실행합니다.
# ==============================================================================

# ----------------- 외부 환경 준비 -----------------
# 🧰 Context: 실제 DB 커넥션과 결제 클라이언트 객체를 준비합니다.
db_connection = "Real_PostgreSQL_Connection"
payment_gateway = "Real_Stripe_API_Client"
app_context_objects = {
    "db_conn": db_connection,
    "payment_client": payment_gateway
}

# 📝 Config: 이 실행을 식별할 고유 ID(세션 ID)를 준비합니다.
# 이는 체크포인터가 어떤 대화 기록을 찾을지 알려주는 '주소' 역할을 합니다.
order_id = "ORD-2025-09-28-001"
app_config = {"configurable": {"thread_id": order_id}}

# 📜 State: 그래프의 시작에 필요한 초기 데이터를 준비합니다.
initial_state = {
    "user_id": "user-777",
    "item_id": "item-abc",
    "inventory_status": "",
    "payment_status": "",
    "shipping_id": "",
    "logs": []
}
# ------------------------------------------------

# ▶️ 실행: invoke 함수에 세 가지 요소를 모두 전달합니다.
print("="*30, "그래프 실행 시작", "="*30)
final_state = app.invoke(
    initial_state,       # State: 작업할 데이터
    config=app_config,   # Config: 실행 설정 및 세션 ID
    context=app_context_objects # Context: 사용할 도구
)
print("="*30, "그래프 실행 종료", "="*30)

# 🏁 결과 확인
print("\n--- 최종 주문 상태 (Final State) ---")
import json
print(json.dumps(final_state, indent=4, ensure_ascii=False))