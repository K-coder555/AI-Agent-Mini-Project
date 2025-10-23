"""
AI 트렌드 예측 보고서 생성 AI 에이전트
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from pathlib import Path
# ==================== 한글 폰트 설정 ====================
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

# 컬러 팔레트 (더 다양한 색상)
PRIMARY_COLOR = colors.HexColor('#1E3A8A')      # 진한 파랑
SECONDARY_COLOR = colors.HexColor('#3B82F6')    # 밝은 파랑
ACCENT_COLOR = colors.HexColor('#06B6D4')       # 청록색
SUCCESS_COLOR = colors.HexColor('#10B981')      # 초록색
WARNING_COLOR = colors.HexColor('#F59E0B')      # 주황색
DANGER_COLOR = colors.HexColor('#EF4444')       # 빨강색
LIGHT_BG = colors.HexColor('#F0F9FF')           # 연한 파랑 배경
GRAY_BG = colors.HexColor('#F3F4F6')            # 회색 배경
BORDER_COLOR = colors.HexColor('#E5E7EB')       # 테두리 색


class NumberedCanvas(canvas.Canvas):
    """페이지 번호가 있는 캔버스"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        
    # def showPage(self):
    #     self._saved_page_states.append(dict(self.__dict__))
    #     self._startPage()
        
    def showPage(self):
        """페이지를 저장하기 전에 페이지 번호 그리기"""
        page_num = self._pageNumber
        
        # 첫 페이지가 아니면 페이지 번호 그리기
        if page_num > 1:
            self.saveState()  # 현재 상태 저장
            self.setFont(KOREAN_FONT, 9)
            self.setFillColor(colors.grey)
            # 우측 하단
            self.drawRightString(A4[0] - 50, 25, f"Page {page_num - 1}")
            # 좌측 하단
            self.drawString(50, 25, "Physical AI Trend Report")
            self.restoreState()  # 상태 복원
        
        # 실제 페이지 저장
        canvas.Canvas.showPage(self)
    # def save(self):
    #     num_pages = len(self._saved_page_states)
    #     for state in self._saved_page_states:
    #         self.__dict__.update(state)
    #         self.draw_page_number(num_pages)
    #         canvas.Canvas.showPage(self)
    #     canvas.Canvas.save(self)
        
    # def draw_page_number(self, page_count):
    #     """페이지 번호 그리기"""
    #     page_num = self._pageNumber
    #     if page_num > 1:
    #         self.setFont(KOREAN_FONT, 9)
    #         self.setFillColor(colors.grey)
    #         self.drawRightString(A4[0] - 50, 25, f"Page {page_num - 1} of {page_count - 1}")
    #         self.drawString(50, 25, "Physical AI Trend Report")


def clean_markdown_symbols(text):
    """마크다운 기호를 제거하고 정리"""
    # 볼드 처리 (**text** -> <b>text</b>)
    text = re.sub(r'\*\*\*\*(.*?)\*\*\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<b><i>\1</i></b>', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # 이탤릭 처리 (*text* -> <i>text</i>)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    
    # 인라인 코드 처리 (`code` -> <font name="Courier">code</font>)
    text = re.sub(r'`(.*?)`', r'<font name="Courier" color="#E11D48">\1</font>', text)
    
    # 링크 처리 [text](url) -> text
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    
    return text


def parse_markdown_list_item(line, level=0):
    """리스트 아이템 파싱 (들여쓰기 레벨 포함)"""
    # 불릿 리스트: -, *, •
    bullet_match = re.match(r'^(\s*)([-*•])\s+(.+)$', line)
    if bullet_match:
        indent = len(bullet_match.group(1))
        content = bullet_match.group(3)
        level = indent // 2  # 들여쓰기 레벨 계산
        return 'bullet', content, level
    
    # 숫자 리스트: 1., 2., etc.
    number_match = re.match(r'^(\s*)(\d+)\.\s+(.+)$', line)
    if number_match:
        indent = len(number_match.group(1))
        number = number_match.group(2)
        content = number_match.group(3)
        level = indent // 2
        return 'number', content, level, number
    
    return None, None, 0


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
    
    # 메인 타이틀 스타일
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=32,
        textColor=PRIMARY_COLOR,
        alignment=TA_CENTER,
        spaceAfter=40,
        spaceBefore=20,
        fontName=KOREAN_FONT_BOLD,
        leading=38
    )
    
    # H1 스타일 (박스 형태)
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.white,
        spaceAfter=15,
        spaceBefore=25,
        fontName=KOREAN_FONT_BOLD,
        borderWidth=0,
        borderPadding=12,
        backColor=PRIMARY_COLOR,
        leftIndent=10,
        rightIndent=10
    )
    
    # H2 스타일 (왼쪽 테두리)
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=PRIMARY_COLOR,
        spaceAfter=12,
        spaceBefore=18,
        fontName=KOREAN_FONT_BOLD,
        leftIndent=15,
        borderWidth=0,
        borderPadding=8,
        borderColor=ACCENT_COLOR,
        backColor=LIGHT_BG
    )
    
    # H3 스타일
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=15,
        textColor=SECONDARY_COLOR,
        spaceAfter=10,
        spaceBefore=14,
        fontName=KOREAN_FONT_BOLD,
        leftIndent=10
    )
    
    # H4 스타일
    h4_style = ParagraphStyle(
        'CustomH4',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=SECONDARY_COLOR,
        spaceAfter=8,
        spaceBefore=12,
        fontName=KOREAN_FONT_BOLD,
        leftIndent=5
    )
    
    # 본문 스타일
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
        leading=18,
        fontName=KOREAN_FONT,
        textColor=colors.HexColor('#374151')
    )
    
    # 불릿 리스트 스타일
    bullet_style = ParagraphStyle(
        'BulletList',
        parent=body_style,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=6,
        fontSize=11
    )
    
    # 인용구 스타일
    quote_style = ParagraphStyle(
        'Quote',
        parent=body_style,
        leftIndent=30,
        rightIndent=30,
        fontSize=10,
        textColor=colors.HexColor('#6B7280'),
        backColor=GRAY_BG,
        borderWidth=0,
        borderPadding=10,
        borderColor=ACCENT_COLOR,
        spaceAfter=12,
        spaceBefore=12
    )
    
    story = []
    
    # 마크다운 파싱
    lines = markdown_text.split('\n')
    i = 0
    in_quote = False
    quote_lines = []
    
    while i < len(lines):
        line = lines[i].rstrip()
        
        # 빈 줄
        if not line:
            if in_quote and quote_lines:
                # 인용구 종료
                quote_text = '<br/>'.join(quote_lines)
                story.append(Paragraph(quote_text, quote_style))
                quote_lines = []
                in_quote = False
            i += 1
            continue
        
        # 인용구 처리
        if line.startswith('> '):
            in_quote = True
            quote_content = line[2:].strip()
            quote_content = clean_markdown_symbols(quote_content)
            quote_lines.append(quote_content)
            i += 1
            continue
        elif in_quote:
            # 인용구 종료
            quote_text = '<br/>'.join(quote_lines)
            story.append(Paragraph(quote_text, quote_style))
            quote_lines = []
            in_quote = False
        
        # 제목 처리
        if line.startswith('# '):
            title_text = line[2:].strip()
            title_text = clean_markdown_symbols(title_text)
            if i < 3:  # 메인 타이틀
                story.append(Spacer(1, 0.3*inch))
                story.append(Paragraph(title_text, title_style))
                
                # 제목 아래 구분선
                line_table = Table([['']], colWidths=[doc.width])
                line_table.setStyle(TableStyle([
                    ('LINEABOVE', (0, 0), (-1, 0), 3, ACCENT_COLOR),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(line_table)
                story.append(Spacer(1, 0.2*inch))
            else:
                story.append(Paragraph(title_text, h1_style))
            i += 1
            
        elif line.startswith('## '):
            title_text = line[3:].strip()
            title_text = clean_markdown_symbols(title_text)
            story.append(Paragraph(f'▸ {title_text}', h2_style))
            i += 1
            
        elif line.startswith('### '):
            title_text = line[4:].strip()
            title_text = clean_markdown_symbols(title_text)
            story.append(Paragraph(f'▪ {title_text}', h3_style))
            i += 1
            
        elif line.startswith('#### '):
            title_text = line[5:].strip()
            title_text = clean_markdown_symbols(title_text)
            story.append(Paragraph(f'• {title_text}', h4_style))
            i += 1
        
        # 수평선
        elif line.startswith('---') or line.startswith('___'):
            hr_table = Table([['']], colWidths=[doc.width])
            hr_table.setStyle(TableStyle([
                ('LINEABOVE', (0, 0), (-1, 0), 1, BORDER_COLOR),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(hr_table)
            i += 1
        
        # 리스트 처리
        else:
            list_type, content, level, *extra = parse_markdown_list_item(line) + (None,)
            
            if list_type in ['bullet', 'number']:
                content = clean_markdown_symbols(content)
                indent = 20 + (level * 20)
                
                if list_type == 'bullet':
                    bullet_char = '•' if level == 0 else ('◦' if level == 1 else '▪')
                    list_text = f'{bullet_char} {content}'
                else:
                    list_text = f'{extra[0]}. {content}'
                
                list_para_style = ParagraphStyle(
                    f'ListLevel{level}',
                    parent=bullet_style,
                    leftIndent=indent,
                    bulletIndent=indent - 10
                )
                story.append(Paragraph(list_text, list_para_style))
                i += 1
            else:
                # 일반 텍스트
                cleaned_line = clean_markdown_symbols(line)
                story.append(Paragraph(cleaned_line, body_style))
                i += 1
    
    # 인용구가 남아있으면 처리
    if in_quote and quote_lines:
        quote_text = '<br/>'.join(quote_lines)
        story.append(Paragraph(quote_text, quote_style))
    
    # 발행일 추가
    story.append(Spacer(1, 0.5*inch))
    date_table = Table(
        [[Paragraph(f"<i>보고서 생성일: {datetime.now().strftime('%Y년 %m월 %d일')}</i>", 
                   ParagraphStyle('DateStyle', parent=body_style, fontSize=10, 
                                textColor=colors.grey, alignment=TA_CENTER))]],
        colWidths=[doc.width]
    )
    date_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(date_table)
    
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
    ("system", """당신은 AI 분야의 시니어 리서처입니다.
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

REVIEW_BASELINE_REPORT = """
AI 보고서 요약 (미흡 예시 - 점수 5.8/10)

시장 전망
AI 시장은 빠르게 성장하고 있습니다. 많은 기업들이 이 분야에 투자하고 있으며, 향후 전망이 밝습니다.

기술 트렌드
- AI 기술
- 로봇 기술
- 센서 기술

산업 적용
제조, 물류, 헬스케어 등 다양한 산업에서 활용되고 있습니다.

권고사항
기업들은 AI 기술에 대한 투자를 고려해야 하며, 관련 인재를 확보하고 파트너십을 강화해야 합니다.
"""

REVIEW_STRONG_REPORT = """
AI 보고서 요약 (우수 예시 - 점수 8.9/10)

시장 전망
AI 시장은 2024년 3.78억 달러에서 2034년 67.91억 달러로 성장할 것으로 전망됩니다(CAGR 33.49%, Market.us 2024). 
- 북미 시장이 전체의 42%를 차지하며 선도적 위치
- 아시아태평양 지역은 가장 빠른 성장률(CAGR 38%)을 기록 예상
- 주요 성장 동력: 자동화 수요 증가, AI 칩 성능 향상, 클라우드 로보틱스 발전

기술 트렌드
1. Vision-Language-Action (VLA) 모델: Google의 RT-2, 1X의 EVE 등 멀티모달 foundation model이 로봇의 범용 작업 수행 능력을 획기적으로 향상
2. World Foundation Models: NVIDIA Cosmos, Google Genesis 등 물리 시뮬레이션 기반 합성 데이터 생성으로 학습 데이터 부족 문제 해결
3. 엣지 AI 가속화: Qualcomm RB6, NVIDIA Jetson Orin을 통한 온디바이스 추론으로 실시간 반응성 30% 개선

산업별 적용 사례
제조: Figure AI와 BMW 협력 사례 - South Carolina 공장에서 Figure 02 휴머노이드가 부품 조립 작업을 수행하며 생산성 25% 향상, 품질 불량률 15% 감소 (2024년 3분기 실증 결과)

물류: Amazon이 2024년 Proteus AMR(자율주행 로봇) 1,000대를 배포하여 물류센터 처리량 40% 증가 달성

헬스케어: Diligent Robotics의 Moxi가 미국 내 200개 이상 병원에서 간호사 업무 부담을 30% 경감 (약물/물품 배송 자동화)

권고사항
1. 단계별 투자 로드맵:
   - Phase 1 (6-12개월): RPA 기반 단순 작업 자동화로 ROI 검증 (예상 투자: $50K-200K)
   - Phase 2 (1-2년): AMR/협동로봇 도입으로 물류/조립 공정 최적화 (예상 투자: $500K-2M)
   - Phase 3 (2-3년): AI 기반 의사결정 및 휴머노이드 파일럿 (예상 투자: $2M+)

2. 핵심 파트너십 전략:
   - 하드웨어: Boston Dynamics, Agility Robotics와 POC 계약 체결
   - 소프트웨어: OpenAI, Covariant 등 AI 플랫폼 벤더와 라이선스 협상
   - 시스템 통합: Accenture, Deloitte의 SI 컨설팅 활용

3. 인재 확보 계획:
   - Robotics Engineer 2-3명, ML Engineer 3-5명 채용 (연봉 범위: $120K-180K)
   - UC Berkeley, CMU 등 주요 대학 연구실과 인턴십 프로그램 운영

참고 자료 및 출처
- Market.us, "Physical AI Market Forecast to 2034", 2024
URL: https://market.us/report/physical-ai-market
- Google Research, "RT-2: Vision-Language-Action Model for Robotics"
URL: https://ai.googleblog.com/2024/02/rt-2-vision-language-action-model-for.html
- NVIDIA, "Cosmos: AI-Driven Simulation for Robotics", 2024
URL: https://developer.nvidia.com/blog/cosmos-ai-driven-simulation-for-robotics/
"""

REVIEW_FEW_SHOT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 AI 전문 감수자입니다. 아래 5가지 기준(각 20점, 총 100점)으로 평가하고, 0-10점 사이 점수를 부여하세요.

평가 기준:

A. 내용 완성도 (20점)
- 18-20점: 모든 핵심 질문을 깊이 있게 다루며 추가 인사이트 제공
- 14-17점: 대부분의 질문을 충실히 답하나 일부 영역에서 깊이 부족
- 10-13점: 기본적인 내용은 포함하나 표면적 수준
- 0-9점: 주요 질문이 누락되거나 내용이 불충분

B. 데이터 정확성 (20점)
- 18-20점: 검증 가능한 최신 데이터와 명확한 출처 제시
- 14-17점: 대체로 정확하나 일부 출처 미비
- 10-13점: 정성적 서술 위주, 수치 근거 부족
- 0-9점: 부정확한 정보 포함 또는 출처 없음

C. 구조 논리성 (20점)
- 18-20점: 매끄러운 전개와 명확한 논리적 연결
- 14-17점: 전반적으로 체계적이나 일부 중복/비약
- 10-13점: 구조는 있으나 섹션 간 연결 약함
- 0-9점: 비체계적이거나 논리적 흐름 부재

D. 실행 가능성 (20점)
- 18-20점: 재무/기술/파트너십 등 구체적 실행 지침 제공
- 14-17점: 방향성은 명확하나 세부 단계 부족
- 10-13점: 추상적 권고안 수준
- 0-9점: 실행 가능한 제안 없음

E. 전문성 (20점)
- 18-20점: 업계 전문가 수준의 통찰과 용어 활용
- 14-17점: 기본적인 전문성은 갖추었으나 차별화 부족
- 10-13점: 일반적 수준의 분석
- 0-9점: 전문성 결여

응답 형식:
점수: x.x/10 (총점: yy/100)

세부 평가:
- A. 내용 완성도: xx/20점 - ...
- B. 데이터 정확성: xx/20점 - ...
- C. 구조 논리성: xx/20점 - ...
- D. 실행 가능성: xx/20점 - ...
- E. 전문성: xx/20점 - ..."""),
    
    ("human", """평가 대상 보고서 (미흡 예시):
{baseline_report}"""),
    
    ("assistant", """점수: 5.8/10 (총점: 58/100)

세부 평가:
- A. 내용 완성도: 11/20점 - 핵심 영역(시장, 기술, 산업, 권고)을 언급했으나 각 영역의 깊이가 매우 부족하고 표면적입니다. "빠르게 성장"과 같은 모호한 표현만 있고 구체적인 답변이 없습니다.

- B. 데이터 정확성: 8/20점 - 단 하나의 수치나 출처도 제시하지 않았습니다. "많은 기업들", "다양한 산업" 등 검증 불가능한 정성적 서술만 존재합니다. 데이터 기반 의사결정이 불가능한 수준입니다.

- C. 구조 논리성: 12/20점 - 기본적인 섹션 구분은 있으나 각 섹션이 2-3줄로 매우 짧고, 시장 전망과 기술 트렌드, 산업 적용이 서로 연결되지 않습니다. 요약-본문-결론의 구조가 없습니다.

- D. 실행 가능성: 10/20점 - 권고사항이 "투자를 고려해야 한다", "인재를 확보해야 한다"는 수준으로 당위성만 제시합니다. 투자 규모, 시기, 우선순위, 구체적 파트너 후보, 채용 직무/인원 등 실무 지침이 전혀 없습니다.

- E. 전문성: 17/20점 - "AI 기술", "로봇 기술", "센서 기술"처럼 일반인도 아는 수준의 용어만 사용합니다. VLA, AMR, RPA, 휴머노이드 등 업계 전문 용어가 없고, 통찰이나 트렌드 분석이 결여되어 있습니다."""),
    
    ("human", """평가 대상 보고서 (우수 예시):
{strong_report}"""),
    
    ("assistant", """점수: 8.9/10 (총점: 89/100)

세부 평가:
- A. 내용 완성도: 18/20점 - 시장, 기술, 산업, 권고 모든 영역을 깊이 있게 다루었습니다. 시장 섹션은 금액/성장률/지역별 분석, 기술 섹션은 3가지 주요 트렌드와 실제 제품, 산업 섹션은 3개 산업별 정량 성과를 제시했습니다. 2점 감점 사유는 도전과제/위험 관리 영역이 상대적으로 약하기 때문입니다.

- B. 데이터 정확성: 17/20점 - 다수의 수치(시장 규모 $67.91B, CAGR 33.49%, 생산성 25% 향상, 물류 처리량 40% 증가)와 구체적인 사례(BMW 공장, Amazon AMR 1,000대)를 제시했습니다. 출처는 일부 명시(Market.us 2024)했으나 모든 데이터에 대한 출처가 필요하고, 참고문헌 전체 목록이 없어 3점 감점했습니다.

- C. 구조 논리성: 18/20점 - 시장 전망 → 기술 기반 → 산업 적용 → 실행 권고로 이어지는 논리적 흐름이 매끄럽습니다. 각 섹션이 다음 섹션의 근거가 되며, 권고사항이 앞서 제시한 시장/기술 분석과 정렬됩니다. 2점 감점 사유는 결론/요약 섹션이 없어 전체를 아우르는 마무리가 부족하기 때문입니다.

- D. 실행 가능성: 19/20점 - 3단계 투자 로드맵에 각 단계별 기간, 투자 규모($50K-$2M+), 구체적 기술(RPA, AMR, 휴머노이드), 파트너 후보(Boston Dynamics, OpenAI, Accenture), 채용 인원(2-3명, 3-5명)과 연봉($120K-$180K)까지 제시하여 즉시 실무에 활용 가능합니다. 1점 감점 사유는 각 단계의 성공/실패 기준(KPI)이 명시되지 않았기 때문입니다.

- E. 전문성: 17/20점 - VLA, World Foundation Models, AMR, POC, SI 등 업계 전문 용어를 정확히 사용하고, RT-2, EVE, Cosmos, Proteus 등 최신 제품명을 언급했습니다. UC Berkeley, CMU 같은 연구 기관까지 구체적으로 제시하여 도메인 지식이 풍부합니다. 3점 감점 사유는 일부 약어(AMR, RPA)에 대한 첫 언급 시 풀네임 병기가 없고, 기술적 깊이(예: VLA 모델의 아키텍처)가 더 있으면 전문성이 높아질 것이기 때문입니다."""),
    
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
            #print(f"✅ 성공! 결과 타입: {type(result)}")
            
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
            print(f"🔖 {area} 핵심 질문: {area_plan.focus_question}")
        state["messages"].append("✅ LLM 기반 리서치 계획 수립 완료")
        print("✅ 리서치 계획: 수립완료")
        overview = plan.plan_overview.strip()
        if overview:
            state["messages"].append(f"🧭 계획 요약: {overview}")
        print(f"🧭 계획 요약: {overview}")
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
        ("system", """당신은 AI 전문 분석가입니다.
        Tavily AI가 제공한 답변과 상세 데이터를 종합하여 핵심 인사이트를 추출하세요.
        각 영역별로 가장 중요한 트렌드 3-5가지를 구체적 수치와 함께 제시하세요."""),
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
                    f"- {top_result.get('title', '')}: {top_result.get('content', '')[:200]}"
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
        if total == 0:
            failing_metrics.append("items")
        if hits == 0:
            failing_metrics.append("coverage")
        if answers == 0:
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
    """보고서 초안 생성 - 공식적이고 정형화된 트렌드 분석 보고서 양식"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    sections = {
        "executive_summary": "핵심 요약",
        "market_overview": "시장 전망",
        "technology_trends": "기술 트렌드",
        "industry_applications": "산업별 응용",
        "key_players": "주요 기업",
        "challenges": "도전과제",
        "forecast": "향후 5년 전망",
        "recommendations": "전략적 권고사항",
        "conclusion": "결론"
    }

    # 섹션별 상세 작성 가이드라인
    section_guidelines = {
        "executive_summary": """
        - 보고서 전체의 핵심 내용을 3-5개의 주요 포인트로 요약
        - 시장 규모, 성장률(CAGR) 등 핵심 수치를 반드시 포함
        - 주요 트렌드와 기술 혁신을 간략히 언급
        - 전략적 시사점을 1-2문장으로 제시
        """,
        "market_overview": """
        - 현재 시장 규모와 예측 시장 규모를 구체적인 금액($)으로 제시
        - CAGR(연평균 성장률) 수치와 기간 명시
        - 지역별 시장 비중(북미, 유럽, 아시아태평양 등) 백분율로 제시
        - 주요 성장 동력(예: 자동화 수요, AI 칩 발전 등)을 3-4가지 나열
        - 가능한 경우 출처(예: Market.us 2024, IDC 2025) 명시
        """,
        "technology_trends": """
        - 핵심 기술 트렌드를 3-5개 선정하여 각각 상세 설명
        - 각 기술별로 실제 제품명이나 프로젝트명 언급(예: Google RT-2, NVIDIA Cosmos)
        - 기술적 성능 개선 수치를 포함(예: 정확도 30% 향상, 지연시간 50ms 단축)
        - 업계 전문 용어 적극 활용(VLA, AMR, Edge AI, Foundation Model 등)
        - 각 기술의 산업적 의의와 적용 가능성 설명
        """,
        "industry_applications": """
        - 최소 3개 이상의 주요 산업 분야 다루기(제조, 물류, 헬스케어, 자율주행 등)
        - 각 산업별로 구체적인 사례 제시(기업명, 프로젝트명 포함)
        - 정량적 성과 지표 포함(예: 생산성 25% 향상, 물류 처리량 40% 증가)
        - 실증 데이터나 파일럿 프로젝트 결과 언급
        - 각 산업에서의 도입 단계(초기/성장/성숙) 평가
        """,
        "key_players": """
        - 주요 기업 5-7개를 선정하여 각각의 전략과 제품 소개
        - 최근 투자 유치 금액, 파트너십, M&A 정보 포함
        - 각 기업의 기술적 차별점과 시장 포지셔닝 설명
        - 스타트업과 대기업을 구분하여 분석
        - 주요 제품의 구체적인 스펙이나 성능 지표 언급
        """,
        "challenges": """
        - 기술적 과제(예: 배터리, 정밀도, 안전성) 3-4가지
        - 비즈니스 장벽(예: 높은 초기 비용, ROI 불확실성) 2-3가지
        - 규제 및 윤리적 이슈(예: 안전 규제, 일자리 대체) 1-2가지
        - 각 과제에 대한 현재 해결 시도나 대안 언급
        - 향후 해결 전망과 예상 시점 제시
        """,
        "forecast": """
        - 향후 5년간의 단계적 발전 시나리오 제시
        - 연도별 주요 마일스톤 예측(예: 2026년 대량 배포, 2028년 표준화)
        - 시장 침투율 전망(예: 2030년까지 제조업의 30% 도입)
        - 기술 성숙도 로드맵(초기→성장→성숙 단계)
        - 낙관적/보수적 시나리오 구분 제시
        """,
        "recommendations": """
        - 3단계 실행 로드맵 제시(Phase 1/2/3, 각 단계별 기간 명시)
        - 각 단계별 예상 투자 규모($50K-$2M+ 등 구체적 범위)
        - 핵심 파트너십 전략(구체적인 벤더명이나 SI 업체명 제시)
        - 인재 확보 계획(직무, 인원, 예상 연봉 범위 포함)
        - 각 단계별 기대 효과와 ROI 목표 제시
        - 성공 측정 지표(KPI) 제안
        """,
        "conclusion": """
        - 보고서의 핵심 메시지를 3-4문장으로 요약
        - Physical AI의 전략적 중요성 강조
        - 조직이 취해야 할 즉각적 행동 1-2가지 제시
        - 미래 전망에 대한 간결한 견해 제시
        """
    }

    report_sections = {}

    for section_key, section_title in sections.items():
        guidelines = section_guidelines.get(section_key, "")

        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""당신은 AI 분야의 시니어 애널리스트입니다.
'{section_title}' 섹션을 공식적이고 정형화된 산업 트렌드 분석 보고서 양식에 맞춰 작성하세요.

**필수 요구사항:**
- 섹션 제목을 포함하지 말고 본론만 작성하세요
- synthesis_node에서 추출한 핵심 인사이트를 최대한 활용하세요
- 구체적인 수치, 통계, 금액을 반드시 포함하세요
- 실제 기업명, 제품명, 프로젝트명을 적극 언급하세요
- 업계 전문 용어를 정확하게 사용하세요
- 출처나 시기를 함께 제시하여 신뢰도를 높이세요
- 정성적 서술보다는 정량적 데이터 기반으로 작성하세요

**섹션별 작성 가이드라인:**
{guidelines}

**작성 스타일:**
- 문장은 명확하고 간결하게 (1문장 2줄 이내)
- 각 주장에 대한 근거(수치, 사례, 출처)를 반드시 제시
- 추상적 표현(많은, 빠른, 중요한 등) 지양하고 구체적 표현 사용

이 섹션은 전체 보고서의 일부이므로, 제공된 분석 데이터를 충분히 활용하여 전문성 있고 실행 가능한 내용으로 작성하세요."""),
            ("user", """분석 데이터:
{data}

위 데이터에서 추출한 핵심 인사이트를 바탕으로 '{section_title}' 섹션을 작성하세요.
가능한 모든 구체적인 수치, 기업명, 제품명, 사례를 포함하세요.""")
        ])

        response = llm.invoke(
            prompt.format_messages(
                data=str(state["synthesized_data"]),
                section_title=section_title,
                guidelines=guidelines
            )
        )
        report_sections[section_key] = response.content

    state["report_sections"] = report_sections
    state["messages"].append("✅ 보고서 초안 생성 완료 (정형화된 트렌드 분석 양식 적용)")
    return state

def extract_sources_from_data(state: AgentState) -> str:
    """수집된 데이터에서 출처 URL 추출"""
    sources = []
    seen_urls = set()
    
    for category in ["market_data", "tech_data", "industry_data", "company_data", "challenge_data"]:
        data_list = state.get(category, [])
        for item in data_list:
            results = item.get("results", [])
            for result in results[:2]:  # 상위 2개 결과만
                url = result.get("url", "")
                title = result.get("title", "")
                if url and url not in seen_urls:
                    sources.append(f"- [{title}]({url[:10]})")
                    seen_urls.add(url)
    
    return "\n".join(sources[:40]) if sources else "- Tavily AI Search API를 통해 수집된 다양한 온라인 소스"

def structure_node(state: AgentState) -> AgentState:
    """보고서 구조화 및 포맷팅 (결론, 출처, 평가기준 포함)"""
    sections = state["report_sections"]
    
    # 출처 자동 추출
    sources = extract_sources_from_data(state)
    
    # Markdown 형식으로 보고서 구조화
    final_report = f"""

# 2026-2030 AI 산업 트렌드 분석 보고서

## 핵심 요약

{sections.get("executive_summary", "")}

---

## 시장 전망

{sections.get("market_overview", "")}

---

## 기술 트렌드

{sections.get("technology_trends", "")}

---

## 산업별 응용

{sections.get("industry_applications", "")}

---

## 주요 기업

{sections.get("key_players", "")}

---

## 도전 과제

{sections.get("challenges", "")}

---

## 향후 5년 전망

{sections.get("forecast", "")}

---

## 전략적 권고사항

{sections.get("recommendations", "")}

---

## 결론

{sections.get("conclusion", "")}

---

## 참고 자료 및 출처

본 보고서는 다음의 자료를 참고하여 작성되었습니다:

{sources}

**데이터 수집 방법:**
- Tavily AI Advanced Search API를 활용한 실시간 웹 검색
- 업계 보고서, 뉴스 기사, 기업 발표 자료 등 다양한 공개 소스 분석
- AI 기반 정보 종합 및 트렌드 분석

---

## Appendix: 보고서 품질 평가 기준

본 보고서는 다음 5가지 기준으로 품질을 평가합니다:

### A. 내용 완성도 (20점 만점)
- 핵심 질문에 대한 명확한 답변 제시
- 각 섹션의 깊이와 포괄성
- 논리적 전개와 일관성

### B. 데이터 정확성 (20점 만점)
- 수치와 통계의 정확성 및 최신성
- 출처의 신뢰도와 명확성
- 팩트 체크 수준

### C. 구조 논리성 (20점 만점)
- 섹션 간 연결성과 흐름
- 목차 구성의 체계성
- 요약-본문-결론의 정합성

### D. 실행 가능성 (20점 만점)
- 권고사항의 구체성
- 실무 적용 가능성
- 실행 로드맵 제시 여부

### E. 전문성 (20점 만점)
- 업계 용어와 개념 활용 수준
- 통찰의 깊이와 독창성
- 전문 리포트로서의 완성도

"""
    
    state["final_report"] = final_report
    state["messages"].append("✅ 보고서 구조화 완료 (목차, 결론, 출처, 평가기준 포함)")
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
    state["quality_score"] = score
    state["final_report"] += f"\n\n---\n\n## 보고서 품질 검토 결과\n\n{content}"
    state["final_report"] += f"*보고서 생성일: {__import__('datetime').datetime.now().strftime('%Y년 %m월 %d일')}*\n*생성 시스템: Physical AI Trend Report Generator (Powered by LangGraph + Tavily AI)*"
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

    # review_feedback 가져오기
    review_feedback = state.get("search_context", {}).get("review_feedback", "리뷰 피드백 없음")

    prompt = ChatPromptTemplate.from_messages([
        ("system", """보고서를 개선하세요. 다음에 집중하세요:
        1. 구체적인 수치 및 데이터 추가
        2. 실행 가능한 권고사항 강화
        3. 논리적 흐름 개선

품질 검토 피드백:
{review_feedback}

위 피드백을 참고하여 지적된 문제점을 개선하세요."""),
        ("user", "현재 보고서:\n{report}\n\n분석 데이터:\n{data}")
    ])

    response = llm.invoke(
        prompt.format_messages(
            review_feedback=review_feedback,
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
        pdf_filename = f"Ai_report_{timestamp}.pdf"
        markdown_to_pdf(state["final_report"], pdf_filename)
        state["messages"].append(f"📄 PDF 보고서 생성 완료: {pdf_filename}")
    except Exception as e:
        state["messages"].append(f"⚠️ PDF 생성 실패: {str(e)}")
    
    return state

# ==================== 그래프 구성 ====================

def create_physical_ai_agent():
    """AI 보고서 생성 에이전트 그래프 생성"""
    
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
    
    print("🚀 AI 트렌드 보고서 생성 시작...")
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
    
    query = "향후 5년 이내 기업에서 관심있게 봐야할 AI 트렌드"
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║         AI 트렌드 보고서 생성 에이전트              ║
║              Powered by LangGraph + Tavily                   ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    result = run_agent(query)
    
    if result:
        # 보고서를 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Ai_report_{timestamp}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(result["final_report"])
        
        print(f"\n💾 보고서가 저장되었습니다: {filename}")