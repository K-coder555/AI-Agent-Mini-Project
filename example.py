"""
Physical AI Report Generator - Quick Start Example

이 예제는 Physical AI 트렌드 보고서를 생성하는 가장 간단한 방법을 보여줍니다.
"""

from physical_ai_agent import run_agent

def main():
    """메인 실행 함수"""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║         Physical AI 트렌드 보고서 생성 에이전트              ║
║              Powered by LangGraph + Tavily                   ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 1. 기본 사용법
    query = "향후 5년 이내 기업에서 관심있게 봐야할 Physical AI 트렌드"
    result = run_agent(query)
    
    # 2. 결과 확인
    if result:
        print(f"\n✅ 보고서 생성 성공!")
        print(f"📈 품질 점수: {result['quality_score']}/10")
        print(f"🔄 반복 횟수: {result['iteration_count']}")
        print(f"📄 생성된 PDF 파일을 확인하세요.")
    else:
        print("\n❌ 보고서 생성 실패. API 키를 확인하세요.")


def custom_query_example():
    """커스텀 쿼리 예제"""
    
    # 다양한 쿼리 예제
    queries = [
        "헬스케어 분야의 Physical AI 활용 사례",
        "제조업에서의 AI 로봇 통합 트렌드",
        "Physical AI 시장의 주요 기업 분석",
        "AI 기반 자율주행 물류 로봇 전망"
    ]
    
    # 원하는 쿼리 선택
    selected_query = queries[0]
    result = run_agent(selected_query)
    
    return result


def advanced_usage_example():
    """고급 사용 예제"""
    
    from physical_ai_agent import create_physical_ai_agent
    
    # 에이전트 생성
    agent = create_physical_ai_agent()
    
    # 초기 상태 커스터마이징
    initial_state = {
        "user_query": "Physical AI 트렌드 심층 분석",
        "research_plan": {},
        "market_data": [],
        "tech_data": [],
        "industry_data": [],
        "company_data": [],
        "challenge_data": [],
        "synthesized_data": {},
        "report_sections": {},
        "final_report": "",
        "quality_score": 0.0,
        "iteration_count": 0,
        "search_context": {},
        "messages": []
    }
    
    # 실행
    result = agent.invoke(initial_state)
    
    # 중간 결과 확인
    print(f"시장 데이터 개수: {len(result['market_data'])}")
    print(f"기술 데이터 개수: {len(result['tech_data'])}")
    print(f"산업 데이터 개수: {len(result['industry_data'])}")
    
    return result


if __name__ == "__main__":
    # 환경 변수 확인
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("📝 .env 파일을 생성하고 API 키를 입력하세요.")
        exit(1)
    
    if not os.getenv("TAVILY_API_KEY"):
        print("⚠️ TAVILY_API_KEY가 설정되지 않았습니다.")
        print("📝 .env 파일을 생성하고 API 키를 입력하세요.")
        exit(1)
    
    # 기본 실행
    main()
    
    # 또는 고급 사용법
    # advanced_usage_example()
