from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Any
from operator import add

# ========== 1. ADD Reducer (리스트 누적) ==========
print("=" * 60)
print("1. ADD Reducer - 리스트에 요소 추가")
print("=" * 60)

class AddState(TypedDict):
    messages: Annotated[list, add]  # 각 노드에서 반환한 리스트가 누적됨
    count: int

def node1_add_node(state: AddState) -> AddState:
    return {
        "messages": ["첫 번째 메시지"],  # 리스트 반환
        "count": 1
    }

def node2_add_node(state: AddState) -> AddState:
    return {
        "messages": ["두 번째 메시지"],  # 이전 messages에 추가됨
        "count": 2
    }

def node3_add_node(state: AddState) -> AddState:
    return {
        "messages": ["세 번째 메시지"],  # 계속 누적
        "count": 3
    }

# Graph 구성
workflow_add = StateGraph(AddState)
workflow_add.add_node("node1", node1_add_node)
workflow_add.add_node("node2", node2_add_node)
workflow_add.add_node("node3", node3_add_node)
workflow_add.add_edge(START, "node1")
workflow_add.add_edge("node1", "node2")
workflow_add.add_edge("node2", "node3")
workflow_add.add_edge("node3", END)

app_add = workflow_add.compile()

# 실행
result = app_add.invoke({"messages": [], "count": 0})
print(f"초기: messages=[]")
print(f"최종: messages={result['messages']}")
print(f"     count={result['count']}")
print()

# ========== 2. Custom Reducer - 최대값 유지 ==========
print("=" * 60)
print("2. Custom Reducer - 최대값만 유지")
print("=" * 60)

def max_reducer(current: int, new: int) -> int:
    """현재 값과 새 값 중 큰 값을 유지"""
    if new is None:
        return current
    if current is None:
        return new
    return max(current, new)

class MaxState(TypedDict):
    score: Annotated[int, max_reducer]  # 최대값만 유지
    name: str

def node1_max_node(state: MaxState) -> MaxState:
    print(f"  Node1: score=75 반환")
    return {"score": 75, "name": "Node1"}

def node2_max_node(state: MaxState) -> MaxState:
    print(f"  Node2: score=90 반환 (현재 최대: {state['score']})")
    return {"score": 90, "name": "Node2"}

def node3_max_node(state: MaxState) -> MaxState:
    print(f"  Node3: score=85 반환 (현재 최대: {state['score']})")
    return {"score": 85, "name": "Node3"}  # 90보다 작으므로 무시됨

# Graph 구성
workflow_max = StateGraph(MaxState)
workflow_max.add_node("node1", node1_max_node)
workflow_max.add_node("node2", node2_max_node)
workflow_max.add_node("node3", node3_max_node)
workflow_max.add_edge(START, "node1")
workflow_max.add_edge("node1", "node2")
workflow_max.add_edge("node2", "node3")
workflow_max.add_edge("node3", END)

app_max = workflow_max.compile()

# 실행
result = app_max.invoke({"score": 0, "name": ""})
print(f"최종 최대값: score={result['score']} (from {result['name']})")
print()

# ========== 3. Dict Merge Reducer ==========
print("=" * 60)
print("3. Dict Merge Reducer - 딕셔너리 병합")
print("=" * 60)

def merge_dicts(current: dict, new: dict) -> dict:
    """두 딕셔너리를 병합 (deep merge)"""
    if new is None:
        return current
    if current is None:
        return new
    
    result = current.copy()
    for key, value in new.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)  # 재귀적 병합
        else:
            result[key] = value
    return result

class MergeState(TypedDict):
    config: Annotated[dict, merge_dicts]  # 딕셔너리 병합
    step: int

def node1_merge_node(state: MergeState) -> MergeState:
    return {
        "config": {
            "database": {"host": "localhost", "port": 5432}
        },
        "step": 1
    }

def node2_merge_node(state: MergeState) -> MergeState:
    return {
        "config": {
            "database": {"user": "admin"},  # database 내용 병합
            "cache": {"enabled": True}       # 새 키 추가
        },
        "step": 2
    }

def node3_merge_node(state: MergeState) -> MergeState:
    return {
        "config": {
            "cache": {"ttl": 3600},  # cache 내용 병합
            "logging": {"level": "INFO"}  # 새 키 추가
        },
        "step": 3
    }

# Graph 구성
workflow_merge = StateGraph(MergeState)
workflow_merge.add_node("node1", node1_merge_node)
workflow_merge.add_node("node2", node2_merge_node)
workflow_merge.add_node("node3", node3_merge_node)
workflow_merge.add_edge(START, "node1")
workflow_merge.add_edge("node1", "node2")
workflow_merge.add_edge("node2", "node3")
workflow_merge.add_edge("node3", END)

app_merge = workflow_merge.compile()

# 실행
result = app_merge.invoke({"config": {}, "step": 0})
print(f"초기: config={{}}")
print(f"최종 병합된 config:")
import json
print(json.dumps(result['config'], indent=2))
print()

# ========== 4. String Concatenation Reducer ==========
print("=" * 60)
print("4. String Concatenation Reducer - 문자열 연결")
print("=" * 60)

def concat_strings_node(current: str, new: str) -> str:
    """문자열을 연결 (구분자 포함)"""
    if new is None:
        return current
    if current is None or current == "":
        return new
    return f"{current} → {new}"

class ConcatState(TypedDict):
    journey: Annotated[str, concat_strings]  # 여정 기록
    current_location: str

def node1_concat_node(state: ConcatState) -> ConcatState:
    return {
        "journey": "서울",
        "current_location": "서울"
    }

def node2_concat_node(state: ConcatState) -> ConcatState:
    return {
        "journey": "부산",
        "current_location": "부산"
    }

def node3_concat_node(state: ConcatState) -> ConcatState:
    return {
        "journey": "제주",
        "current_location": "제주"
    }

# Graph 구성
workflow_concat = StateGraph(ConcatState)
workflow_concat.add_node("node1", node1_concat_node)
workflow_concat.add_node("node2", node2_concat_node)
workflow_concat.add_node("node3", node3_concat_node)
workflow_concat.add_edge(START, "node1")
workflow_concat.add_edge("node1", "node2")
workflow_concat.add_edge("node2", "node3")
workflow_concat.add_edge("node3", END)

app_concat = workflow_concat.compile()

# 실행
result = app_concat.invoke({"journey": "", "current_location": ""})
print(f"여정: {result['journey']}")
print(f"현재 위치: {result['current_location']}")
print()

# ========== 5. Set Union Reducer (중복 제거) ==========
print("=" * 60)
print("5. Set Union Reducer - 중복 없이 누적")
print("=" * 60)

def union_sets(current: set, new: set) -> set:
    """Set union - 중복 없이 합치기"""
    if new is None:
        return current
    if current is None:
        return new
    return current.union(new)

class SetState(TypedDict):
    tags: Annotated[set, union_sets]  # 중복 없이 태그 수집
    count: int

def node1_set(state: SetState) -> SetState:
    return {
        "tags": {"python", "langgraph"},
        "count": 2
    }

def node2_set(state: SetState) -> SetState:
    return {
        "tags": {"python", "ai", "ml"},  # python은 중복
        "count": 3
    }

def node3_set(state: SetState) -> SetState:
    return {
        "tags": {"langgraph", "agent"},  # langgraph는 중복
        "count": 2
    }

# Graph 구성
workflow_set = StateGraph(SetState)
workflow_set.add_node("node1", node1_set)
workflow_set.add_node("node2", node2_set)
workflow_set.add_node("node3", node3_set)
workflow_set.add_edge(START, "node1")
workflow_set.add_edge("node1", "node2")
workflow_set.add_edge("node2", "node3")
workflow_set.add_edge("node3", END)

app_set = workflow_set.compile()

# 실행
result = app_set.invoke({"tags": set(), "count": 0})
print(f"수집된 고유 태그: {result['tags']}")
print(f"태그 수: {len(result['tags'])}개")
print()

# ========== 6. Last Value Wins (기본 동작) ==========
print("=" * 60)
print("6. No Reducer (Last Value Wins) - 마지막 값만 유지")
print("=" * 60)

class LastState(TypedDict):
    value: str  # Reducer 없음 - 마지막 값만 유지
    history: Annotated[list, add]  # 이건 누적

def node1_last(state: LastState) -> LastState:
    return {
        "value": "첫 번째",
        "history": ["Node1 실행"]
    }

def node2_last(state: LastState) -> LastState:
    return {
        "value": "두 번째",  # 첫 번째를 덮어씀
        "history": ["Node2 실행"]
    }

def node3_last(state: LastState) -> LastState:
    return {
        "value": "세 번째",  # 두 번째를 덮어씀
        "history": ["Node3 실행"]
    }

# Graph 구성
workflow_last = StateGraph(LastState)
workflow_last.add_node("node1", node1_last)
workflow_last.add_node("node2", node2_last)
workflow_last.add_node("node3", node3_last)
workflow_last.add_edge(START, "node1")
workflow_last.add_edge("node1", "node2")
workflow_last.add_edge("node2", "node3")
workflow_last.add_edge("node3", END)

app_last = workflow_last.compile()

# 실행
result = app_last.invoke({"value": "", "history": []})
print(f"value (마지막 값만): {result['value']}")
print(f"history (누적): {result['history']}")

print("\n" + "=" * 60)
print("✅ Reducer 패턴 정리")
print("=" * 60)
print("1. add: 리스트에 요소 추가 (from operator import add)")
print("2. Custom Max: 최대값만 유지")
print("3. Dict Merge: 딕셔너리 깊은 병합")
print("4. String Concat: 문자열 연결")
print("5. Set Union: 중복 제거하며 합치기")
print("6. No Reducer: 마지막 값으로 덮어쓰기 (기본)")
print("=" * 60)