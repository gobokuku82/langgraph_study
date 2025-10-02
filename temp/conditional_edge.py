# LangGraph 및 필수 라이브러리 임포트
from langgraph.graph import StateGraph, START, END

# ==============================================================================
# 예시 1: 함수 내 경로 설정 (판단과 경로 반환을 한 번에)
# ==============================================================================
def run_example_1_path_in_function():
    """
    분기 함수가 다음에 가야 할 노드의 '이름 자체'를 직접 반환하는 방식입니다.
    """
    print("\n--- 예시 1: 함수 내 경로 설정 실행 ---")

    # 분기 함수가 직접 목적지 노드 이름을 반환
    def check_status(state: dict) -> str:
        """상태를 확인하고, 다음 노드 이름을 직접 반환합니다."""
        print(f"상태 확인: {state['status']}")
        if state["status"] == "success":
            return "success_node"  # 성공 시 'success_node'로 가라고 지정
        else:
            return "failure_node"  # 실패 시 'failure_node'로 가라고 지정

    # 그래프 설정
    graph = StateGraph(dict)
    graph.add_node("check_status_node", lambda state: state)
    graph.add_node("success_node", lambda state: print(">> 경로: 성공!"))
    graph.add_node("failure_node", lambda state: print(">> 경로: 실패!"))
    graph.add_edge(START, "check_status_node")

    # 판단 함수(check_status)의 반환값 자체가 목적지가 됨
    graph.add_conditional_edges(
        "check_status_node",
        check_status
    )

    # 실행
    app = graph.compile()
    print("'success' 상태로 실행합니다.")
    app.invoke({"status": "success"})
    print("'failure' 상태로 실행합니다.")
    app.invoke({"status": "failure"})


# ==============================================================================
# 예시 2: 함수 외 경로 설정 (판단과 경로 매핑을 분리)
# ==============================================================================
def run_example_2_path_map_outside():
    """
    분기 함수는 '상태 키'만 반환하고, 실제 경로는 외부에 정의된 '딕셔너리'가 결정하는 방식입니다.
    """
    print("\n--- 예시 2: 함수 외 경로 설정 실행 ---")

    # 분기 함수는 '상태 키'만 반환
    def should_proceed(state: dict) -> str:
        """진행 여부를 판단하여 '키'를 반환합니다."""
        print(f"현재 단계: {state['steps_completed']}")
        if state["steps_completed"] < 3:
            return "proceed"  # '진행' 이라는 키 반환
        else:
            return "stop"     # '중단' 이라는 키 반환

    # 그래프 설정
    graph = StateGraph(dict)
    # process_step 노드는 실행될 때마다 steps_completed를 1씩 증가시킴
    graph.add_node("process_step", lambda state: {"steps_completed": state.get("steps_completed", 0) + 1})

    # 경로 맵 딕셔너리: 함수가 반환한 키와 실제 목적지를 연결
    path_map = {
        "proceed": "process_step", # 'proceed' 키는 'process_step' 노드로 다시 돌아감 (루프)
        "stop": END                # 'stop' 키는 종료(END)로
    }

    graph.add_edge(START, "process_step")

    # 함수와 경로 맵을 분리하여 전달
    graph.add_conditional_edges(
        "process_step",
        should_proceed,
        path_map
    )

    # 실행
    app = graph.compile()
    print("루프를 3번 실행하고 종료합니다.")
    app.invoke({"steps_completed": 0})
    print(">> 최종 종료 완료")


# ==============================================================================
# 예시 3: 키워드 인자 함수 (가독성을 높인 방식)
# ==============================================================================
def run_example_3_keyword_args():
    """
    예시 2와 기능은 동일하지만, 키워드 인자를 사용해 각 매개변수의 역할을 명시하는 방식입니다.
    """
    print("\n--- 예시 3: 키워드 인자 함수 실행 ---")

    # (예시 2와 동일한 함수 및 딕셔너리)
    def should_proceed(state: dict) -> str:
        print(f"현재 단계: {state['steps_completed']}")
        if state["steps_completed"] < 3:
            return "proceed"
        else:
            return "stop"
    path_map = {"proceed": "process_step", "stop": END}

    # 그래프 설정
    graph = StateGraph(dict)
    graph.add_node("process_step", lambda state: {"steps_completed": state.get("steps_completed", 0) + 1})
    graph.add_edge(START, "process_step")

    # 키워드 인자(start_key, path, path_map)를 사용하여 각 매개변수의 역할을 명시
    graph.add_conditional_edges(
        start_key="process_step", # 시작 노드임을 명시
        path=should_proceed,      # 판단 함수임을 명시
        path_map=path_map         # 경로 맵임을 명시
    )

    # 실행
    app = graph.compile()
    print("루프를 3번 실행하고 종료합니다.")
    app.invoke({"steps_completed": 0})
    print(">> 최종 종료 완료")


# ==============================================================================
# 메인 실행 블록
# ==============================================================================
if __name__ == "__main__":
    # 아래 세 가지 예시 중, 실행하고 싶은 함수의 주석을 해제하고 실행하세요.
    # 하나만 주석 해제해야 정상적으로 보입니다.

    run_example_1_path_in_function()
    # run_example_2_path_map_outside()
    # run_example_3_keyword_args()

"""
  graph.add_conditional_edges(
        start_key="process_step", # 시작 노드임을 명시
        path=should_proceed,      # 판단 함수임을 명시
        path_map=path_map         # 경로 맵임을 명시
    )
"""

"""
path_map = {
        "proceed": "process_step", 
        "stop": END                
    }

    graph.add_conditional_edges(
        "process_step",
        should_proceed,
        path_map
    )
"""

"""
    graph.add_conditional_edges
    (
        "process_step",
        should_proceed,
        {"proceed":"process_step" , "stop": END }
    )

"""

