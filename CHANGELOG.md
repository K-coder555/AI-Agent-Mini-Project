# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 계획된 기능
- [ ] 다국어 지원 (영어, 일본어)
- [ ] 웹 대시보드 UI
- [ ] 차트 및 그래프 자동 생성
- [ ] 커스텀 템플릿 지원
- [ ] 실시간 업데이트 기능
- [ ] API 서버 모드

## [1.0.0] - 2025-01-23

### Added
- 🎉 최초 릴리스
- LangGraph 기반 멀티 노드 워크플로우 구현
- Tavily AI 통합으로 실시간 웹 검색 기능
- 5개 도메인 병렬 리서치 (시장, 기술, 산업, 기업, 도전과제)
- AI 기반 품질 평가 시스템 (10점 만점)
- Few-shot Learning을 활용한 보고서 검토
- 자동 개선 루프 (점수 7.0 미만 시 재생성)
- 전문적인 PDF 보고서 생성 (한글 지원)
- 다채로운 색상 팔레트와 공식 문서 스타일
- 페이지 번호, 목차, 출처 자동 삽입
- 보고서 품질 평가 기준 (5가지 기준, 각 20점)

### Core Features
- **Planning Node**: 조사 계획 수립
- **Research Nodes**: 
  - Market Research (시장 조사)
  - Tech Research (기술 조사)
  - Industry Research (산업 조사)
  - Company Research (기업 조사)
  - Challenge Research (도전과제 조사)
- **Synthesis Node**: 데이터 통합 및 분석
- **Report Generation Node**: 섹션별 보고서 작성
- **Structure Node**: 목차, 결론, 출처 추가
- **Review Node**: AI 품질 평가
- **Refinement Node**: 피드백 기반 개선
- **Formatting Node**: PDF 생성

### Technical Stack
- Python 3.8+
- LangGraph 0.0.20+
- LangChain 0.1.0+
- OpenAI GPT-4o-mini
- Tavily Search API
- ReportLab 4.0.0+

### Documentation
- README.md: 프로젝트 소개 및 사용법
- CONTRIBUTING.md: 기여 가이드
- PROJECT_STRUCTURE.md: 프로젝트 구조 설명
- example.py: 사용 예제 코드

### Configuration
- .env.example: 환경 변수 템플릿
- requirements.txt: Python 패키지 의존성
- .gitignore: Git 제외 파일 목록

### License
- MIT License

---

## Version History

### v1.0.0 (2025-01-23) - Initial Release
첫 번째 안정 버전 릴리스. Physical AI 트렌드 보고서를 자동으로 생성하는 모든 핵심 기능 포함.

**주요 통계:**
- 코드 라인 수: ~1,600 lines
- 평균 보고서 생성 시간: 1.5-2분
- 평균 보고서 길이: 10페이지
- 평균 품질 점수: 8.5/10
- API 비용 (보고서당): $0.10-0.30

**지원 환경:**
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 20.04+)

---

## How to Read This Changelog

### 버전 번호 체계
- **Major (X.0.0)**: 하위 호환성이 없는 주요 변경
- **Minor (1.X.0)**: 하위 호환성이 있는 새로운 기능
- **Patch (1.0.X)**: 하위 호환성이 있는 버그 수정

### 변경 유형
- **Added**: 새로운 기능
- **Changed**: 기존 기능의 변경
- **Deprecated**: 곧 제거될 기능
- **Removed**: 제거된 기능
- **Fixed**: 버그 수정
- **Security**: 보안 이슈 수정

---

## Upgrade Guide

### 1.0.0으로 업그레이드

이것이 첫 번째 릴리스이므로 업그레이드 가이드가 없습니다.

향후 버전으로 업그레이드할 때는:

```bash
# 1. 저장소 업데이트
git pull origin main

# 2. 의존성 업데이트
pip install -r requirements.txt --upgrade

# 3. 환경 변수 확인
# .env.example과 비교하여 새로운 변수 추가
```

---

## Support

문제가 발생하거나 질문이 있으신가요?

- 🐛 버그 리포트: [GitHub Issues](https://github.com/yourusername/physical-ai-report-generator/issues)
- 💬 토론: [GitHub Discussions](https://github.com/yourusername/physical-ai-report-generator/discussions)
- 📧 이메일: your.email@example.com

---

## Contributors

이 프로젝트에 기여해주신 모든 분들께 감사드립니다! ❤️

<!-- 
Contributors will be added here as they contribute:
- @username1
- @username2
-->

---

**[Unreleased]**: https://github.com/yourusername/physical-ai-report-generator/compare/v1.0.0...HEAD
**[1.0.0]**: https://github.com/yourusername/physical-ai-report-generator/releases/tag/v1.0.0
