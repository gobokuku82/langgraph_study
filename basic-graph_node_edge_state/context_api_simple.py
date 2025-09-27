from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig
from typing import TypedDict, Annotated
from operator import add
from dataclasses import dataclass

# ========== 1. State만 사용 (가장 기본) ==========
print("=" * 60)
print("1. State만 사용 - 노드 간 데이터 전달")
print("=" * 60)

class SimpleState(TypedDict):
    name: str
    age: int
    messages: Annotated[list, add]

def node1(state: SimpleState) -> SimpleState:
    print(f"  Node1: {state['name']}님 안녕하세요!")
    return {
        "messages": ["Node1 실행됨"]
    }

def node2(state: SimpleState) -> SimpleState:
    print(f"  Node2: {state['name']}님은 {state['age']}살입니다")
    return {
        "messages": ["Node2 실행됨"]
    }

workflow1 = StateGraph(SimpleState)
workflow1.add_node("node1", node1)
workflow1.add_node("node2", node2)
workflow1.add_edge(START, "node1")
workflow1.add_edge("node1", "node2")
workflow1.add_edge("node2", END)

app1 = workflow1.compile()

result = app1.invoke({
    "name": "철수",
    "age": 25,
    "messages": []
})

print(f"\n최종 결과: {result['messages']}")
print()

# ========== 2. Config 추가 사용 ==========
print("=" * 60)
print("2. Config 추가 - 실행 설정 전달")
print("=" * 60)

class ConfigState(TypedDict):
    result: str

def node_with_config(state: ConfigState, config: RunnableConfig) -> ConfigState:
    model = config.get("configurable", {}).get("model", "기본모델")
    temp = config.get("configurable", {}).get("temperature", 0.5)

    print(f"  설정: model={model}, temperature={temp}")

    return {
        "result": f"모델={model}, 온도={temp}"
    }

workflow2 = StateGraph(ConfigState)
workflow2.add_node("node", node_with_config)
workflow2.add_edge(START, "node")
workflow2.add_edge("node", END)

app2 = workflow2.compile()

result = app2.invoke(
    {"result": ""},
    config={
        "configurable": {
            "model": "gpt-4",
            "temperature": 0.9
        }
    }
)

print(f"최종 결과: {result['result']}")
print()

# ========== 3. Context 사용 (0.6+) ==========
print("=" * 60)
print("3. Context 사용 - 외부 리소스 전달")
print("=" * 60)

@dataclass
class AppContext:
    user_name: str = "손님"
    api_key: str = "없음"

class ContextState(TypedDict):
    messages: Annotated[list, add]

def node_with_context(state: ContextState, runtime: Runtime[AppContext]) -> ContextState:
    user = runtime.context.user_name
    key = runtime.context.api_key

    print(f"  Context: user={user}, api_key={key}")

    return {
        "messages": [f"{user}님이 {key}로 접속"]
    }

workflow3 = StateGraph(ContextState, context_schema=AppContext)
workflow3.add_node("node", node_with_context)
workflow3.add_edge(START, "node")
workflow3.add_edge("node", END)

app3 = workflow3.compile()

result = app3.invoke(
    {"messages": []},
    context=AppContext(user_name="영희", api_key="sk-12345")
)

print(f"최종 결과: {result['messages']}")
print()

# ========== 4. State + Context 함께 사용 ==========
print("=" * 60)
print("4. State + Context 조합 - 실전 예시")
print("=" * 60)

@dataclass
class DBContext:
    db_name: str = "test_db"

class CombinedState(TypedDict):
    user_id: int
    query_results: Annotated[list, add]

def fetch_user(state: CombinedState, runtime: Runtime[DBContext]) -> CombinedState:
    db = runtime.context.db_name
    user_id = state["user_id"]

    print(f"  [{db}] User {user_id} 조회 중...")

    return {
        "query_results": [f"User {user_id} found in {db}"]
    }

def fetch_orders(state: CombinedState, runtime: Runtime[DBContext]) -> CombinedState:
    db = runtime.context.db_name
    user_id = state["user_id"]

    print(f"  [{db}] User {user_id}의 주문 조회 중...")

    return {
        "query_results": [f"User {user_id} has 3 orders"]
    }

workflow4 = StateGraph(CombinedState, context_schema=DBContext)
workflow4.add_node("fetch_user", fetch_user)
workflow4.add_node("fetch_orders", fetch_orders)
workflow4.add_edge(START, "fetch_user")
workflow4.add_edge("fetch_user", "fetch_orders")
workflow4.add_edge("fetch_orders", END)

app4 = workflow4.compile()

result = app4.invoke(
    {"user_id": 42, "query_results": []},
    context=DBContext(db_name="production_db")
)

print(f"\n최종 결과:")
for res in result["query_results"]:
    print(f"  - {res}")
print()

# ========== 5. 세 가지 모두 사용 ==========
print("=" * 60)
print("5. State + Config + Context 모두 사용")
print("=" * 60)

@dataclass
class FullContext:
    api_endpoint: str = "https://api.example.com"

class FullState(TypedDict):
    input_text: str
    output: str

def process_node(state: FullState, config: RunnableConfig, runtime: Runtime[FullContext]) -> FullState:
    # State에서 읽기
    input_text = state["input_text"]

    # Config에서 읽기
    mode = config.get("configurable", {}).get("mode", "normal")

    # Context에서 읽기
    endpoint = runtime.context.api_endpoint

    print(f"  State: input='{input_text}'")
    print(f"  Config: mode={mode}")
    print(f"  Context: endpoint={endpoint}")

    return {
        "output": f"처리완료: {input_text} (모드={mode}, 엔드포인트={endpoint})"
    }

workflow5 = StateGraph(FullState, context_schema=FullContext)
workflow5.add_node("process", process_node)
workflow5.add_edge(START, "process")
workflow5.add_edge("process", END)

app5 = workflow5.compile()

result = app5.invoke(
    {"input_text": "안녕하세요", "output": ""},
    config={"configurable": {"mode": "debug"}},
    context=FullContext(api_endpoint="https://api.prod.com")
)

print(f"\n최종 결과: {result['output']}")
print()

# ========== 정리 ==========
print("=" * 60)
print("✅ 정리")
print("=" * 60)
print("1️⃣  State:   노드 간 데이터 (name, age, messages)")
print("2️⃣  Config:  실행 설정 (model, temperature)")
print("3️⃣  Context: 외부 리소스 (api_key, db_name)")
print()
print("💡 선택 가이드:")
print("  - 데이터 전달? → State")
print("  - 실행 옵션? → Config")
print("  - DB/API 연결? → Context")
print("=" * 60)