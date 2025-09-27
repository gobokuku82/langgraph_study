####################################################
# 작업에 필요한 모든 정보를 담을 State를 정의합니다.
####################################################

from typing import TypedDict, Annotated, Literal
from operator import add

class OrderState(TypedDict):
    # 입력 데이터
    user_id: str
    item_id: str
    
    # 작업 과정 및 결과 기록
    inventory_status: Literal["available", "out_of_stock", ""]
    payment_status: Literal["success", "failed", ""]
    shipping_id: str
    
    # 모든 단계의 로그를 누적해서 저장
    logs: Annotated[list, add]

####################################################
# 실행 및 결과 확인
# 이제 thread_id와 함께 그래프를 실행하면, 모든 과정이 State에 기록됩니다.
####################################################

def check_inventory(state: OrderState):
    """재고를 확인하고 State를 업데이트합니다."""
    print(f"Checking inventory for item: {state['item_id']}")
    # (실제 재고 확인 로직) ...
    
    # 작업 결과를 State에 기록
    return {
        "inventory_status": "available", 
        "logs": ["Inventory: OK"]
    }

def process_payment(state: OrderState):
    """결제를 처리하고 State를 업데이트합니다."""
    print(f"Processing payment for user: {state['user_id']}")
    # (실제 결제 로직) ...

    return {
        "payment_status": "success", 
        "logs": ["Payment: Success"]
    }
    
def start_shipping(state: OrderState):
    """배송을 시작하고 State를 업데이트합니다."""
    print("Starting shipping process...")
    shipping_id = "SHP-12345" # 배송 ID 생성
    
    return {
        "shipping_id": shipping_id,
        "logs": [f"Shipping started. ID: {shipping_id}"]
    }

####################################################
# 그래프 구성 (조건부 분기 포함)
# 재고 유무에 따라 다음 단계를 결정하는 조건부 분기를 추가합니다.
####################################################

from langgraph.graph import StateGraph, START, END

def should_proceed(state: OrderState):
    """State를 보고 다음 경로를 결정합니다."""
    if state["inventory_status"] == "available":
        return "process_payment"
    else:
        return "end_process"

# 그래프 빌드
workflow = StateGraph(OrderState)
workflow.add_node("check_inventory", check_inventory)
workflow.add_node("process_payment", process_payment)
workflow.add_node("start_shipping", start_shipping)

# 분기 노드 추가
workflow.add_conditional_edges(
    "check_inventory",
    should_proceed,
    {
        "process_payment": "process_payment",
        "end_process": END
    }
)

workflow.add_edge(START, "check_inventory")
workflow.add_edge("process_payment", "start_shipping")
workflow.add_edge("start_shipping", END)

app = workflow.compile()

####################################################
# 실행 및 결과 확인
# 이제 thread_id와 함께 그래프를 실행하면, 모든 과정이 State에 기록됩니다.
# 실행할 때마다 고유한 주문 ID를 thread_id로 사용
####################################################

order_id = "ORD-2025-09-28-001"
config = {"configurable": {"thread_id": order_id}}

# 초기 State와 함께 실행
final_state = app.invoke(
    {
        "user_id": "user-777",
        "item_id": "item-abc",
        "inventory_status": "",
        "payment_status": "",
        "shipping_id": "",
        "logs": []
    },
    config=config
)

print("\n--- 최종 주문 상태 ---")
print(final_state)

####################################################
# {
#     'user_id': 'user-777', 
#     'item_id': 'item-abc', 
#     'inventory_status': 'available', 
#     'payment_status': 'success', 
#     'shipping_id': 'SHP-12345', 
#     'logs': [
#         'Inventory: OK', 
#         'Payment: Success', 
#         'Shipping started. ID: SHP-12345'
#     ]
# }
####################################################