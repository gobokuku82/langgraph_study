from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from typing import TypedDict, Annotated
from operator import add
from dataclasses import dataclass

# ========== 1. 기본 Context 사용 ==========
print("=" * 60)
print("1. Context API 기본 - Runtime으로 데이터 전달")
print("=" * 60)

@dataclass
class BasicContext:
    user_name: str = "Unknown"
    api_key: str = "none"

class BasicState(TypedDict):
    messages: Annotated[list, add]
    count: int

def node1_basic(state: BasicState, runtime: Runtime[BasicContext]) -> BasicState:
    user = runtime.context.user_name
    api_key = runtime.context.api_key

    print(f"  Node1 - user: {user}, api_key: {api_key}")
    return {
        "messages": [f"Node1 실행 (user={user})"],
        "count": 1
    }

def node2_basic(state: BasicState, runtime: Runtime[BasicContext]) -> BasicState:
    user = runtime.context.user_name

    print(f"  Node2 - user: {user}")
    return {
        "messages": [f"Node2 실행 (user={user})"],
        "count": 2
    }

workflow_basic = StateGraph(BasicState, context_schema=BasicContext)
workflow_basic.add_node("node1", node1_basic)
workflow_basic.add_node("node2", node2_basic)
workflow_basic.add_edge(START, "node1")
workflow_basic.add_edge("node1", "node2")
workflow_basic.add_edge("node2", END)

app_basic = workflow_basic.compile()

result = app_basic.invoke(
    {"messages": [], "count": 0},
    context=BasicContext(user_name="Alice", api_key="sk-12345")
)

print(f"결과: {result['messages']}")
print()

# ========== 2. Config vs Context 비교 ==========
print("=" * 60)
print("2. Config vs Context - 전달 방식 비교")
print("=" * 60)

@dataclass
class MixedContext:
    temperature: float = 0.5

class ConfigState(TypedDict):
    messages: Annotated[list, add]

def node_with_context(state: ConfigState, config: dict, runtime: Runtime[MixedContext]) -> ConfigState:
    from_context = runtime.context.temperature
    from_config = config.get("configurable", {}).get("model", "없음")

    print(f"  Context에서: temperature={from_context}")
    print(f"  Config에서: model={from_config}")

    return {
        "messages": [f"temp={from_context}, model={from_config}"]
    }

workflow_config = StateGraph(ConfigState, context_schema=MixedContext)
workflow_config.add_node("node", node_with_context)
workflow_config.add_edge(START, "node")
workflow_config.add_edge("node", END)

app_config = workflow_config.compile()

result = app_config.invoke(
    {"messages": []},
    config={"configurable": {"model": "gpt-4"}},
    context=MixedContext(temperature=0.7)
)

print(f"결과: {result['messages']}")
print()

# ========== 3. Context로 DB 연결 공유 ==========
print("=" * 60)
print("3. Context 활용 - 리소스 공유 (DB 연결 시뮬레이션)")
print("=" * 60)

class FakeDB:
    def __init__(self, name: str):
        self.name = name
        print(f"  [DB 연결 생성: {name}]")

    def query(self, sql: str):
        return f"결과 from {self.name}: {sql}"

@dataclass
class DBContext:
    db: FakeDB = None

class DBState(TypedDict):
    messages: Annotated[list, add]
    records: Annotated[list, add]

def node_query1(state: DBState, runtime: Runtime[DBContext]) -> DBState:
    db = runtime.context.db

    result = db.query("SELECT * FROM users")
    print(f"  Node1 쿼리: {result}")

    return {
        "messages": ["Node1 완료"],
        "records": [result]
    }

def node_query2(state: DBState, runtime: Runtime[DBContext]) -> DBState:
    db = runtime.context.db

    result = db.query("SELECT * FROM orders")
    print(f"  Node2 쿼리: {result}")

    return {
        "messages": ["Node2 완료"],
        "records": [result]
    }

workflow_db = StateGraph(DBState, context_schema=DBContext)
workflow_db.add_node("node1", node_query1)
workflow_db.add_node("node2", node_query2)
workflow_db.add_edge(START, "node1")
workflow_db.add_edge("node1", "node2")
workflow_db.add_edge("node2", END)

app_db = workflow_db.compile()

db_connection = FakeDB("ProductionDB")

result = app_db.invoke(
    {"messages": [], "records": []},
    context=DBContext(db=db_connection)
)

print(f"총 레코드 수: {len(result['records'])}개")
print()

# ========== 4. Context 변경 전후 문법 비교 ==========
print("=" * 60)
print("4. 문법 변화 - Context 도입 전후")
print("=" * 60)

print("❌ 0.6 이전 방식:")
print("""
def old_node(state: State, config: dict):
    # config에서 직접 꺼냄
    user = config.get('configurable', {}).get('user_name')
    api_key = config.get('configurable', {}).get('api_key')
    return {...}
""")

print("\n✅ 0.6 이후 방식 (Runtime API):")
print("""
@dataclass
class Context:
    user_name: str
    api_key: str

def new_node(state: State, runtime: Runtime[Context]):
    # Runtime으로 타입 안전하게 접근
    user = runtime.context.user_name
    api_key = runtime.context.api_key
    return {...}
""")

print("\n장점:")
print("  - 타입 안전성 (dataclass 기반)")
print("  - runtime.context.속성 으로 명확한 접근")
print("  - 코드가 더 깔끔하고 직관적")
print()

# ========== 5. State, Config, Context 차이점 정리 ==========
print("=" * 60)
print("5. State vs Config vs Context 정리")
print("=" * 60)

@dataclass
class AllContext:
    user: str = "Guest"

class AllConceptState(TypedDict):
    counter: int
    logs: Annotated[list, add]

def demo_node(state: AllConceptState, config: dict, runtime: Runtime[AllContext]) -> AllConceptState:
    print(f"  State:   counter={state['counter']} (노드 간 공유 데이터)")
    print(f"  Config:  {config.get('configurable', {})} (실행 설정)")
    print(f"  Context: user={runtime.context.user} (런타임 리소스)")

    return {
        "counter": state["counter"] + 1,
        "logs": ["실행 완료"]
    }

workflow_all = StateGraph(AllConceptState, context_schema=AllContext)
workflow_all.add_node("node", demo_node)
workflow_all.add_edge(START, "node")
workflow_all.add_edge("node", END)

app_all = workflow_all.compile()

result = app_all.invoke(
    {"counter": 0, "logs": []},
    config={"configurable": {"session_id": "abc123"}},
    context=AllContext(user="Bob")
)

print(f"\n최종 State: counter={result['counter']}, logs={result['logs']}")
print()

# ========== 정리 ==========
print("=" * 60)
print("✅ 핵심 정리")
print("=" * 60)
print("📌 State:   노드 간 데이터 전달 및 상태 관리 (Reducer로 업데이트)")
print("📌 Config:  그래프 실행 시 설정값 전달 (configurable 딕셔너리)")
print("📌 Runtime: 런타임 리소스 접근 (DB, API 클라이언트 등)")
print()
print("💡 Runtime/Context API 장점:")
print("   - dataclass 기반 타입 안전성")
print("   - runtime.context로 명확한 접근")
print("   - 무거운 리소스(DB, 캐시) 공유에 최적")
print("=" * 60)