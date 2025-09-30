# LangGraph 리듀서(Reducer) 완벽 가이드

## 🎯 리듀서란?
리듀서는 여러 노드가 동일한 state 필드를 업데이트할 때, 그 값들을 어떻게 합칠지 결정하는 함수입니다.

## 📌 리듀서의 중요성

### 1. **상태 충돌 해결**
```python
# 리듀서 없이: 마지막 값으로 덮어쓰기
state["messages"] = "안녕"  # node1
state["messages"] = "반가워"  # node2
# 결과: "반가워" (이전 값 손실!)

# 리듀서 사용: 값 누적
messages: Annotated[List[str], add]
# 결과: ["안녕", "반가워"] (모든 값 보존!)
```

### 2. **복잡한 상태 관리**
- 메시지 히스토리 관리
- 점수/통계 집계
- 이벤트 로깅
- 데이터 필터링 및 검증

## 📊 기본 리듀서 vs 헬퍼 함수 리듀서

### 기본 리듀서 (간단한 경우)
```python
# 1. add - 리스트/숫자 누적
messages: Annotated[List[str], add]

# 2. 커스텀 리듀서 - 직접 정의
def max_reducer(current, new):
    return max(current, new)
score: Annotated[float, max_reducer]
```

**장점:**
- 단순하고 직관적
- 빠른 프로토타이핑
- 성능 오버헤드 최소

**단점:**
- 재사용성 낮음
- 복잡한 로직 구현 어려움

### 헬퍼 함수 리듀서 (복잡한 경우)
```python
# 파라미터화된 리듀서 생성
def create_windowed_reducer(window_size):
    def reducer(current, new):
        return (current + new)[-window_size:]
    return reducer

# 사용
recent_3 = create_windowed_reducer(3)
messages: Annotated[List, recent_3]
```

**장점:**
- 높은 재사용성
- 파라미터로 동작 커스터마이즈
- 복잡한 로직을 깔끔하게 구현
- 리듀서 조합 가능

**단점:**
- 초기 설정 복잡
- 약간의 성능 오버헤드

## 🔥 실전 활용 패턴

### 1. **채팅 애플리케이션**
```python
# 최근 N개 메시지만 유지 (메모리 절약)
recent_messages: Annotated[List, create_windowed_reducer(10)]
# 전체 카운트는 유지
total_count: Annotated[int, add]
```

### 2. **데이터 파이프라인**
```python
# 유효한 데이터만 필터링
valid_data: Annotated[List, create_filtered_reducer(validator)]
# 에러는 모두 수집
errors: Annotated[List, add]
```

### 3. **ML 모델 신뢰도**
```python
# 가중 평균으로 신뢰도 계산
confidence: Annotated[float, create_averaged_reducer(0.3)]
```

### 4. **이벤트 소싱**
```python
# 타임스탬프와 함께 모든 이벤트 기록
events: Annotated[List, timestamped_reducer]
```

## 💡 선택 가이드

### 기본 리듀서를 사용하세요:
- ✅ 단순한 값 누적/덮어쓰기
- ✅ 프로토타입 개발
- ✅ 성능이 매우 중요한 경우

### 헬퍼 함수 리듀서를 사용하세요:
- ✅ 복잡한 비즈니스 로직
- ✅ 재사용이 필요한 패턴
- ✅ 파라미터화가 필요한 경우
- ✅ 여러 리듀서 조합이 필요한 경우

## 🎓 핵심 요약

1. **리듀서는 State 관리의 핵심**: 여러 노드의 출력을 어떻게 합칠지 결정
2. **기본 vs 헬퍼**: 간단한 작업은 기본, 복잡한 작업은 헬퍼
3. **성능 vs 유지보수**: 트레이드오프를 고려하여 선택
4. **조합 가능성**: 헬퍼 함수로 복잡한 리듀서도 깔끔하게 구현

리듀서를 잘 활용하면 복잡한 상태 관리도 깔끔하고 예측 가능하게 만들 수 있습니다!
