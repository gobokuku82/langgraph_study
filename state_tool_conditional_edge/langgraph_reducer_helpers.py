"""
LangGraph State 리듀서 예시 - 헬퍼 함수 활용 버전
헬퍼 함수를 사용하여 더 복잡하고 재사용 가능한 리듀서 패턴 구현
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional, Union
from operator import add
from langgraph.graph import StateGraph, END
from datetime import datetime
import json

print("=" * 60)
print("2. 헬퍼 함수를 활용한 고급 리듀서 패턴")
print("=" * 60)

# ========================================
# 헬퍼 함수들 정의
# ========================================

class ReducerHelpers:
    """재사용 가능한 리듀서 헬퍼 함수 모음"""
    
    @staticmethod
    def create_windowed_reducer(window_size: int):
        """최근 N개 항목만 유지하는 리듀서 생성"""
        def windowed_reducer(current: List, new: List) -> List:
            if current is None:
                current = []
            combined = current + new
            return combined[-window_size:]  # 마지막 N개만 유지
        return windowed_reducer
    
    @staticmethod
    def create_filtered_reducer(filter_func):
        """조건에 맞는 항목만 추가하는 리듀서 생성"""
        def filtered_reducer(current: List, new: List) -> List:
            if current is None:
                current = []
            filtered_new = [item for item in new if filter_func(item)]
            return current + filtered_new
        return filtered_reducer
    
    @staticmethod
    def create_averaged_reducer(weight: float = 0.5):
        """가중 평균을 계산하는 리듀서 생성"""
        def averaged_reducer(current: float, new: float) -> float:
            if current is None:
                return new
            return current * (1 - weight) + new * weight
        return averaged_reducer
    
    @staticmethod
    def create_validated_reducer(validator):
        """유효성 검사를 통과한 값만 업데이트하는 리듀서"""
        def validated_reducer(current: Any, new: Any) -> Any:
            if validator(new):
                return new
            return current if current is not None else new
        return validated_reducer
    
    @staticmethod
    def create_timestamped_reducer():
        """타임스탬프와 함께 저장하는 리듀서"""
        def timestamped_reducer(current: List[Dict], new: Any) -> List[Dict]:
            if current is None:
                current = []
            timestamped_items = []
            
            # new가 리스트가 아니면 리스트로 변환
            items = new if isinstance(new, list) else [new]
            
            for item in items:
                timestamped_items.append({
                    "value": item,
                    "timestamp": datetime.now().isoformat()
                })
            
            return current + timestamped_items
        return timestamped_reducer

# ========================================
# 예시 1: 윈도우 리듀서 (최근 N개만 유지)
# ========================================
print("\n### 예시 1: 윈도우 리듀서 (최근 3개 메시지만 유지)")

# 최근 3개만 유지하는 리듀서 생성
recent_messages_reducer = ReducerHelpers.create_windowed_reducer(window_size=3)

class ChatWindowState(TypedDict):
    recent_messages: Annotated[List[str], recent_messages_reducer]
    all_count: Annotated[List[int], add]  # 전체 메시지 수는 계속 카운트

def message_node(i: int):
    def node(state: ChatWindowState) -> Dict:
        return {
            "recent_messages": [f"메시지 {i}"],
            "all_count": [1]
        }
    return node

workflow1 = StateGraph(ChatWindowState)
for i in range(1, 6):
    workflow1.add_node(f"msg{i}", message_node(i))

workflow1.set_entry_point("msg1")
for i in range(1, 5):
    workflow1.add_edge(f"msg{i}", f"msg{i+1}")
workflow1.add_edge("msg5", END)

app1 = workflow1.compile()
result1 = app1.invoke({"recent_messages": [], "all_count": []})
print(f"최근 메시지 (3개만): {result1['recent_messages']}")
print(f"전체 메시지 수: {len(result1['all_count'])}")

# ========================================
# 예시 2: 필터링 리듀서 (조건에 맞는 것만 추가)
# ========================================
print("\n### 예시 2: 필터링 리듀서 (점수 70 이상만 저장)")

# 70점 이상만 통과시키는 필터
high_score_filter = lambda score: score >= 70
high_scores_reducer = ReducerHelpers.create_filtered_reducer(high_score_filter)

class ExamState(TypedDict):
    high_scores: Annotated[List[int], high_scores_reducer]
    all_scores: Annotated[List[int], add]

def exam_node(score: int):
    def node(state: ExamState) -> Dict:
        return {
            "high_scores": [score],
            "all_scores": [score]
        }
    return node

workflow2 = StateGraph(ExamState)
scores = [65, 82, 58, 91, 73, 45, 88]
for i, score in enumerate(scores):
    workflow2.add_node(f"exam{i}", exam_node(score))

workflow2.set_entry_point("exam0")
for i in range(len(scores) - 1):
    workflow2.add_edge(f"exam{i}", f"exam{i+1}")
workflow2.add_edge(f"exam{len(scores)-1}", END)

app2 = workflow2.compile()
result2 = app2.invoke({"high_scores": [], "all_scores": []})
print(f"높은 점수들 (70+): {result2['high_scores']}")
print(f"모든 점수: {result2['all_scores']}")

# ========================================
# 예시 3: 가중 평균 리듀서
# ========================================
print("\n### 예시 3: 가중 평균 리듀서 (신뢰도 점수 계산)")

# 30% 가중치로 새 값을 반영
confidence_reducer = ReducerHelpers.create_averaged_reducer(weight=0.3)

class ConfidenceState(TypedDict):
    confidence: Annotated[float, confidence_reducer]
    measurements: Annotated[List[float], add]

def measure_node(value: float):
    def node(state: ConfidenceState) -> Dict:
        return {
            "confidence": value,
            "measurements": [value]
        }
    return node

workflow3 = StateGraph(ConfidenceState)
measurements = [0.8, 0.85, 0.75, 0.9, 0.82]
for i, value in enumerate(measurements):
    workflow3.add_node(f"measure{i}", measure_node(value))

workflow3.set_entry_point("measure0")
for i in range(len(measurements) - 1):
    workflow3.add_edge(f"measure{i}", f"measure{i+1}")
workflow3.add_edge(f"measure{len(measurements)-1}", END)

app3 = workflow3.compile()
result3 = app3.invoke({"confidence": 0.0, "measurements": []})
print(f"가중 평균 신뢰도: {result3['confidence']:.3f}")
print(f"모든 측정값: {[f'{m:.2f}' for m in result3['measurements']]}")

# ========================================
# 예시 4: 유효성 검증 리듀서
# ========================================
print("\n### 예시 4: 유효성 검증 리듀서 (이메일 형식 검증)")

# 간단한 이메일 검증 함수
email_validator = lambda email: "@" in email and "." in email
validated_email_reducer = ReducerHelpers.create_validated_reducer(email_validator)

class UserState(TypedDict):
    email: Annotated[str, validated_email_reducer]
    attempts: Annotated[List[str], add]

def email_input_node(email: str):
    def node(state: UserState) -> Dict:
        return {
            "email": email,
            "attempts": [email]
        }
    return node

workflow4 = StateGraph(UserState)
email_attempts = ["invalid", "user@", "user@example.com", "another-invalid", "backup@email.org"]
for i, email in enumerate(email_attempts):
    workflow4.add_node(f"input{i}", email_input_node(email))

workflow4.set_entry_point("input0")
for i in range(len(email_attempts) - 1):
    workflow4.add_edge(f"input{i}", f"input{i+1}")
workflow4.add_edge(f"input{len(email_attempts)-1}", END)

app4 = workflow4.compile()
result4 = app4.invoke({"email": "", "attempts": []})
print(f"최종 유효 이메일: {result4['email']}")
print(f"모든 시도: {result4['attempts']}")

# ========================================
# 예시 5: 타임스탬프 리듀서
# ========================================
print("\n### 예시 5: 타임스탬프 리듀서 (이벤트 로깅)")

timestamped_reducer = ReducerHelpers.create_timestamped_reducer()

class EventState(TypedDict):
    events: Annotated[List[Dict], timestamped_reducer]

def event_node(event_name: str):
    def node(state: EventState) -> Dict:
        return {"events": event_name}
    return node

workflow5 = StateGraph(EventState)
events = ["user_login", "page_view", "button_click", "form_submit"]
for i, event in enumerate(events):
    workflow5.add_node(f"event{i}", event_node(event))

workflow5.set_entry_point("event0")
for i in range(len(events) - 1):
    workflow5.add_edge(f"event{i}", f"event{i+1}")
workflow5.add_edge(f"event{len(events)-1}", END)

app5 = workflow5.compile()
result5 = app5.invoke({"events": []})
print(f"타임스탬프된 이벤트:")
for event in result5['events']:
    print(f"  - {event['value']}: {event['timestamp']}")

# ========================================
# 예시 6: 복합 헬퍼 - 우선순위 큐 리듀서
# ========================================
print("\n### 예시 6: 복합 헬퍼 - 우선순위 큐 리듀서")

class PriorityQueueHelper:
    @staticmethod
    def create_priority_queue_reducer(max_size: int = 5):
        """우선순위 큐 리듀서 (높은 우선순위 N개만 유지)"""
        def priority_reducer(current: List[Dict], new: List[Dict]) -> List[Dict]:
            if current is None:
                current = []
            combined = current + new
            # 우선순위로 정렬 후 상위 N개만 유지
            sorted_items = sorted(combined, key=lambda x: x.get('priority', 0), reverse=True)
            return sorted_items[:max_size]
        return priority_reducer

priority_reducer = PriorityQueueHelper.create_priority_queue_reducer(max_size=3)

class TaskState(TypedDict):
    priority_tasks: Annotated[List[Dict], priority_reducer]

def task_node(name: str, priority: int):
    def node(state: TaskState) -> Dict:
        return {
            "priority_tasks": [{
                "name": name,
                "priority": priority
            }]
        }
    return node

workflow6 = StateGraph(TaskState)
tasks = [
    ("Task A", 5), ("Task B", 8), ("Task C", 3), 
    ("Task D", 9), ("Task E", 6), ("Task F", 10)
]

for i, (name, priority) in enumerate(tasks):
    workflow6.add_node(f"task{i}", task_node(name, priority))

workflow6.set_entry_point("task0")
for i in range(len(tasks) - 1):
    workflow6.add_edge(f"task{i}", f"task{i+1}")
workflow6.add_edge(f"task{len(tasks)-1}", END)

app6 = workflow6.compile()
result6 = app6.invoke({"priority_tasks": []})
print(f"상위 3개 우선순위 작업:")
for task in result6['priority_tasks']:
    print(f"  - {task['name']}: 우선순위 {task['priority']}")

# ========================================
# 예시 7: 체이닝 가능한 헬퍼 조합
# ========================================
print("\n### 예시 7: 헬퍼 함수 조합 (필터링 + 윈도우)")

class ComposableReducers:
    @staticmethod
    def compose(*reducers):
        """여러 리듀서를 조합하는 헬퍼"""
        def composed_reducer(current, new):
            result = new
            for reducer in reducers:
                result = reducer(current, result)
                current = result
            return result
        return composed_reducer

# 점수 80 이상 필터 + 최근 2개만 유지
high_score_filter_reducer = ReducerHelpers.create_filtered_reducer(lambda x: x >= 80)
recent_window_reducer = ReducerHelpers.create_windowed_reducer(2)

# 두 리듀서 조합
composed_reducer = ComposableReducers.compose(
    high_score_filter_reducer,
    recent_window_reducer
)

class FilteredWindowState(TypedDict):
    top_recent: Annotated[List[int], composed_reducer]

def score_node(score: int):
    def node(state: FilteredWindowState) -> Dict:
        return {"top_recent": [score]}
    return node

workflow7 = StateGraph(FilteredWindowState)
scores = [75, 85, 90, 70, 88, 95, 60, 92]
for i, score in enumerate(scores):
    workflow7.add_node(f"score{i}", score_node(score))

workflow7.set_entry_point("score0")
for i in range(len(scores) - 1):
    workflow7.add_edge(f"score{i}", f"score{i+1}")
workflow7.add_edge(f"score{len(scores)-1}", END)

app7 = workflow7.compile()
result7 = app7.invoke({"top_recent": []})
print(f"최근 높은 점수 2개 (80+): {result7['top_recent']}")

print("\n" + "=" * 60)
print("💡 헬퍼 함수 활용의 장점:")
print("- 복잡한 리듀서 로직을 재사용 가능")
print("- 파라미터화로 유연한 설정 가능")
print("- 리듀서 조합으로 복잡한 상태 관리 구현")
print("- 테스트와 유지보수가 용이")
print("=" * 60)
