# LangGraph 0.6+ Context API 가이드

## 📌 개요

LangGraph 0.6 버전부터 도입된 **Context API**는 그래프 실행 중 State에 포함되지 않는 런타임 정보를 노드에 전달하는 메커니즘입니다.

---

## 🔍 State vs Config vs Context

### 1. **State** - 그래프 상태 관리

**목적:** 노드 간 공유되는 데이터 구조

**특징:**
- TypedDict, dataclass, Pydantic 모델로 정의
- 그래프 실행 중 업데이트되는 현재 스냅샷
- Reducer 함수로 업데이트 방식 제어

**예시:**
```python
from typing import TypedDict, Annotated
from operator import add

class State(TypedDict):
    messages: Annotated[list, add]  # 리스트 누적
    counter: int                     # 값 덮어쓰기
    user_name: str
```

**사용 시점:**
- ✅ 노드 간 데이터 전달 (메시지, 결과, 카운터 등)
- ✅ 그래프 실행 중 변경되는 데이터
- ✅ 최종 결과로 반환해야 하는 데이터

---

### 2. **Config** - 실행 설정 정보

**목적:** 그래프 실행 시 메타데이터 및 설정 전달

**특징:**
- `RunnableConfig` 객체
- `thread_id`, tracing 정보, 사용자 정의 설정 포함
- `config["configurable"]` 딕셔너리로 접근

**예시:**
```python
# 그래프 실행 시 config 전달
result = app.invoke(
    {"messages": []},
    config={
        "configurable": {
            "thread_id": "session-123",
            "model_name": "gpt-4",
            "temperature": 0.7
        }
    }
)

# 노드에서 config 접근 (0.6 이전 방식)
def old_node(state: State, config: dict):
    model = config.get("configurable", {}).get("model_name")
    return {"messages": [f"Using {model}"]}
```

**사용 시점:**
- ✅ 세션 ID, 스레드 ID 전달
- ✅ 모델 이름, 온도 같은 실행 파라미터
- ✅ 디버깅/추적을 위한 메타데이터

---

### 3. **Context** - 런타임 리소스 공유 (0.6+)

**목적:** State에 포함되지 않는 외부 리소스를 노드에 전달

**특징:**
- `from langgraph.managed import Context` 임포트
- 데이터베이스 연결, API 클라이언트, LLM 프로바이더 등 전달
- Config보다 깔끔한 문법으로 접근 가능
- dataclass로 스키마 정의

**예시:**
```python
from langgraph.managed import Context
from dataclasses import dataclass

# Context 스키마 정의
@dataclass
class ContextSchema:
    llm_provider: str = "openai"
    db_connection: object = None
    api_key: str = ""

# 그래프 생성 시 context_schema 지정
workflow = StateGraph(State, context_schema=ContextSchema)

# 노드에서 Context 접근
def my_node(state: State):
    ctx = Context()
    provider = ctx.get("llm_provider")
    api_key = ctx.get("api_key")

    print(f"Using {provider} with key {api_key}")
    return {"messages": ["완료"]}

# 실행 시 context 전달
result = app.invoke(
    {"messages": []},
    context={
        "llm_provider": "anthropic",
        "api_key": "sk-12345"
    }
)
```

**사용 시점:**
- ✅ DB 연결, 캐시 같은 무거운 리소스 공유
- ✅ API 클라이언트, LLM 프로바이더
- ✅ State에 포함시키기 애매한 런타임 의존성

---

## 🆚 비교 요약표

| 구분 | State | Config | Context (0.6+) |
|------|-------|--------|----------------|
| **목적** | 노드 간 데이터 전달 | 실행 설정 정보 | 외부 리소스 공유 |
| **정의 방법** | TypedDict/dataclass | RunnableConfig | dataclass 스키마 |
| **접근 방법** | `state["key"]` | `config["configurable"]["key"]` | `Context().get("key")` |
| **변경 여부** | ✅ 노드에서 업데이트 가능 | ❌ 읽기 전용 | ❌ 읽기 전용 |
| **Reducer 사용** | ✅ 가능 | ❌ 불가능 | ❌ 불가능 |
| **반환 값 포함** | ✅ 최종 결과에 포함 | ❌ 미포함 | ❌ 미포함 |
| **예시** | messages, counter | thread_id, model_name | db_connection, api_key |

---

## 📖 실전 예시

### 예시 1: State 사용 (노드 간 데이터 전달)

```python
from typing import TypedDict, Annotated
from operator import add

class ChatState(TypedDict):
    messages: Annotated[list, add]
    user_input: str

def process_node(state: ChatState) -> ChatState:
    user_msg = state["user_input"]
    return {
        "messages": [f"처리 완료: {user_msg}"]
    }

# 실행
result = app.invoke({"messages": [], "user_input": "안녕"})
print(result["messages"])  # ['처리 완료: 안녕']
```

---

### 예시 2: Config 사용 (실행 설정)

```python
class State(TypedDict):
    output: str

def config_node(state: State, config: dict) -> State:
    # Config에서 설정 읽기
    model = config.get("configurable", {}).get("model", "gpt-3.5")
    temp = config.get("configurable", {}).get("temperature", 0.5)

    return {"output": f"Model: {model}, Temp: {temp}"}

# 실행 시 config 전달
result = app.invoke(
    {"output": ""},
    config={
        "configurable": {
            "model": "gpt-4",
            "temperature": 0.9
        }
    }
)
print(result["output"])  # "Model: gpt-4, Temp: 0.9"
```

---

### 예시 3: Context 사용 (리소스 공유)

```python
from langgraph.managed import Context
from dataclasses import dataclass

@dataclass
class AppContext:
    db_url: str = "localhost:5432"
    cache_enabled: bool = True

class State(TypedDict):
    result: str

def db_node(state: State) -> State:
    ctx = Context()
    db_url = ctx.get("db_url")
    cache = ctx.get("cache_enabled")

    return {"result": f"DB: {db_url}, Cache: {cache}"}

# 그래프 생성
workflow = StateGraph(State, context_schema=AppContext)
workflow.add_node("db", db_node)
# ...

app = workflow.compile()

# 실행 시 context 전달
result = app.invoke(
    {"result": ""},
    context={
        "db_url": "prod-db:5432",
        "cache_enabled": False
    }
)
print(result["result"])  # "DB: prod-db:5432, Cache: False"
```

---

## 🔄 0.6 이전 vs 이후 문법 비교

### ❌ 0.6 이전 (Config만 사용)

```python
def old_node(state: State, config: dict) -> State:
    # config에서 직접 꺼내야 함
    api_key = config.get("configurable", {}).get("api_key", "")
    db_url = config.get("configurable", {}).get("db_url", "")

    # 중첩된 딕셔너리 접근이 번거로움
    return {"result": f"API: {api_key}, DB: {db_url}"}
```

### ✅ 0.6 이후 (Context API)

```python
from langgraph.managed import Context

def new_node(state: State) -> State:
    ctx = Context()
    api_key = ctx.get("api_key", "")
    db_url = ctx.get("db_url", "")

    # 훨씬 간결하고 직관적
    return {"result": f"API: {api_key}, DB: {db_url}"}
```

**장점:**
- 노드 함수에 `config` 매개변수 불필요
- `Context()` 객체로 어디서든 접근 가능
- 코드 가독성과 유지보수성 향상

---

## 🎯 언제 무엇을 사용할까?

### State를 사용해야 하는 경우
```python
✅ 노드 간 메시지 누적
✅ 계산 결과 저장 및 전달
✅ 사용자 입력, 대화 기록
✅ 최종 반환값에 포함되어야 하는 데이터
```

### Config를 사용해야 하는 경우
```python
✅ 세션 ID, 스레드 ID (추적/디버깅)
✅ 실행 시점의 메타데이터
✅ 간단한 스칼라 설정값 (문자열, 숫자)
✅ LangSmith 트레이싱 정보
```

### Context를 사용해야 하는 경우
```python
✅ 데이터베이스 연결 객체
✅ API 클라이언트 (OpenAI, Anthropic 등)
✅ 캐시, 세션 스토어
✅ 파일 시스템, S3 같은 외부 리소스
✅ 무거운 객체를 여러 노드에서 재사용
```

---

## 💡 Best Practices

### 1. Context 스키마는 dataclass로 정의
```python
from dataclasses import dataclass

@dataclass
class MyContext:
    api_key: str = ""
    db_pool: object = None
    cache: object = None
```

### 2. 기본값 제공으로 안전성 확보
```python
@dataclass
class Context:
    api_key: str = "default-key"
    timeout: int = 30

def my_node(state: State, runtime: Runtime[Context]):
    # dataclass 기본값 활용
    api_key = runtime.context.api_key
    timeout = runtime.context.timeout
```

### 3. 무거운 리소스는 Context로, 간단한 값은 Config로
```python
@dataclass
class Context:
    db: object = None

# ✅ 좋은 예: DB 객체는 Context로
context = Context(db=db_connection)

# ✅ 간단한 값은 Config로
config = {"configurable": {"thread_id": "abc", "model": "gpt-4"}}
```

### 4. Context는 읽기 전용, 변경이 필요하면 State 사용
```python
# ❌ Context는 변경 불가
def node(state: State, runtime: Runtime[Context]):
    runtime.context.api_key = "new-key"  # 불가능!

# ✅ 변경이 필요한 데이터는 State에 포함
class State(TypedDict):
    api_key: str  # State로 관리
```

---

## 🔗 참고 자료

- [LangGraph Official Docs - Low Level Concepts](https://langchain-ai.github.io/langgraph/concepts/low_level/)
- [LangGraph Context API](https://langchain-ai.github.io/langgraph/concepts/low_level/#context)
- [LangGraph Configuration](https://langchain-ai.github.io/langgraph/concepts/low_level/#config)

---

## 📝 요약

| 개념 | 한 줄 설명 |
|------|-----------|
| **State** | 노드 간 공유되며 업데이트되는 그래프 데이터 |
| **Config** | 실행 시점의 메타데이터와 간단한 설정값 |
| **Context** | State에 포함되지 않는 외부 리소스 (DB, API 등) |

**핵심:** State는 "무엇을 처리할지", Config는 "어떻게 실행할지", Context는 "어떤 도구를 사용할지"를 담당합니다.