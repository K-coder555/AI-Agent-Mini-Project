# 프로젝트 구조

Physical AI Report Generator 프로젝트의 파일 구조와 각 파일의 역할을 설명합니다.

## 디렉토리 구조

```
physical-ai-report-generator/
│
├── physical_ai_agent.py          # 메인 에이전트 코드
├── example.py                     # 사용 예제
├── requirements.txt               # Python 패키지 의존성
├── .env.example                   # 환경 변수 템플릿
├── .gitignore                     # Git 제외 파일 목록
├── LICENSE                        # MIT 라이선스
├── README.md                      # 프로젝트 소개 및 사용법
├── CONTRIBUTING.md                # 기여 가이드
│
├── docs/                          # 문서 디렉토리
│   ├── architecture.md            # 아키텍처 설명
│   ├── api_reference.md           # API 레퍼런스
│   └── images/                    # 이미지 파일
│       ├── sample_report_page1.png
│       └── workflow_diagram.png
│
├── tests/                         # 테스트 코드
│   ├── __init__.py
│   ├── test_nodes.py              # 노드 단위 테스트
│   ├── test_synthesis.py          # 데이터 종합 테스트
│   ├── test_pdf_generation.py     # PDF 생성 테스트
│   └── test_integration.py        # 통합 테스트
│
├── outputs/                       # 생성된 보고서 저장
│   └── .gitkeep
│
└── utils/                         # 유틸리티 함수
    ├── __init__.py
    ├── pdf_utils.py               # PDF 생성 유틸리티
    ├── search_utils.py            # 검색 유틸리티
    └── text_processing.py         # 텍스트 처리 유틸리티
```

## 주요 파일 설명

### `physical_ai_agent.py`

메인 에이전트 코드로, 다음 컴포넌트를 포함합니다:

```python
# 1. 상태 정의
class AgentState(TypedDict):
    user_query: str
    market_data: List[Dict]
    # ... 기타 상태 필드

# 2. 노드 함수들
def planning_node(state: AgentState) -> AgentState:
    """조사 계획 수립"""
    
def market_research_node(state: AgentState) -> AgentState:
    """시장 조사"""
    
# ... 기타 노드

# 3. 그래프 구성
def create_physical_ai_agent():
    """LangGraph 워크플로우 생성"""
    workflow = StateGraph(AgentState)
    # 노드 및 엣지 추가
    return workflow.compile()

# 4. 실행 함수
def run_agent(user_query: str):
    """에이전트 실행 및 보고서 생성"""
```

### `example.py`

사용 예제 코드:

```python
# 기본 사용법
def main():
    query = "Physical AI 트렌드"
    result = run_agent(query)

# 고급 사용법
def advanced_usage_example():
    agent = create_physical_ai_agent()
    result = agent.invoke(initial_state)
```

### `requirements.txt`

프로젝트 의존성 패키지 목록:

```
langchain>=0.1.0
langgraph>=0.0.20
tavily-python>=0.3.0
reportlab>=4.0.0
# ... 기타 패키지
```

## 코드 구조 상세

### 1. 상태 관리 (AgentState)

```python
class AgentState(TypedDict):
    # 입력
    user_query: str                    # 사용자 쿼리
    
    # 조사 데이터
    market_data: List[Dict]            # 시장 조사 결과
    tech_data: List[Dict]              # 기술 조사 결과
    industry_data: List[Dict]          # 산업 조사 결과
    company_data: List[Dict]           # 기업 조사 결과
    challenge_data: List[Dict]         # 도전과제 조사 결과
    
    # 중간 결과
    synthesized_data: Dict             # 종합된 데이터
    report_sections: Dict              # 보고서 섹션
    
    # 최종 결과
    final_report: str                  # 최종 보고서
    quality_score: float               # 품질 점수
    
    # 메타데이터
    iteration_count: int               # 반복 횟수
    messages: List[str]                # 로그 메시지
```

### 2. 노드 구조

각 노드는 상태를 입력받아 처리 후 업데이트된 상태를 반환:

```python
def node_function(state: AgentState) -> AgentState:
    """
    1. 상태에서 필요한 정보 추출
    2. 처리 로직 실행 (LLM 호출, 검색 등)
    3. 결과를 상태에 저장
    4. 로그 메시지 추가
    5. 업데이트된 상태 반환
    """
    # 입력
    query = state["user_query"]
    
    # 처리
    result = process(query)
    
    # 상태 업데이트
    state["result_field"] = result
    state["messages"].append("✅ 처리 완료")
    
    return state
```

### 3. 워크플로우 구성

```python
def create_physical_ai_agent():
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("planning", planning_node)
    workflow.add_node("research", research_node)
    
    # 엣지 추가
    workflow.set_entry_point("planning")
    workflow.add_edge("planning", "research")
    
    # 조건부 엣지
    workflow.add_conditional_edges(
        "research",
        quality_check,
        {"continue": "next_node", "retry": "planning"}
    )
    
    return workflow.compile()
```

## 데이터 플로우

### 1. 입력 → 조사

```
User Query
    ↓
Planning Node
    ↓
5개 Research Nodes (병렬)
    ├─ Market Research
    ├─ Tech Research
    ├─ Industry Research
    ├─ Company Research
    └─ Challenge Research
```

### 2. 조사 → 종합

```
Research Results
    ↓
Synthesis Node
    ├─ 데이터 통합
    ├─ 중복 제거
    ├─ 카테고리화
    └─ 요약 생성
```

### 3. 종합 → 보고서

```
Synthesized Data
    ↓
Report Generation
    ├─ 섹션별 작성
    ├─ 목차 생성
    ├─ 결론 작성
    └─ 출처 정리
```

### 4. 보고서 → 검토

```
Draft Report
    ↓
Quality Review
    ├─ 5가지 기준 평가
    ├─ 점수 산출
    └─ 피드백 생성
    ↓
Refinement (필요시)
    ↓
PDF Generation
```

## API 인터페이스

### 주요 함수

```python
# 1. 에이전트 실행
def run_agent(user_query: str) -> Dict[str, Any]:
    """
    Args:
        user_query: 사용자 질문
    
    Returns:
        {
            "final_report": str,
            "quality_score": float,
            "iteration_count": int,
            "messages": List[str]
        }
    """

# 2. PDF 생성
def markdown_to_pdf(
    markdown_text: str, 
    output_filename: str
) -> str:
    """
    Args:
        markdown_text: 마크다운 텍스트
        output_filename: 출력 파일명
    
    Returns:
        생성된 PDF 파일 경로
    """

# 3. 그래프 생성
def create_physical_ai_agent() -> CompiledGraph:
    """
    Returns:
        컴파일된 LangGraph 워크플로우
    """
```

## 확장 가능한 구조

### 새로운 리서치 노드 추가

```python
# 1. 노드 함수 정의
def new_research_node(state: AgentState) -> AgentState:
    # 검색 로직
    results = search_tool.invoke("query")
    state["new_data"] = results
    return state

# 2. 그래프에 추가
workflow.add_node("new_research", new_research_node)
workflow.add_edge("planning", "new_research")
workflow.add_edge("new_research", "synthesis")

# 3. 상태에 필드 추가
class AgentState(TypedDict):
    # ... 기존 필드
    new_data: List[Dict]  # 새로운 데이터 필드
```

### 새로운 평가 기준 추가

```python
# review_node 함수 수정
REVIEW_CRITERIA = """
기존 5가지 기준:
A. 내용 완성도
B. 데이터 정확성
C. 구조 논리성
D. 실행 가능성
E. 전문성

새로운 기준:
F. 혁신성 (20점 만점)
- 새로운 인사이트 제시
- 독창적인 분석
"""
```

## 설정 관리

### 환경 변수

```python
# .env 파일
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
OPENAI_MODEL=gpt-4o-mini
MAX_SEARCH_RESULTS=5
QUALITY_THRESHOLD=7.0
```

### 코드에서 사용

```python
import os
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
```

## 로깅

### 로그 레벨

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### 사용 예시

```python
def research_node(state):
    logger.info("Starting market research")
    results = search_tool.invoke(query)
    logger.debug(f"Found {len(results)} results")
    return state
```

## 테스트 구조

```python
# tests/test_nodes.py
def test_planning_node():
    state = {"user_query": "test"}
    result = planning_node(state)
    assert "research_plan" in result

# tests/test_integration.py
def test_full_pipeline():
    result = run_agent("test query")
    assert result["quality_score"] > 0
```

## 성능 최적화

### 병렬 처리

```python
# LangGraph의 자동 병렬 처리
# 공통 출발점을 가진 노드들은 자동으로 병렬 실행됨
workflow.add_edge("planning", "market_research")
workflow.add_edge("planning", "tech_research")  # 동시 실행
```

### 캐싱

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def search_with_cache(query: str):
    return search_tool.invoke(query)
```

---

이 문서는 프로젝트의 기술적 구조를 이해하는 데 도움을 줍니다. 
더 자세한 내용은 코드 내 docstring을 참조하세요.
