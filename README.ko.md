# opus-mind

`CLAUDE.md` 같은 시스템 프롬프트 채점기. [CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S)에
유출된 1,408줄 Opus 4.7 시스템 프롬프트에서 규칙을 뽑았다. Claude Code
스킬로도, CLI로도 쓸 수 있음. 모든 규칙이 원전의 특정 줄에 앵커돼
있고, 채점 엔진은 regex + 카운트 — LLM은 안 부름.

```
$ opus-mind lint audit ~/.claude/CLAUDE.md
score: 10/11   verdict: BORDERLINE
  [FAIL] I6  failure_modes_explicit   consequence 0개, 최소 1개 필요

  L42 'the bot must cite sources' — consequence 안 붙음
```

같은 스킬에 두 번째 도구도 있음. 프롬프트 엔지니어링의 반대편 — 네가
매일 Claude / ChatGPT / Cursor에 보내는 일회성 프롬프트 코칭:

```
$ opus-mind boost check "write a blog post about AI safety"
coverage: 1/10    task_type: write

비어있음, 임팩트 순위:
  [ ] B4 context        'write' 태스크는 대상 독자가 가장 중요
  [ ] B6 constraints    톤 / 피할 것
  [ ] B3 length         300 단어 / 불릿 5개 / 200 토큰 이하
  ...
```

**English**: [README.md](./README.md)

```
    LINT — 시스템 프롬프트                   BOOST — 유저 프롬프트
    ──────────────────────                   ──────────────────────
    CLAUDE.md / AGENTS.md                   LLM에 보내는 프롬프트
    .cursorrules / SKILL.md                 "블로그 글 써줘..."

    11개 구조 불변식                         10개 슬롯 (스펙 7 + 추론 3)
    에이전트 설계 품질 감사                  요청 명확도 감사
    커밋 게이트                              프롬프터 코칭
```

---

## 왜 만들었나

내 `CLAUDE.md`가 녹슬었다. 처음엔 규칙이 쨍했는데, 모델이 추천한 줄
붙여넣기를 반복하다 보니 어느 순간 `never X`가 `typically avoid X`로
바뀌어 있었다. 리뷰어도 없고, "좋은 프롬프트"의 객관 기준도 없었다.

유출된 Opus 4.7 프롬프트가 그 기준이었다. 1,408줄. Anthropic이 자기
대표 모델에 쏟은 규칙. 프로덕션 프롬프트에 필요한 패턴 — 형용사 대신
hard number, 무순위 리스트 대신 decision ladder, jailbreak drift 잡는
reframe-as-signal — 다 들어있고 다 calibrated. 그 패턴을 뽑고, 존재
여부를 탐지하는 regex를 짜서, linter로 포장했다.

BOOST는 나중에 왔다. 같은 엔진 아이디어를 다른 대상에 — 내가 안 쓴
시스템 프롬프트를 채점하는 게 아니라, 내가 **지금 쓰는** 채팅
프롬프트를 코칭하는 쪽. 모호한 프롬프트를 좋은 프롬프트로 만드는 10개
슬롯을 가리킨다.

---

## 설치

Claude Code 안에서 (추천):

```bash
git clone https://github.com/Hybirdss/opus-mind
cd opus-mind
bash skills/opus-mind/scripts/install-skill.sh
```

Claude Code 재시작 후 그냥 말 걸면 됨 — "내 CLAUDE.md 감사해줘", "내
봇이 거절 후에 굽힌다", "이 프롬프트 좋게 만들어줘". Claude가 스킬
읽고, 헬퍼 돌리고, 응답을 합성한다. API 키 불필요 — 이미 Claude랑
말하고 있으니까.

독립 CLI (pre-commit 훅, CI, 스크립트):

```bash
opus_mind=skills/opus-mind/scripts/opus-mind

$opus_mind lint audit path/to/CLAUDE.md        # 점수 + 지적사항
$opus_mind lint critic path/to/CLAUDE.md       # audit → fix → re-audit 루프
$opus_mind lint seed --type customer-bot       # 9+/11 나오는 스켈레톤

$opus_mind boost check "프롬프트 여기"
$opus_mind boost ask   "프롬프트 여기"         # 한 번에 질문 하나
$opus_mind boost expand "프롬프트" --length "300 단어" --format markdown
```

커밋 임계값 게이트:

```bash
bash skills/opus-mind/scripts/install-hook.sh --threshold 6
```

---

## 뭘 잡아내나

**LINT — 11 불변식.** 모든 신호가 Opus 4.7 원전의 특정 줄에 앵커.

| ID | 체크 | 원전 |
|---|---|---|
| I1  | hedge 비율 ≤ 0.25, 숫자 비율 ≥ 0.10 | L664, L620 |
| I2  | 라우팅 분기에 `Step N → ...` ladder | L515–L537 |
| I3  | refusal 있으면 reframe-as-signal 조항 | L33 |
| I4  | narration 서두 ("Let me check" 등) 0개 | L536, L560 |
| I5  | 예시마다 rationale 부착 | L710–L750 |
| I6  | directive 대비 consequence 문장 | L753–L759 |
| I7  | `{foo}…{/foo}` 블록 모두 닫힘 | 구조적 |
| I8  | default + exception 근접 공존 | L25, L57–68 |
| I9  | 긴 프롬프트엔 self-check 블록 | L698–L707 |
| I10 | 고위험 규칙엔 ALLCAPS tier label | L640, L657 |
| I11 | Tier 체인 / hierarchical override | L657 |

통과/실패 외에 두 가지 더: `verdict` enum (THIN / POOR / BORDERLINE /
GOOD), placeholder 카운트 — `<FIXME>`, `[TODO]`, `TBD`, `???`, `XXX`
잔재가 있으면 11개 구조 체크가 다 통과해도 GOOD 못 받음.

**BOOST — 10 슬롯.** 스펙 층 (B1–B7)은 Anthropic 공식 prompt
engineering 문서에, 추론 층 (B8–B10)은
`evidence/smart-prompting-refs.md`에 앵커.

| ID | 슬롯 | 출처 |
|---|---|---|
| B1  | task                 | Anthropic 문서 |
| B2  | format               | Anthropic 문서 |
| B3  | length               | Anthropic 문서 |
| B4  | context              | Anthropic 문서 |
| B5  | few-shot             | Anthropic 문서 |
| B6  | constraints          | Anthropic 문서 |
| B7  | clarify              | Anthropic 문서 |
| B8  | reasoning (CoT)      | Wei 2022 |
| B9  | verification         | Shinn 2023 (Reflexion) |
| B10 | decomposition        | Zhou 2022 (Least-to-most) |

슬롯 임팩트 랭킹은 추론한 `task_type`에 따라 달라짐 — 코드 태스크는
B10(분해)이 먼저, 에세이는 B4(대상 독자)가 먼저, 짧은 한 방짜리는
추론 층을 아예 건너뜀.

---

## 다른 사람 프롬프트에 돌려보기

<!-- benchmark:begin -->

CL4R1T4S에서 가져온 2026-04-17 기준 실점수.
`python3 skills/opus-mind/scripts/benchmark.py --update-readme`로 갱신.

| 출처 | 점수 | Verdict | 주요 미달 |
|---|---|---|---|
| [Claude Opus 4.7](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude-Opus-4.7.txt) | **11/11** | GOOD | — (canonical) |
| [Cursor Prompt](https://github.com/elder-plinius/CL4R1T4S/blob/main/CURSOR/Cursor_Prompt.md) | 6/11 | BORDERLINE | I1, I2, I8, I9, I10 |
| [ChatGPT-5 (Aug 2025)](https://github.com/elder-plinius/CL4R1T4S/blob/main/OPENAI/ChatGPT5-08-07-2025.mkd) | 4/11 | POOR | I1, I2, I3, I5, I6, I9, I11 |
| [Claude Code (2024-03)](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude_Code_03-04-24.md) | 7/11 | BORDERLINE | I2, I3, I8, I10 |

<!-- benchmark:end -->

6/11이라고 제품이 나쁜 건 아님 — 그 프롬프트가 12-primitive 스타일로
쓰이지 않았다는 뜻일 뿐. 짧은 프롬프트는 I9(self-check는 긴 프롬프트
용)와 I10(tier label은 고위험 규칙 용)에서 자연스럽게 점수가 낮게
나옴. 짧거나 위험도가 낮으면 해당 invariant가 요구되지도 않음.

---

## 못 하는 것

- **규칙이 맞는지는 판단 못 함.** 모양과 규율을 볼 뿐, 의미적 정당성은
  못 본다. 11/11 받은 프롬프트도 내용이 틀릴 수 있음 — 다만 drift는
  안 함.
- **보안 리뷰 아님.** jailbreak 탐지기도 아니고 red-team 도구도
  아님. Primitive 09(reframe-as-signal)가 방어적이지, 나머지는 구조
  체크.
- **멀티턴 대화 커버 X.** LINT는 시스템 프롬프트 하나를 본다. 턴 간
  context drift는 스코프 밖.
- **영어 regex 중심.** 한국어·일본어·스페인어 프롬프트는 Python 층이
  덜 잡아냄. Claude Code 안에서는 스킬이 "Claude가 자기 언어 판단으로
  override하라"고 지시함. Claude Code 밖이면 비영어 프롬프트 점수는
  대략적 근사치.
- **`boost expand`가 완성 프롬프트를 반환하진 않음.** 둘러싼 LLM이
  적용할 composition 템플릿을 뱉는다. Claude Code 안에선 Claude가 그
  템플릿 읽고 재작성한 프롬프트를 답장한다. 밖이면 원하는 LLM에
  복붙해서 돌리면 됨.

10줄 미만 + directive 3개 미만이면 `audit.py`가 verdict THIN 찍고
채점 거부함 — 구조적으로 볼 게 없는 파일이라. 버그 아니라 의도된
바닥값.

---

## 테스트

통과 156개, 오프라인일 때 skip 4개.

```
python3 -m pytest tests/ skills/opus-mind/tests/ -q
```

그 중 `test_dogfood.py`는 매 실행마다 Opus 4.7 원전을 live-fetch해서
우리 채점기로 여전히 11/11 나오는지 검증한다. regex가 원전에서
드리프트하면 이 테스트가 가장 먼저 깨짐.

`test_skill_orchestration.py`는 스킬이 의존하는 JSON 스키마 계약을
잠근다 — `audit --json` 구조, 모든 primitive 문서에 TL;DR 섹션 존재,
레포 어디에도 API 콜 없음 (grep 보증).

---

## 아키텍처

Python 스크립트는 결정론적 — regex, 카운트, 문자열 템플릿. LLM 안
부르고 `ANTHROPIC_API_KEY` 안 읽음. Claude Code 세션 안에서는 합성
(리포트 구성, crosscheck 적용, 비영어 프롬프트 처리)이 옆에서 돌고
있는 Claude의 몫. CLI는 Claude Code 없는 환경용 탈출구 — pre-commit
훅, CI, Ruby 프로젝트, 뭐든.

```
skills/opus-mind/
├── SKILL.md                  주 UX: phase-based flow + JSON 스키마
├── hooks.json                Claude Code / Cursor / Codex lifecycle
└── scripts/
    ├── audit.py              LINT — 11 invariants, --json 우선
    ├── plan.py               LINT — 도메인 추론 + 필요 primitive
    ├── fix.py                LINT — slop 재작성 + 스켈레톤 주입
    ├── decode.py             LINT — primitive 라벨링
    ├── seed.py               LINT — task type별 스켈레톤 6종
    ├── boost.py              BOOST — check / ask / expand, 10슬롯
    ├── symptom_search.py     DEBUG — 증상 → primitive 포인터
    ├── benchmark.py          CI — CL4R1T4S에서 live 리더보드
    ├── critic.sh             audit → plan → fix → re-audit 루프
    ├── install-skill.sh      ~/.claude/skills/opus-mind/에 등록
    ├── install-hook.sh       git pre-commit 설치
    └── opus-mind             bash wrapper / CLI 엔트리포인트
```

---

## 귀속

1,408줄 Opus 4.7 시스템 프롬프트는 이 레포에 호스팅하지 않음.
[CL4R1T4S 미러](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude-Opus-4.7.txt)에
있고, [@elder-plinius](https://github.com/elder-plinius)가 관리함.
Anthropic은 이 프롬프트를 공식 발표하지 않았다. 이 레포는 독립 제3자
분석 — 후원, 리뷰, 파트너십 아님.

분석 파일의 인용은 15단어 이내이고 라인 번호에 앵커돼 있어서, 원전
맥락을 직접 확인할 수 있다.

저작권자인데 특정 인용에 대해 공정 이용 판단이 틀렸다고 보면
이슈로 알려줘 — 같은 날 대응. 분석 프레임워크(primitives, 도구,
테스트)는 독립 창작물이라 범위 밖이고, 직접 인용만 범위 안.

MIT. 포크, 확장, 반박 자유.

---

## 기여

환영하는 것:

- **다른 유출 프롬프트와의 대조.** 같은 primitive가 GPT / Gemini /
  Grok 에도 나타나는지? 어디서 갈라지는지?
- **내가 빠뜨린 BOOST 슬롯.** 10개에 없는 일관된 프롬프트 축을
  발견했으면 fixture 2개(filled + empty)와 근거 인용으로 제안.
- **실패 모드 리포트.** "primitive X를 적용했는데 Y 때문에 깨졌다" —
  가장 귀한 피드백.

[CHANGELOG](./CHANGELOG.md) · [방법론](./methodology/README.ko.md) ·
[primitives](./primitives/) · [techniques](./techniques/) ·
[evidence / line-refs](./evidence/line-refs.md)
