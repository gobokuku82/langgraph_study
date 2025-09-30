"""
LangGraph State 리듀서 예시 - 기본 버전 (헬퍼 함수 없음)
리듀서: 여러 노드에서 동일한 state 필드를 업데이트할 때 값을 어떻게 합칠지 결정
"""

from typing import TypedDict, Annotated, List, Dict, Any
from operator import add
from langgraph.graph import StateGraph, END
import json

print("=" * 60)
print("1. 기본 리듀서 예시들 (헬퍼 함수 없음)")
print("=" * 60)

# ========================================
# 예시 1: add 리듀서 - 리스트에 요소 추가
# ========================================
print("\n### 예시 1: add 리듀서 (리스트 누적)")

class ChatState(TypedDict):
    messages: Annotated[List[str], add]  # 메시지들이 계속 누적됨
    
def user_node(state: ChatState) -> Dict:
    return {"messages": ["안녕하세요"]}

def assistant_node(state: ChatState) -> Dict:
    return {"messages": ["반갑습니다"]}

def summary_node(state: ChatState) -> Dict:
    return {"messages": ["대화가 끝났습니다"]}

# 그래프 생성 및 실행
workflow = StateGraph(ChatState)
workflow.add_node("user", user_node)
workflow.add_node("assistant", assistant_node)
workflow.add_node("summary", summary_node)

workflow.set_entry_point("user")
workflow.add_edge("user", "assistant")
workflow.add_edge("assistant", "summary")
workflow.add_edge("summary", END)

app = workflow.compile()
result = app.invoke({"messages": ["대화 시작"]})
print(f"최종 messages: {result['messages']}")
print("→ add 리듀서로 모든 메시지가 누적됨")

# ========================================
# 예시 2: 덮어쓰기 (기본 동작)
# ========================================
print("\n### 예시 2: 기본 리듀서 (마지막 값으로 덮어쓰기)")

class ConfigState(TypedDict):
    temperature: float  # 리듀서 없음 = 덮어쓰기
    model: str

def init_node(state: ConfigState) -> Dict:
    return {"temperature": 0.7, "model": "gpt-3.5"}

def update_node(state: ConfigState) -> Dict:
    return {"temperature": 0.9}  # model은 안 바꿈

def final_node(state: ConfigState) -> Dict:
    return {"temperature": 0.5, "model": "gpt-4"}

workflow2 = StateGraph(ConfigState)
workflow2.add_node("init", init_node)
workflow2.add_node("update", update_node)
workflow2.add_node("final", final_node)

workflow2.set_entry_point("init")
workflow2.add_edge("init", "update")
workflow2.add_edge("update", "final")
workflow2.add_edge("final", END)

app2 = workflow2.compile()
result2 = app2.invoke({"temperature": 1.0, "model": "claude"})
print(f"최종 state: {result2}")
print("→ 각 노드가 반환한 값으로 계속 덮어씀")

# ========================================
# 예시 3: 커스텀 리듀서 - 최대값 선택
# ========================================
print("\n### 예시 3: 커스텀 리듀서 (최대값 선택)")

def max_reducer(current: float, new: float) -> float:
    """더 큰 값을 선택하는 리듀서"""
    if current is None:
        return new
    return max(current, new)

class ScoreState(TypedDict):
    score: Annotated[float, max_reducer]
    attempts: Annotated[List[int], add]  # 시도 횟수는 누적

def attempt1(state: ScoreState) -> Dict:
    return {"score": 75.5, "attempts": [1]}

def attempt2(state: ScoreState) -> Dict:
    return {"score": 82.3, "attempts": [1]}

def attempt3(state: ScoreState) -> Dict:
    return {"score": 79.1, "attempts": [1]}

workflow3 = StateGraph(ScoreState)
workflow3.add_node("attempt1", attempt1)
workflow3.add_node("attempt2", attempt2)
workflow3.add_node("attempt3", attempt3)

workflow3.set_entry_point("attempt1")
workflow3.add_edge("attempt1", "attempt2")
workflow3.add_edge("attempt2", "attempt3")
workflow3.add_edge("attempt3", END)

app3 = workflow3.compile()
result3 = app3.invoke({"score": 0.0, "attempts": []})
print(f"최종 점수: {result3['score']}, 시도 횟수: {len(result3['attempts'])}")
print("→ 최대 점수만 보존, 시도 횟수는 누적")

# ========================================
# 예시 4: 딕셔너리 병합 리듀서
# ========================================
print("\n### 예시 4: 딕셔너리 병합 리듀서")

def merge_dict_reducer(current: Dict, new: Dict) -> Dict:
    """딕셔너리를 병합하는 리듀서"""
    if current is None:
        return new
    result = current.copy()
    result.update(new)
    return result

class DataState(TypedDict):
    metadata: Annotated[Dict[str, Any], merge_dict_reducer]
    
def collect_user_data(state: DataState) -> Dict:
    return {"metadata": {"user_id": "123", "name": "홍길동"}}

def collect_session_data(state: DataState) -> Dict:
    return {"metadata": {"session_id": "abc", "timestamp": "2024-01-01"}}

def collect_device_data(state: DataState) -> Dict:
    return {"metadata": {"device": "mobile", "os": "iOS"}}

workflow4 = StateGraph(DataState)
workflow4.add_node("user", collect_user_data)
workflow4.add_node("session", collect_session_data)
workflow4.add_node("device", collect_device_data)

workflow4.set_entry_point("user")
workflow4.add_edge("user", "session")
workflow4.add_edge("session", "device")
workflow4.add_edge("device", END)

app4 = workflow4.compile()
result4 = app4.invoke({"metadata": {}})
print(f"병합된 메타데이터: {json.dumps(result4['metadata'], ensure_ascii=False, indent=2)}")
print("→ 모든 딕셔너리가 하나로 병합됨")

# ========================================
# 예시 5: 중복 제거 리듀서
# ========================================
print("\n### 예시 5: 중복 제거 리듀서 (Set 활용)")

def unique_list_reducer(current: List, new: List) -> List:
    """중복을 제거하면서 리스트를 합치는 리듀서"""
    if current is None:
        current = []
    # set으로 중복 제거 후 다시 리스트로
    combined = list(set(current + new))
    return sorted(combined)  # 정렬해서 반환

class TagState(TypedDict):
    tags: Annotated[List[str], unique_list_reducer]
    
def tag_node1(state: TagState) -> Dict:
    return {"tags": ["python", "ai", "ml"]}

def tag_node2(state: TagState) -> Dict:
    return {"tags": ["python", "deep-learning", "ai"]}

def tag_node3(state: TagState) -> Dict:
    return {"tags": ["nlp", "ml", "transformers"]}

workflow5 = StateGraph(TagState)
workflow5.add_node("tagger1", tag_node1)
workflow5.add_node("tagger2", tag_node2)
workflow5.add_node("tagger3", tag_node3)

workflow5.set_entry_point("tagger1")
workflow5.add_edge("tagger1", "tagger2")
workflow5.add_edge("tagger2", "tagger3")
workflow5.add_edge("tagger3", END)

app5 = workflow5.compile()
result5 = app5.invoke({"tags": []})
print(f"고유 태그들: {result5['tags']}")
print("→ 중복 제거되고 정렬된 태그 목록")

# ========================================
# 예시 6: 카운터 리듀서
# ========================================
print("\n### 예시 6: 카운터 리듀서 (빈도수 계산)")

def counter_reducer(current: Dict[str, int], new: Dict[str, int]) -> Dict[str, int]:
    """각 항목의 빈도수를 누적하는 리듀서"""
    if current is None:
        current = {}
    result = current.copy()
    for key, value in new.items():
        result[key] = result.get(key, 0) + value
    return result

class AnalyticsState(TypedDict):
    word_count: Annotated[Dict[str, int], counter_reducer]
    
def analyze_text1(state: AnalyticsState) -> Dict:
    return {"word_count": {"python": 3, "code": 2, "ai": 1}}

def analyze_text2(state: AnalyticsState) -> Dict:
    return {"word_count": {"python": 1, "ml": 2, "ai": 2}}

def analyze_text3(state: AnalyticsState) -> Dict:
    return {"word_count": {"code": 1, "ml": 1, "data": 3}}

workflow6 = StateGraph(AnalyticsState)
workflow6.add_node("analyze1", analyze_text1)
workflow6.add_node("analyze2", analyze_text2)
workflow6.add_node("analyze3", analyze_text3)

workflow6.set_entry_point("analyze1")
workflow6.add_edge("analyze1", "analyze2")
workflow6.add_edge("analyze2", "analyze3")
workflow6.add_edge("analyze3", END)

app6 = workflow6.compile()
result6 = app6.invoke({"word_count": {}})
print(f"단어 빈도수: {json.dumps(result6['word_count'], indent=2)}")
print("→ 각 단어의 출현 횟수가 누적됨")

print("\n" + "=" * 60)
print("💡 리듀서 없는 버전의 특징:")
print("- 각 리듀서 로직을 직접 구현")
print("- 단순하지만 반복 코드가 많음")
print("- 타입 힌트로 리듀서 함수 지정")
print("=" * 60)
