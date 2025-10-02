from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

# 1. 기본 tool 정의
@tool
def add(a: int, b: int) -> int:
    """두 숫자를 더합니다."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """두 숫자를 곱합니다."""
    return a * b

@tool
def get_weather(city: str) -> str:
    """도시의 날씨를 조회합니다."""
    weather_data = {
        "서울": "맑음, 15도",
        "부산": "흐림, 18도",
        "제주": "비, 20도"
    }
    return weather_data.get(city, "날씨 정보 없음")

@tool
def search_product(keyword: str, max_price: int = 50000) -> list:
    """키워드로 상품을 검색합니다."""
    products = [
        {"name": f"{keyword} 제품 A", "price": 30000},
        {"name": f"{keyword} 제품 B", "price": 45000},
        {"name": f"{keyword} 제품 C", "price": 60000}
    ]
    return [p for p in products if p["price"] <= max_price]


# 2. LLM에 tool 바인딩
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
tools = [add, multiply, get_weather, search_product]
llm_with_tools = llm.bind_tools(tools)


# 케이스 1: 단일 tool 호출
print("=== 케이스 1: 단일 tool 호출 ===")
messages = [HumanMessage(content="5 더하기 3은?")]
ai_msg = llm_with_tools.invoke(messages)
print(f"AI 응답: {ai_msg.tool_calls}")

if ai_msg.tool_calls:
    for tool_call in ai_msg.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        selected_tool = {t.name: t for t in tools}[tool_name]
        result = selected_tool.invoke(tool_args)
        print(f"Tool 실행 결과: {result}")


# 케이스 2: 다중 tool 호출
print("\n=== 케이스 2: 다중 tool 호출 ===")
messages = [HumanMessage(content="10 더하기 5는? 그리고 3 곱하기 4는?")]
ai_msg = llm_with_tools.invoke(messages)
print(f"호출된 tool 수: {len(ai_msg.tool_calls)}")

for tool_call in ai_msg.tool_calls:
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    selected_tool = {t.name: t for t in tools}[tool_name]
    result = selected_tool.invoke(tool_args)
    print(f"{tool_name}({tool_args}) = {result}")


# 케이스 3: 컨텍스트가 필요한 경우
print("\n=== 케이스 3: 대화 컨텍스트 유지 ===")
messages = [HumanMessage(content="서울 날씨 알려줘")]
ai_msg = llm_with_tools.invoke(messages)

messages.append(ai_msg)
for tool_call in ai_msg.tool_calls:
    selected_tool = {t.name: t for t in tools}[tool_call["name"]]
    result = selected_tool.invoke(tool_call["args"])
    messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))

final_response = llm_with_tools.invoke(messages)
print(f"최종 답변: {final_response.content}")


# 케이스 4: 선택적 파라미터
print("\n=== 케이스 4: 선택적 파라미터 ===")
messages = [HumanMessage(content="노트북을 4만원 이하로 검색해줘")]
ai_msg = llm_with_tools.invoke(messages)

for tool_call in ai_msg.tool_calls:
    selected_tool = {t.name: t for t in tools}[tool_call["name"]]
    result = selected_tool.invoke(tool_call["args"])
    print(f"검색 결과: {result}")


# 케이스 5: tool 없이 답변 가능한 경우
print("\n=== 케이스 5: tool 필요 없는 질문 ===")
messages = [HumanMessage(content="안녕하세요!")]
ai_msg = llm_with_tools.invoke(messages)
print(f"Tool 호출 여부: {len(ai_msg.tool_calls) > 0}")
print(f"직접 답변: {ai_msg.content}")