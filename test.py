"""
Physical AI 트렌드 예측 보고서 생성 AI 에이전트
LangGraph 구현 with Tavily Search
"""

from typing import TypedDict, Annotated, List, Dict, Optional, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
import operator
import os
import re
from datetime import datetime
from dotenv import load_dotenv

# PDF 생성 라이브러리
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from pathlib import Path
import os

FONT_DIRS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts",
    Path(r"C:\Windows\Fonts"),
]

def find_font(filename):
    for base in FONT_DIRS:
        candidate = base / filename
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError(filename)


# ==================== PDF 설정 ====================
# 한글 폰트 등록
try:
    pdfmetrics.registerFont(TTFont("NanumGothic", find_font("NanumGothic-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("NanumGothicBold", find_font("NanumGothic-Bold.ttf")))
    KOREAN_FONT = 'NanumGothic'
    KOREAN_FONT_BOLD = 'NanumGothicBold'
except:
    KOREAN_FONT = 'Helvetica'
    KOREAN_FONT_BOLD = 'Helvetica-Bold'
    print("⚠️ 한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")

load_dotenv(override=True)

# 컬러 팔레트
PRIMARY_COLOR = colors.HexColor('#1E3A8A')
SECONDARY_COLOR = colors.HexColor('#3B82F6')
ACCENT_COLOR = colors.HexColor('#06B6D4')
LIGHT_BG = colors.HexColor('#F0F9FF')


class NumberedCanvas(canvas.Canvas):
    """페이지 번호가 있는 캔버스"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        
    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
        
    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
        
    def draw_page_number(self, page_count):
        """페이지 번호 그리기"""
        page_num = self._pageNumber
        if page_num > 1:
            self.setFont(KOREAN_FONT, 9)
            self.setFillColor(colors.grey)
            self.drawRightString(A4[0] - 50, 25, f"Page {page_num - 1} of {page_count - 1}")
            self.drawString(50, 25, "Physical AI Trend Report")


def markdown_to_pdf(markdown_text: str, output_filename: str) -> str:
    """마크다운 텍스트를 PDF로 변환"""
    
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    
    # 스타일 정의
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=PRIMARY_COLOR,
        alignment=TA_CENTER,
        spaceAfter=30,
        fontName=KOREAN_FONT_BOLD
    )
    
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=PRIMARY_COLOR,
        spaceAfter=12,
        spaceBefore=20,
        fontName=KOREAN_FONT_BOLD,
        borderWidth=2,
        borderColor=ACCENT_COLOR,
        borderPadding=8,
        backColor=LIGHT_BG
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=SECONDARY_COLOR,
        spaceAfter=10,
        spaceBefore=15,
        fontName=KOREAN_FONT_BOLD
    )
    
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=SECONDARY_COLOR,
        spaceAfter=8,
        spaceBefore=12,
        fontName=KOREAN_FONT_BOLD
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
        leading=16,
        fontName=KOREAN_FONT
    )
    
    story = []
    
    # 마크다운 파싱
    lines = markdown_text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 빈 줄
        if not line:
            i += 1
            continue
        
        # 제목
        if line.startswith('# '):
            title_text = line[2:].strip()
            if i < 3:  # 처음 나오는 제목은 메인 타이틀
                story.append(Spacer(1, 0.5*inch))
                story.append(Paragraph(title_text, title_style))
                story.append(Spacer(1, 0.3*inch))
            else:
                story.append(Paragraph(title_text, h1_style))
            i += 1
            
        elif line.startswith('## '):
            story.append(Paragraph(line[3:].strip(), h2_style))
            i += 1
            
        elif line.startswith('### '):
            story.append(Paragraph(line[4:].strip(), h3_style))
            i += 1
        
        # 수평선
        elif line.startswith('---'):
            story.append(Spacer(1, 0.2*inch))
            i += 1
        
        # 불릿 리스트
        elif line.startswith('- ') or line.startswith('* '):
            bullet_text = line[2:].strip()
            bullet_text = f"• {bullet_text}"
            story.append(Paragraph(bullet_text, body_style))
            i += 1
        
        # 일반 텍스트
        else:
            # 볼드 처리 (**text**)
            line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            # 이탤릭 처리 (*text*)
            line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', line)
            
            story.append(Paragraph(line, body_style))
            i += 1
    
    # 발행일 추가
    story.append(Spacer(1, 0.5*inch))
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER,
        fontName=KOREAN_FONT
    )
    story.append(Paragraph(f"<i>보고서 생성일: {datetime.now().strftime('%Y년 %m월 %d일')}</i>", date_style))
    
    # PDF 생성
    doc.build(story, canvasmaker=NumberedCanvas)
    
    return output_filename


# ==================== 리서치 계획 구조 ====================
class ResearchArea(BaseModel):
    """LLM이 반환하는 각 연구 영역 구조"""
    focus_question: str = Field(..., description="해당 영역에서 답해야 할 핵심 질문")
    search_keywords: List[str] = Field(..., description="해당 영역을 탐색할 검색 키워드 목록 (최소 5개)")
    expected_insights: str = Field(..., description="조사를 통해 도출하고자 하는 주요 인사이트")


class ResearchPlan(BaseModel):
    """LLM이 생성하는 전체 리서치 계획"""
    plan_overview: str = Field(..., description="전체 리서치 방향과 목표 요약")
    market: ResearchArea
    tech: ResearchArea
    industry: ResearchArea
    company: ResearchArea
    challenge: ResearchArea


DEFAULT_RESEARCH_PLAN: Dict[str, List[str]] = {
    "market": [
        "Physical AI market size 2025-2030",
        "humanoid robotics market forecast",
        "AI robotics investment trends",
        "Physical AI market growth rate",
        "robotics market segmentation"
    ],
    "tech": [
        "Vision-Language-Action models 2025",
        "Physical AI foundation models",
        "robotics AI breakthrough 2025",
        "NVIDIA Isaac GR00T",
        "world foundation models robotics"
    ],
    "industry": [
        "Physical AI manufacturing use cases",
        "robotics logistics warehouse 2025",
        "AI robotics healthcare applications",
        "autonomous vehicles Physical AI",
        "retail robotics deployment"
    ],
    "company": [
        "Tesla Optimus humanoid robot",
        "Figure AI BMW partnership",
        "Agility Robotics Digit",
        "Boston Dynamics Atlas electric",
        "NVIDIA Cosmos robotics"
    ],
    "challenge": [
        "Physical AI adoption barriers",
        "robotics battery life challenges",
        "AI robot safety concerns",
        "workforce robotics impact",
        "Physical AI regulation 2025"
    ]
}

planning_prompt = ChatPromptTemplate.from_messages([
    ("system", """당신은 Physical AI 분야의 시니어 리서처입니다.
향후 5년을 대상으로 시장, 기술, 산업, 기업, 도전과제 다섯 영역에 대한 리서치 계획을 수립하세요.
응답은 JSON 형식이며, 각 영역에 대해 focus_question, search_keywords, expected_insights를 반드시 포함하세요.
search_keywords는 영어로 제공하며 항상 5개 이상의 구체적인 키워드 또는 문구를 제공합니다."""),
    ("user", """요청: {query}

분석 기간: 향후 5년

각 영역별 조사 목표를 간결하게 정리하고, 검색 키워드 5개와 기대 인사이트를 제시하세요.""")
])

planning_chain = planning_prompt | ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(ResearchPlan)

QUALITY_CRITERIA = {
    "min_items": 3,
    "min_hit_ratio": 0.6,
    "min_avg_score": 0.25,
    "min_answer_ratio": 0.4,
    "min_content_ratio": 0.5,
    "min_answer_chars": 80,
    "min_content_chars": 120,
}

REVIEW_BASELINE_REPORT = """# Physical AI 보고서 요약 (초안)
- 시장 전망이 정성적 서술에 머물러 있으며 수치 근거가 부족합니다.
- 기술 섹션은 트렌드 키워드만 나열하고 실제 구현 사례가 없습니다.
- 산업별 분석이 단순히 업종을 열거하는 수준이라 실행 통찰이 떨어집니다.
"""

REVIEW_STRONG_REPORT = """# Physical AI 보고서 요약 (우수)
- 글로벌 시장 데이터를 CAGR과 투자 금액으로 제시하고 지역별 차별화 포인트를 제공합니다.
- 기술 섹션은 GAI, 로보틱스 소프트웨어 스택 등 핵심 기술을 최신 사례와 함께 설명합니다.
- 산업 적용과 도전과제, 권고안이 서로 논리적으로 연결되어 전략적 실행 아이디어를 제시합니다.
"""

REVIEW_FEW_SHOT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 Physical AI 전문 감수자입니다. 아래 기준으로 0-10점 사이 점수를 부여하고, 각 항목별 코멘트를 남기세요.
- 내용 완성도: 핵심 질문에 대한 답변 여부와 깊이
- 데이터 정확성: 수치, 출처, 사실 검증 수준
- 구조 논리성: 섹션 간 연결성과 이야기 흐름
- 실행 가능성: 권고사항의 구체성 및 실현성
- 전문성: 업계 용어 활용과 통찰의 수준

항상 아래 형식을 그대로 유지하세요:
점수: x.x/10
강점:
- ...
개선 필요:
- ...
세부 평가:
- 내용 완성도: ...
- 데이터 정확성: ...
- 구조 논리성: ...
- 실행 가능성: ...
- 전문성: ..."""),
    ("human", """평가 대상 보고서:
{baseline_report}"""),
    ("assistant", """점수: 5.8/10
강점:
- Physical AI 시장이 성장 중이라는 방향성은 제시했습니다.
개선 필요:
- 수치 근거와 최근 사례가 없어 신뢰도가 낮습니다.
- 권고안이 추상적이며 실행 단계를 제시하지 못합니다.
세부 평가:
- 내용 완성도: 핵심 질문을 부분적으로만 다룹니다.
- 데이터 정확성: 정성적 주장만 있고 근거 수치가 부족합니다.
- 구조 논리성: 섹션 간 연결이 약하고 중복이 있습니다.
- 실행 가능성: 권고안이 "협력 강화" 수준에 머뭅니다.
- 전문성: 업계 지식과 용어 활용이 제한적입니다."""),
    ("human", """평가 대상 보고서:
{strong_report}"""),
    ("assistant", """점수: 8.9/10
강점:
- 시장·기술·산업 데이터를 최신 수치와 인용으로 명확히 제시합니다.
- 권고안이 투자 우선순위와 실행 단계를 구체적으로 안내합니다.
개선 필요:
- 위험 관리 전략에 대한 대안 시나리오가 조금 더 있으면 좋겠습니다.
세부 평가:
- 내용 완성도: 요구된 질문을 모두 깊이 있게 답했습니다.
- 데이터 정확성: 다수의 최신 통계와 보고서를 정확히 인용합니다.
- 구조 논리성: 섹션 전개가 매끄럽고 요약-본문-권고가 정렬됩니다.
- 실행 가능성: 재무·기술·파트너십 관점에서 실무 지침을 제공합니다.
- 전문성: 업계 동향과 용어 활용이 전문 리포트 수준입니다."""),
    ("human", """평가 대상 보고서:
{report}

위 형식을 그대로 따르세요."""),
])

# ==================== Tavily 검색 설정 ====================
def get_tavily_search(max_results: int = 5):
    """Tavily 검색 도구 생성"""
    return TavilySearchResults(
        max_results=max_results,
        search_depth="advanced",  # "basic" or "advanced"
        include_answer=True,  # AI 생성 답변 포함
        include_raw_content=False,  # only summary text to keep logs small
        include_images=False
    )

# ==================== 상태 병합 유틸리티 ====================
def preserve_user_query(existing: Optional[str], new: str) -> str:
    """Keep the first user query value when multiple nodes emit it."""
    return existing if existing else new

def replace_research_plan(existing: Optional[Dict[str, List[str]]], new: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Prefer the newest non-empty research plan."""
    if new:
        return new
    return existing or {}

def replace_result_list(existing: Optional[List[Dict]], new: List[Dict]) -> List[Dict]:
    """Prefer the latest non-empty research results list."""
    if new:
        return new
    return existing or []

def merge_search_context(existing: Optional[Dict[str, str]], new: Dict[str, str]) -> Dict[str, str]:
    """Merge search context dictionaries across parallel nodes."""
    merged = dict(existing) if existing else {}
    merged.update(new)
    return merged

def merge_report_sections(existing: Optional[Dict[str, str]], new: Dict[str, str]) -> Dict[str, str]:
    """Merge report section text updates across nodes."""
    merged = dict(existing) if existing else {}
    merged.update(new)
    return merged


def merge_synthesized_data(existing: Optional[Dict[str, Any]], new: Dict[str, Any]) -> Dict[str, Any]:
    """Merge synthesized insights coming from multiple nodes."""
    merged = dict(existing) if existing else {}
    merged.update(new)
    return merged

def replace_final_report(existing: Optional[str], new: str) -> str:
    """Prefer the latest final report content."""
    return new if new else (existing or "")

def replace_quality_score(existing: Optional[float], new: float) -> float:
    """Prefer the latest quality score provided."""
    return new if new is not None else (existing if existing is not None else 0.0)

def replace_iteration_count(existing: Optional[int], new: int) -> int:
    """Keep the highest iteration count emitted."""
    existing_val = existing if existing is not None else 0
    new_val = new if new is not None else 0
    return max(existing_val, new_val)

# ==================== State 정의 ====================
class AgentState(TypedDict):
    """에이전트 상태 관리"""
    user_query: Annotated[str, preserve_user_query]
    research_plan: Annotated[Dict[str, List[str]], replace_research_plan]
    market_data: Annotated[List[Dict], replace_result_list]
    tech_data: Annotated[List[Dict], replace_result_list]
    industry_data: Annotated[List[Dict], replace_result_list]
    company_data: Annotated[List[Dict], replace_result_list]
    challenge_data: Annotated[List[Dict], replace_result_list]
    synthesized_data: Annotated[Dict[str, Any], merge_synthesized_data]
    report_sections: Annotated[Dict[str, str], merge_report_sections]
    final_report: Annotated[str, replace_final_report]
    quality_score: Annotated[float, replace_quality_score]
    iteration_count: Annotated[int, replace_iteration_count]
    search_context: Annotated[Dict[str, str], merge_search_context]  # Tavily 답변 저장
    messages: Annotated[List[str], operator.add]


def execute_tavily_query(tavily_search, query: str) -> Dict[str, Any]:
    """Run Tavily with fallbacks to avoid empty responses."""
    # ✅ 단순화된 시도 목록 (문자열만)
    attempts = [
        query,  # 원본 쿼리
        f"{query} 2024 2025",  # 연도 추가
        f"{query} analysis",  # 영어 키워드 추가
    ]
    last_error = ""

    for idx, query_str in enumerate(attempts, 1):
        try:
            print(f"🔍 시도 {idx}: {query_str[:50]}...")
            result = tavily_search.invoke(query_str)  # ✅ 문자열 직접 전달
            print(f"✅ 성공! 결과 타입: {type(result)}")
            
            # 결과 처리
            if isinstance(result, dict):
                if result.get("results"):
                    result.setdefault("answer", "")
                    result.setdefault("error", "")
                    return result
                last_error = result.get("error", "no results")
                print(f"⚠️ 빈 결과: {last_error}")
                continue

            if isinstance(result, list):
                if result:
                    return {"results": result, "answer": "", "error": ""}
                print(f"⚠️ 빈 리스트")
                continue
                
        except Exception as exc:
            last_error = str(exc)
            print(f"❌ 에러: {exc}")
            
            # 432 에러 특별 처리
            if "432" in str(exc):
                print("\n⚠️ Tavily API 432 에러 발생!")
                print("가능한 원인:")
                print("1. API 키가 무효하거나 만료됨")
                print("2. 무료 플랜 사용량 초과 (https://app.tavily.com/home 에서 확인)")
                print("3. API 키 권한 문제")
                print("\n해결 방법:")
                print("- 새 API 키 발급: https://app.tavily.com/")
                print("- 환경변수 재설정: export TAVILY_API_KEY='your-new-key'")
                break  # 432 에러는 재시도 불필요
            
            continue

    return {"results": [], "answer": "", "error": last_error or "empty Tavily response"}

def strengthen_keyword(category: str, keyword: str, state: AgentState) -> str:
    """Adjust Tavily query with quality feedback to target weak metrics."""
    feedback = state.get("search_context", {}).get("quality_feedback", {})
    issues = feedback.get(category, [])
    if not issues:
        return keyword

    modifiers: List[str] = []
    if "items" in issues or "coverage" in issues:
        modifiers.append("comprehensive data reliable sources 2024")
    if "answers" in issues:
        modifiers.append("key insights summary")
    if "content" in issues:
        modifiers.append("detailed report in depth analysis")
    if "score" in issues:
        modifiers.append("official statistics verified figures")

    if modifiers:
        boost = " ".join(modifiers)
        if boost not in keyword:
            return f"{keyword} {boost}"
    return keyword
# ==================== 노드 함수들 ====================

def planning_node(state: AgentState) -> AgentState:
    """리서치 계획 수립"""
    state.setdefault("search_context", {})
    try:
        plan = planning_chain.invoke({
            "query": state["user_query"]
        })
        state["research_plan"] = {
            "market": list(plan.market.search_keywords),
            "tech": list(plan.tech.search_keywords),
            "industry": list(plan.industry.search_keywords),
            "company": list(plan.company.search_keywords),
            "challenge": list(plan.challenge.search_keywords)
        }
        state["search_context"]["plan_overview"] = plan.plan_overview
        for area in ("market", "tech", "industry", "company", "challenge"):
            area_plan = getattr(plan, area)
            state["search_context"][f"{area}_focus"] = area_plan.focus_question
        state["messages"].append("✅ LLM 기반 리서치 계획 수립 완료")
        print("✅ 리서치 계획: 수립완료")
        overview = plan.plan_overview.strip()
        if overview:
            state["messages"].append(f"🧭 계획 요약: {overview}")
    except Exception as exc:
        print(f"리서치 계획 생성 오류: {exc}")
        state["research_plan"] = {category: list(keywords) for category, keywords in DEFAULT_RESEARCH_PLAN.items()}
        state["search_context"]["plan_overview"] = "사전 정의된 기본 리서치 계획 사용"
        state["messages"].append("⚠️ 기본 리서치 계획으로 대체했습니다")
    return state

def market_research_node(state: AgentState) -> AgentState:
    """시장 데이터 수집 with Tavily"""
    tavily_search = get_tavily_search(max_results=5)
    market_data = []
    search_contexts = []
    
    for keyword in state["research_plan"]["market"]:
        try:
            # Tavily 검색 실행
            query = strengthen_keyword("market", keyword, state)
            raw_results = execute_tavily_query(tavily_search, query)
            answer_value = raw_results.get("answer", "") or ""
            results_list = raw_results.get("results", []) or []
            error_message = raw_results.get("error", "")
            if error_message and not results_list:
                search_contexts.append(f"[{keyword}] ERROR: {error_message}")
            if isinstance(results_list, dict):
                results_list = [results_list]
            elif not isinstance(results_list, list):
                results_list = []
            

            # 결과 처리 (Tavily는 구조화된 Dict 반환)
            processed_results = []
            for result in results_list[:2]:
                if not isinstance(result, dict):
                    continue
                processed_results.append({
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "content": result.get("content", "")[:250],  # 500자 제한
                    "score": result.get("score", 0.0)  # 관련성 점수
                })
            
            market_data.append({
                "keyword": keyword,
                "query": query,
                "results": processed_results,
                "error": raw_results.get("error", ""),
                "answer": answer_value  # Tavily AI 답변
            })
            
            # AI 답변 컨텍스트 저장
            if answer_value:
                search_contexts.append(f"[{keyword}]: {answer_value}")
                
        except Exception as e:
            print(f"검색 오류: {keyword} - {e}")
            market_data.append({
                "keyword": keyword,
                "results": [],
                "answer": ""
            })
    
    state["market_data"] = market_data
    
    # search_context 초기화 (처음 실행시)
    if "search_context" not in state:
        state["search_context"] = {}
    state["search_context"]["market"] = "\n".join(search_contexts)
    
    state["messages"].append(f"✅ 시장 데이터 {len(market_data)}건 수집 (Tavily Advanced)")
    return state

def tech_research_node(state: AgentState) -> AgentState:
    """기술 동향 수집 with Tavily"""
    tavily_search = get_tavily_search(max_results=5)
    tech_data = []
    search_contexts = []
    
    for keyword in state["research_plan"]["tech"]:
        try:
            query = strengthen_keyword("tech", keyword, state)
            raw_results = execute_tavily_query(tavily_search, query)
            answer_value = raw_results.get("answer", "") or ""
            results_list = raw_results.get("results", []) or []
            error_message = raw_results.get("error", "")
            if error_message and not results_list:
                search_contexts.append(f"[{keyword}] ERROR: {error_message}")
            if isinstance(results_list, dict):
                results_list = [results_list]
            elif not isinstance(results_list, list):
                results_list = []
            

            processed_results = []
            for result in results_list[:2]:
                if not isinstance(result, dict):
                    continue
                processed_results.append({
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "content": result.get("content", "")[:250],
                    "score": result.get("score", 0.0)
                })
            
            tech_data.append({
                "keyword": keyword,
                "query": query,
                "results": processed_results,
                "error": raw_results.get("error", ""),
                "answer": answer_value
            })
            
            if answer_value:
                search_contexts.append(f"[{keyword}]: {answer_value}")
                
        except Exception as e:
            print(f"검색 오류: {keyword} - {e}")
            tech_data.append({
                "keyword": keyword,
                "results": [],
                "answer": ""
            })
    
    state["tech_data"] = tech_data
    state["search_context"]["tech"] = "\n".join(search_contexts)
    state["messages"].append(f"✅ 기술 데이터 {len(tech_data)}건 수집 (Tavily Advanced)")
    return state

def industry_research_node(state: AgentState) -> AgentState:
    """산업별 사례 수집 with Tavily"""
    tavily_search = get_tavily_search(max_results=5)
    industry_data = []
    search_contexts = []
    
    for keyword in state["research_plan"]["industry"]:
        try:
            query = strengthen_keyword("industry", keyword, state)
            raw_results = execute_tavily_query(tavily_search, query)
            answer_value = raw_results.get("answer", "") or ""
            results_list = raw_results.get("results", []) or []
            error_message = raw_results.get("error", "")
            if error_message and not results_list:
                search_contexts.append(f"[{keyword}] ERROR: {error_message}")
            if isinstance(results_list, dict):
                results_list = [results_list]
            elif not isinstance(results_list, list):
                results_list = []
            

            processed_results = []
            for result in results_list[:2]:
                if not isinstance(result, dict):
                    continue
                processed_results.append({
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "content": result.get("content", "")[:250],
                    "score": result.get("score", 0.0)
                })
            
            industry_data.append({
                "keyword": keyword,
                "query": query,
                "results": processed_results,
                "error": raw_results.get("error", ""),
                "answer": answer_value
            })
            
            if answer_value:
                search_contexts.append(f"[{keyword}]: {answer_value}")
                
        except Exception as e:
            print(f"검색 오류: {keyword} - {e}")
            industry_data.append({
                "keyword": keyword,
                "results": [],
                "answer": ""
            })
    
    state["industry_data"] = industry_data
    state["search_context"]["industry"] = "\n".join(search_contexts)
    state["messages"].append(f"✅ 산업 데이터 {len(industry_data)}건 수집 (Tavily Advanced)")
    return state

def company_research_node(state: AgentState) -> AgentState:
    """기업 분석 데이터 수집 with Tavily"""
    tavily_search = get_tavily_search(max_results=5)
    company_data = []
    search_contexts = []
    
    for keyword in state["research_plan"]["company"]:
        try:
            query = strengthen_keyword("company", keyword, state)
            raw_results = execute_tavily_query(tavily_search, query)
            answer_value = raw_results.get("answer", "") or ""
            results_list = raw_results.get("results", []) or []
            error_message = raw_results.get("error", "")
            if error_message and not results_list:
                search_contexts.append(f"[{keyword}] ERROR: {error_message}")
            if isinstance(results_list, dict):
                results_list = [results_list]
            elif not isinstance(results_list, list):
                results_list = []
            

            processed_results = []
            for result in results_list[:2]:
                if not isinstance(result, dict):
                    continue
                processed_results.append({
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "content": result.get("content", "")[:250],
                    "score": result.get("score", 0.0)
                })
            
            company_data.append({
                "keyword": keyword,
                "query": query,
                "results": processed_results,
                "error": raw_results.get("error", ""),
                "answer": answer_value
            })
            
            if answer_value:
                search_contexts.append(f"[{keyword}]: {answer_value}")
                
        except Exception as e:
            print(f"검색 오류: {keyword} - {e}")
            company_data.append({
                "keyword": keyword,
                "results": [],
                "answer": ""
            })
    
    state["company_data"] = company_data
    state["search_context"]["company"] = "\n".join(search_contexts)
    state["messages"].append(f"✅ 기업 데이터 {len(company_data)}건 수집 (Tavily Advanced)")
    return state

def challenge_research_node(state: AgentState) -> AgentState:
    """도전과제 데이터 수집 with Tavily"""
    tavily_search = get_tavily_search(max_results=5)
    challenge_data = []
    search_contexts = []
    
    for keyword in state["research_plan"]["challenge"]:
        try:
            query = strengthen_keyword("challenge", keyword, state)
            raw_results = execute_tavily_query(tavily_search, query)
            answer_value = raw_results.get("answer", "") or ""
            results_list = raw_results.get("results", []) or []
            error_message = raw_results.get("error", "")
            if error_message and not results_list:
                search_contexts.append(f"[{keyword}] ERROR: {error_message}")
            if isinstance(results_list, dict):
                results_list = [results_list]
            elif not isinstance(results_list, list):
                results_list = []
            

            processed_results = []
            for result in results_list[:2]:
                if not isinstance(result, dict):
                    continue
                processed_results.append({
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "content": result.get("content", "")[:250],
                    "score": result.get("score", 0.0)
                })
            
            challenge_data.append({
                "keyword": keyword,
                "query": query,
                "results": processed_results,
                "error": raw_results.get("error", ""),
                "answer": answer_value
            })
            
            if answer_value:
                search_contexts.append(f"[{keyword}]: {answer_value}")
                
        except Exception as e:
            print(f"검색 오류: {keyword} - {e}")
            challenge_data.append({
                "keyword": keyword,
                "results": [],
                "answer": ""
            })
    
    state["challenge_data"] = challenge_data
    state["search_context"]["challenge"] = "\n".join(search_contexts)
    state["messages"].append(f"✅ 도전과제 데이터 {len(challenge_data)}건 수집 (Tavily Advanced)")
    return state

def synthesis_node(state: AgentState) -> AgentState:
    """수집된 데이터 통합 및 분석 (Tavily 답변 활용)"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    # Tavily AI 답변을 우선 활용
    all_data = {
        "market": {
            "tavily_answers": state["search_context"].get("market", ""),
            "detailed_data": state["market_data"]
        },
        "tech": {
            "tavily_answers": state["search_context"].get("tech", ""),
            "detailed_data": state["tech_data"]
        },
        "industry": {
            "tavily_answers": state["search_context"].get("industry", ""),
            "detailed_data": state["industry_data"]
        },
        "company": {
            "tavily_answers": state["search_context"].get("company", ""),
            "detailed_data": state["company_data"]
        },
        "challenge": {
            "tavily_answers": state["search_context"].get("challenge", ""),
            "detailed_data": state["challenge_data"]
        }
    }
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 Physical AI 전문 분석가입니다.
        Tavily AI가 제공한 답변과 상세 데이터를 종합하여 핵심 인사이트를 추출하세요.
        각 영역별로 가장 중요한 트렌드 3-5가지를 구체적 수치, 자료의 출처를 함께 제시하세요."""),
        ("user", """카테고리: {category}
        
Tavily AI 답변:
{tavily_answers}

상세 검색 결과 (상위 결과):
{detailed_data}

위 정보를 바탕으로 핵심 인사이트를 추출하세요.""")
    ])
    
    synthesized = {}
    for category, data in all_data.items():
        # 상세 데이터 요약 (상위 3개 결과만)
        detailed_summary = []
        for item in data["detailed_data"][:3]:
            if item.get("results"):
                top_result = item["results"][0]
                detailed_summary.append(
                    f"- {top_result.get('title', '')}: {top_result.get('content', '')[:200]} (출처: {top_result.get('url', '')})"
                )
        
        response = llm.invoke(
            prompt.format_messages(
                category=category,
                tavily_answers=data["tavily_answers"],
                detailed_data="\n".join(detailed_summary)
            )
        )
        synthesized[category] = response.content
    
    state["synthesized_data"] = synthesized
    state["messages"].append("✅ 데이터 통합 분석 완료 (Tavily AI 답변 활용)")
    return state

def quality_check_node(state: AgentState) -> str:
    """   ( )"""
    state.setdefault("search_context", {})
    categories = ["market", "tech", "industry", "company", "challenge"]
    diagnostics: List[str] = []
    failing: List[str] = []
    quality_feedback: Dict[str, List[str]] = {}

    for category in categories:
        data_key = f"{category}_data"
        entries = state.get(data_key, []) or []
        print(f"품질 검사 - {category}: {len(entries)} 항목 분석 중...")
        print(entries[:2])  # 처음 2개 항목 출력
        total = len(entries)
        hits = sum(1 for item in entries if item.get("results"))
        answers = sum(1 for item in entries if item.get("answer"))

        failing_metrics: List[str] = []
        if total < QUALITY_CRITERIA["min_items"]:
            failing_metrics.append("items")
        if hits / total < QUALITY_CRITERIA["min_hit_ratio"]:
            failing_metrics.append("coverage")
        if answers / total < QUALITY_CRITERIA["min_answer_ratio"]:
            failing_metrics.append("answers")

        passes = total > 0 and (hits > 0 or answers > 0)

        if failing_metrics:
            quality_feedback[category] = failing_metrics

        diagnostics.append(
            f"{category}: total={total}, hits={hits}, answers={answers} -> {'PASS' if passes else 'RECHECK'}"
        )
        if not passes:
            failing.append(category)

    state["search_context"]["quality_feedback"] = quality_feedback
    state["search_context"]["quality_diagnostics"] = "\n".join(diagnostics)
    state["messages"].append("     - " + " | ".join(diagnostics))

    current_loop = state.get("iteration_count", 0) + 1
    
    state["iteration_count"] = current_loop 
    max_loops = 2
    
    if failing and current_loop < max_loops:
        print(f"현재 반복 횟수: {current_loop}")
        state["messages"].append(f"  : {', '.join(failing)} ( )")
        return "research_more"

    if failing:
        state["messages"].append(f"        : {', '.join(failing)} (  {max_loops}  )")

    state["messages"].append("    ")
    state["iteration_count"] = 0
    return "generate_report"

def report_generation_node(state: AgentState) -> AgentState:
    """보고서 초안 생성"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
    
    sections = {
        "executive_summary": "핵심 요약",
        "market_overview": "시장 전망",
        "technology_trends": "기술 트렌드",
        "industry_applications": "산업별 응용",
        "key_players": "주요 기업",
        "challenges": "도전과제",
        "forecast": "향후 5년 전망",
        "recommendations": "전략적 권고사항"
    }
    
    report_sections = {}
    
    for section_key, section_title in sections.items():
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""Physical AI 트렌드 보고서의 '{section_title}' 섹션을 작성하세요.
            전문적이고 간결하며 데이터 기반의 내용으로 작성하세요."""),
            ("user", "분석 데이터:\n{data}")
        ])
        
        response = llm.invoke(
            prompt.format_messages(data=str(state["synthesized_data"]))
        )
        report_sections[section_key] = response.content
    
    state["report_sections"] = report_sections
    state["messages"].append("✅ 보고서 초안 생성 완료")
    return state

def structure_node(state: AgentState) -> AgentState:
    """보고서 구조화 및 포맷팅"""
    sections = state["report_sections"]
    
    # Markdown 형식으로 보고서 구조화
    final_report = f"""# Physical AI 트렌드 예측 보고서 (2025-2030)

# 핵심 요약
{sections.get('executive_summary', '')}

---

# 1. 시장 전망
{sections.get('market_overview', '')}

# 2. 핵심 기술 트렌드
{sections.get('technology_trends', '')}

# 3. 산업별 응용 분야
{sections.get('industry_applications', '')}

# 4. 주요 기업 및 경쟁 환경
{sections.get('key_players', '')}

# 5. 도전과제 및 장벽
{sections.get('challenges', '')}

# 6. 향후 5년 전망
{sections.get('forecast', '')}

# 7. 기업을 위한 전략적 권고사항
{sections.get('recommendations', '')}

---
*보고서 생성일: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}*
"""
    
    state["final_report"] = final_report
    state["messages"].append("✅ 보고서 구조화 완료")
    return state

def review_node(state: AgentState) -> AgentState:
    """보고서 품질 검토"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    response = llm.invoke(
        REVIEW_FEW_SHOT_PROMPT.format_messages(
            baseline_report=REVIEW_BASELINE_REPORT,
            strong_report=REVIEW_STRONG_REPORT,
            report=state["final_report"][:4000]
        )
    )

    content = response.content.strip()
    score_match = re.search(r"점수\s*[:=]\s*(\d+(?:\.\d+)?)", content)
    score = float(score_match.group(1)) if score_match else 7.0
    score = max(0.0, min(10.0, score))

    state.setdefault("search_context", {})
    state["search_context"]["review_feedback"] = content
    print(f"보고서 품질 점수: {score}/10")
    print("보고서 품질 검토 내용:", content)
    state["quality_score"] = score
    state["messages"].append(f"✅ 품질 검토 완료 (점수: {score:.1f}/10)")
    state["messages"].append("📝 리뷰 요약 저장")
    return state

def final_quality_check_node(state: AgentState) -> str:
    """최종 품질 확인"""
    if state["quality_score"] < 7.0 and state["iteration_count"] < 2:
        state["iteration_count"] += 1
        return "refine"
    return "format"

def refinement_node(state: AgentState) -> AgentState:
    """보고서 개선"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """보고서를 개선하세요. 다음에 집중하세요:
        1. 구체적인 수치 및 데이터 추가
        2. 실행 가능한 권고사항 강화
        3. 논리적 흐름 개선"""),
        ("user", "현재 보고서:\n{report}\n\n분석 데이터:\n{data}")
    ])
    
    response = llm.invoke(
        prompt.format_messages(
            report=state["final_report"][:2000],
            data=str(state["synthesized_data"])[:1000]
        )
    )
    
    # 개선된 내용으로 업데이트
    state["final_report"] = response.content
    state["messages"].append("✅ 보고서 개선 완료")
    return state

def formatting_node(state: AgentState) -> AgentState:
    """최종 포맷팅 및 PDF 생성"""
    state["messages"].append("✅ 최종 포맷팅 완료")
    
    # PDF 생성
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"physical_ai_report_{timestamp}.pdf"
        markdown_to_pdf(state["final_report"], pdf_filename)
        state["messages"].append(f"📄 PDF 보고서 생성 완료: {pdf_filename}")
    except Exception as e:
        state["messages"].append(f"⚠️ PDF 생성 실패: {str(e)}")
    
    return state

# ==================== 그래프 구성 ====================

def create_physical_ai_agent():
    """Physical AI 보고서 생성 에이전트 그래프 생성"""
    
    # StateGraph 초기화
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("planning", planning_node)
    workflow.add_node("market_research", market_research_node)
    workflow.add_node("tech_research", tech_research_node)
    workflow.add_node("industry_research", industry_research_node)
    workflow.add_node("company_research", company_research_node)
    workflow.add_node("challenge_research", challenge_research_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("report_generation", report_generation_node)
    workflow.add_node("structure", structure_node)
    workflow.add_node("review", review_node)
    workflow.add_node("refinement", refinement_node)
    workflow.add_node("formatting", formatting_node)
    
    # 엣지 추가
    workflow.set_entry_point("planning")
    
    # Planning -> Research 병렬 실행
    workflow.add_edge("planning", "market_research")
    workflow.add_edge("planning", "tech_research")
    workflow.add_edge("planning", "industry_research")
    workflow.add_edge("planning", "company_research")
    workflow.add_edge("planning", "challenge_research")
    
    # Research -> Synthesis
    workflow.add_edge("market_research", "synthesis")
    workflow.add_edge("tech_research", "synthesis")
    workflow.add_edge("industry_research", "synthesis")
    workflow.add_edge("company_research", "synthesis")
    workflow.add_edge("challenge_research", "synthesis")
    
    # Synthesis -> Quality Check (조건부)
    workflow.add_conditional_edges(
        "synthesis",
        quality_check_node,
        {
            "research_more": "planning",
            "generate_report": "report_generation"
        }
    )
    
    # Report Generation -> Structure
    workflow.add_edge("report_generation", "structure")
    
    # Structure -> Review
    workflow.add_edge("structure", "review")
    
    # Review -> Final Check (조건부)
    workflow.add_conditional_edges(
        "review",
        final_quality_check_node,
        {
            "refine": "refinement",
            "format": "formatting"
        }
    )
    
    # Refinement -> Structure (개선 후 재검토)
    workflow.add_edge("refinement", "structure")
    
    # Formatting -> END
    workflow.add_edge("formatting", END)
    
    return workflow.compile()

# ==================== 실행 예제 ====================

def run_agent(user_query: str):
    """에이전트 실행"""
    
    # Tavily API 키 확인
    if not os.environ.get("TAVILY_API_KEY"):
        print("⚠️  경고: TAVILY_API_KEY가 설정되지 않았습니다.")
        print("https://tavily.com 에서 API 키를 발급받으세요.")
        return None
    
    # 초기 상태 설정
    initial_state = {
        "user_query": user_query,
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
        "search_context": {},  # Tavily AI 답변 저장
        "messages": []
    }
    
    print("🚀 Physical AI 보고서 생성 시작...")
    print(f"📝 요청: {user_query}\n")
    
    # 에이전트 생성 및 실행
    agent = create_physical_ai_agent()
    result = agent.invoke(initial_state)
    
    # 결과 출력
    print("\n" + "="*60)
    print("📊 실행 로그")
    print("="*60)
    for msg in result["messages"]:
        print(msg)
    
    print("\n" + "="*60)
    print("📄 최종 보고서")
    print("="*60)
    print(result["final_report"])
    
    print("\n" + "="*60)
    print("✅ 보고서 생성 완료!")
    print(f"📈 품질 점수: {result['quality_score']}/10")
    print(f"🔄 반복 횟수: {result['iteration_count']}")
    print("="*60)
    
    return result

# 실행
if __name__ == "__main__":
    # 환경 변수 설정 필요
    # export OPENAI_API_KEY="your-openai-key"
    # export TAVILY_API_KEY="your-tavily-key"
    
    query = "향후 5년 이내 기업에서 관심있게 봐야할 Physical AI 트렌드"
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║         Physical AI 트렌드 보고서 생성 에이전트              ║
║              Powered by LangGraph + Tavily                   ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    result = run_agent(query)
    
    if result:
        # 보고서를 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"physical_ai_report_{timestamp}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(result["final_report"])
        
        print(f"\n💾 보고서가 저장되었습니다: {filename}")