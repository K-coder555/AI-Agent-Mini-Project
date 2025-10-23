# Contributing to Physical AI Report Generator

Physical AI Report Generator 프로젝트에 기여해주셔서 감사합니다! 🎉

이 문서는 프로젝트에 기여하는 방법을 안내합니다.

## 📋 목차

- [행동 강령](#행동-강령)
- [시작하기](#시작하기)
- [개발 환경 설정](#개발-환경-설정)
- [기여 방법](#기여-방법)
- [코드 스타일](#코드-스타일)
- [커밋 메시지 가이드](#커밋-메시지-가이드)
- [Pull Request 프로세스](#pull-request-프로세스)

## 행동 강령

이 프로젝트는 기여자들이 서로 존중하고 협력하는 환경을 만들기 위해 노력합니다. 모든 기여자는:

- 다른 사람을 존중합니다
- 건설적인 피드백을 제공합니다
- 다양한 관점을 환영합니다
- 프로젝트의 목표에 집중합니다

## 시작하기

### 필요한 것

- Python 3.8 이상
- Git
- GitHub 계정
- OpenAI API 키
- Tavily API 키

### 저장소 Fork 및 Clone

```bash
# 1. GitHub에서 저장소 Fork

# 2. 로컬에 Clone
git clone https://github.com/YOUR_USERNAME/physical-ai-report-generator.git
cd physical-ai-report-generator

# 3. 원본 저장소를 upstream으로 추가
git remote add upstream https://github.com/ORIGINAL_OWNER/physical-ai-report-generator.git
```

## 개발 환경 설정

### 1. 가상환경 생성

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. 개발 의존성 설치

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 개발 도구
```

### 3. Pre-commit 훅 설정 (선택사항)

```bash
pip install pre-commit
pre-commit install
```

### 4. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일에 API 키 입력
```

## 기여 방법

### 버그 리포트

버그를 발견하셨나요? [Issue](https://github.com/yourusername/physical-ai-report-generator/issues)를 생성해주세요.

**좋은 버그 리포트에는 다음이 포함됩니다:**

- 명확한 제목
- 재현 단계
- 예상 동작 vs 실제 동작
- 에러 메시지 (있는 경우)
- 환경 정보 (OS, Python 버전 등)

### 기능 제안

새로운 기능을 제안하고 싶으신가요?

1. 먼저 [Issues](https://github.com/yourusername/physical-ai-report-generator/issues)에서 유사한 제안이 있는지 확인
2. 없다면 새로운 Issue 생성
3. 제안하는 기능의 목적과 사용 사례를 명확히 설명

### 코드 기여

1. **Issue 선택**
   - [Good First Issue](https://github.com/yourusername/physical-ai-report-generator/labels/good%20first%20issue) 라벨 확인
   - 작업할 Issue를 선택하고 코멘트로 의사 표시

2. **브랜치 생성**
   ```bash
   git checkout -b feature/your-feature-name
   # 또는
   git checkout -b fix/bug-description
   ```

3. **코드 작성**
   - 코드 스타일 가이드 준수
   - 테스트 추가 (필요시)
   - 문서 업데이트

4. **테스트**
   ```bash
   # 단위 테스트 실행
   pytest tests/
   
   # 코드 스타일 체크
   flake8 .
   black --check .
   ```

5. **커밋**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

6. **Push 및 PR 생성**
   ```bash
   git push origin feature/your-feature-name
   ```
   - GitHub에서 Pull Request 생성
   - PR 템플릿에 따라 설명 작성

## 코드 스타일

### Python 스타일 가이드

이 프로젝트는 [PEP 8](https://www.python.org/dev/peps/pep-0008/)을 따릅니다.

```python
# 좋은 예
def calculate_market_size(data: Dict[str, Any]) -> float:
    """
    시장 규모를 계산합니다.
    
    Args:
        data: 시장 데이터 딕셔너리
        
    Returns:
        계산된 시장 규모 (억 달러)
    """
    return sum(item['value'] for item in data['items'])


# 나쁜 예
def calc(d):
    return sum(i['value'] for i in d['items'])
```

### 포매팅 도구

```bash
# Black으로 자동 포매팅
black physical_ai_agent.py

# isort로 import 정렬
isort physical_ai_agent.py
```

### 문서화

- 모든 함수에 docstring 추가
- 타입 힌트 사용
- 복잡한 로직에는 주석 추가

```python
def process_data(
    raw_data: List[Dict[str, Any]], 
    threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    원시 데이터를 처리하고 필터링합니다.
    
    Args:
        raw_data: 처리할 원시 데이터 리스트
        threshold: 필터링 임계값 (기본값: 0.5)
        
    Returns:
        처리된 데이터 리스트
        
    Raises:
        ValueError: raw_data가 비어있을 때
    """
    if not raw_data:
        raise ValueError("raw_data cannot be empty")
    
    # 임계값 이상의 항목만 선택
    return [item for item in raw_data if item['score'] >= threshold]
```

## 커밋 메시지 가이드

[Conventional Commits](https://www.conventionalcommits.org/) 형식을 사용합니다.

### 형식

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 스타일 변경 (포매팅, 세미콜론 등)
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가 또는 수정
- `chore`: 빌드 프로세스 또는 도구 변경

### 예시

```bash
# 좋은 예
feat(research): add multi-language support for reports
fix(pdf): resolve font rendering issue in Korean text
docs(readme): update installation instructions

# 나쁜 예
update code
fix bug
changes
```

## Pull Request 프로세스

### PR 체크리스트

PR을 제출하기 전에 확인하세요:

- [ ] 코드가 스타일 가이드를 준수합니다
- [ ] 모든 테스트가 통과합니다
- [ ] 새로운 기능에 대한 테스트를 추가했습니다
- [ ] 문서를 업데이트했습니다
- [ ] CHANGELOG.md를 업데이트했습니다
- [ ] 커밋 메시지가 컨벤션을 따릅니다

### PR 템플릿

```markdown
## 변경 사항
<!-- 무엇을 변경했는지 간단히 설명 -->

## 관련 Issue
<!-- Closes #123 -->

## 변경 유형
- [ ] 버그 수정
- [ ] 새로운 기능
- [ ] 문서 업데이트
- [ ] 코드 리팩토링

## 테스트
<!-- 어떻게 테스트했는지 설명 -->

## 스크린샷 (해당시)
<!-- 시각적 변경사항이 있다면 스크린샷 첨부 -->

## 추가 정보
<!-- 기타 리뷰어가 알아야 할 내용 -->
```

### 리뷰 프로세스

1. PR 생성 후 자동 CI/CD 실행
2. 메인테이너가 코드 리뷰
3. 피드백 반영 및 수정
4. 승인 후 메인 브랜치에 병합

## 개발 워크플로우

### 브랜치 전략

- `main`: 안정적인 프로덕션 코드
- `develop`: 개발 브랜치 (다음 릴리스 준비)
- `feature/*`: 새로운 기능
- `fix/*`: 버그 수정
- `docs/*`: 문서 업데이트

### 릴리스 프로세스

1. `develop` 브랜치에서 기능 개발
2. 릴리스 준비가 되면 `release/*` 브랜치 생성
3. 버그 수정 및 문서 업데이트
4. `main`과 `develop`에 병합
5. 버전 태그 생성

## 테스트 작성

### 단위 테스트

```python
# tests/test_synthesis.py
import pytest
from physical_ai_agent import synthesis_node

def test_synthesis_with_valid_data():
    """유효한 데이터로 synthesis 테스트"""
    state = {
        "market_data": [{"title": "Test", "content": "Data"}],
        "tech_data": [{"title": "Tech", "content": "Info"}],
        # ... 기타 필드
    }
    
    result = synthesis_node(state)
    
    assert "synthesized_data" in result
    assert result["synthesized_data"]["market_summary"]


def test_synthesis_with_empty_data():
    """빈 데이터로 synthesis 테스트"""
    state = {
        "market_data": [],
        "tech_data": [],
        # ...
    }
    
    result = synthesis_node(state)
    
    # 빈 데이터 처리 로직 검증
    assert result["messages"][-1].startswith("⚠️")
```

### 통합 테스트

```python
# tests/test_integration.py
def test_full_pipeline():
    """전체 파이프라인 통합 테스트"""
    query = "Test query for Physical AI trends"
    result = run_agent(query)
    
    assert result is not None
    assert result["final_report"]
    assert result["quality_score"] > 0
```

## 질문이 있으신가요?

- [GitHub Issues](https://github.com/yourusername/physical-ai-report-generator/issues)에 질문 올리기
- [GitHub Discussions](https://github.com/yourusername/physical-ai-report-generator/discussions)에서 토론하기

---

다시 한번 기여해주셔서 감사합니다! 🙏

여러분의 기여가 이 프로젝트를 더욱 발전시킵니다. ✨
