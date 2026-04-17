# opus-mind

`CLAUDE.md` 같은 시스템 프롬프트를 채점해주는 linter예요. [CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S)에
유출된 1,408줄짜리 Opus 4.7 시스템 프롬프트에서 규칙을 뽑아왔어요.
Claude Code 스킬로도, CLI로도 쓸 수 있고요. 모든 규칙이 원전의 특정
줄에 앵커돼 있어서 근거가 명확하고, 채점 엔진은 regex랑 카운트만
써요 — LLM은 따로 안 불러요.

```
$ opus-mind lint audit ~/.claude/CLAUDE.md
score: 10/11   verdict: BORDERLINE
  [FAIL] I6  failure_modes_explicit   consequence가 0개예요 (최소 1개 필요)

  L42 'the bot must cite sources' — consequence가 안 붙어있어요
```

같은 스킬 안에 두 번째 도구도 있어요. 프롬프트 엔지니어링의 반대쪽 —
매일 Claude / ChatGPT / Cursor에 보내는 일회성 프롬프트를 다듬는
쪽이에요.

```
$ opus-mind boost check "write a blog post about AI safety"
coverage: 1/10    task_type: write

비어있는 슬롯, 임팩트 순위:
  [ ] B4 context        'write' 태스크는 대상 독자가 가장 중요해요
  [ ] B6 constraints    톤이랑 피할 것들
  [ ] B3 length         300 단어, 불릿 5개, 200 토큰 이하
  ...
```

**English**: [README.md](./README.md)

```
    LINT — 시스템 프롬프트                   BOOST — 유저 프롬프트
    ──────────────────────                   ──────────────────────
    CLAUDE.md / AGENTS.md                   LLM에 보내는 프롬프트
    .cursorrules / SKILL.md                 "블로그 글 써줘..."

    11개 구조 불변식                         10개 슬롯 (스펙 7 + 추론 3)
    에이전트 설계 품질을 감사                요청 명확도를 감사
    커밋을 게이트                            프롬프터를 코칭
```

---

## 왜 만들었나요

제 `CLAUDE.md`가 녹슬어 있더라고요. 처음 쓸 땐 규칙이 쨍했는데, 모델이
추천해준 줄을 계속 붙여넣다 보니 어느 순간 `never X`가 `typically
avoid X`로 바뀌어 있었어요. 리뷰어도 없고, "좋은 프롬프트"의 객관적인
기준도 없는 상황이었고요.

그때 유출된 Opus 4.7 프롬프트를 봤는데, 그게 딱 그 기준이더라고요.
1,408줄, Anthropic이 자기네 대표 모델에 쏟아부은 규칙들이요. 프로덕션
프롬프트에 있으면 좋을 패턴 — 형용사 대신 hard number, 무순위 리스트
대신 decision ladder, jailbreak drift 잡는 reframe-as-signal — 이 다
들어있고 calibrated돼 있었어요. 그래서 패턴을 뽑고, 존재 여부를
탐지하는 regex를 짜서, linter로 묶었습니다.

BOOST는 나중에 추가했어요. 같은 엔진 아이디어를 다른 대상에
적용했어요. 제가 안 쓴 시스템 프롬프트를 채점하는 대신, 제가 **지금**
쓰는 채팅 프롬프트를 코칭하도록요. 모호한 프롬프트를 좋은 프롬프트로
바꿔주는 10개 슬롯을 가리켜주는 역할이에요.

---

## 설치

Claude Code 안에서 쓰시려면 (추천드려요):

```bash
git clone https://github.com/Hybirdss/opus-mind
cd opus-mind
bash skills/opus-mind/scripts/install-skill.sh
```

Claude Code 재시작하시고, 그냥 평소처럼 말 거시면 돼요 — "내 CLAUDE.md
감사해줘", "내 봇이 거절하고 나서 굽힌다", "이 프롬프트 좋게
만들어줘" 같은 식으로요. Claude가 스킬 읽고, 헬퍼 돌리고, 응답을
합쳐서 드려요. API 키는 필요 없어요. 이미 Claude랑 대화하고 계시니까요.

독립 CLI로 쓰시려면 (pre-commit 훅, CI, 스크립트 등):

```bash
opus_mind=skills/opus-mind/scripts/opus-mind

$opus_mind lint audit path/to/CLAUDE.md        # 점수랑 지적사항
$opus_mind lint critic path/to/CLAUDE.md       # audit → fix → re-audit 한 번에
$opus_mind lint seed --type customer-bot       # 9+/11 나오는 스켈레톤

$opus_mind boost check "프롬프트 여기"
$opus_mind boost ask   "프롬프트 여기"         # 한 번에 질문 하나씩
$opus_mind boost expand "프롬프트" --length "300 단어" --format markdown
```

커밋 임계값으로 막고 싶으시면:

```bash
bash skills/opus-mind/scripts/install-hook.sh --threshold 6
```

---

## 뭘 잡아내나요

**LINT — 11개 불변식.** 모든 신호가 Opus 4.7 원전의 특정 줄에 앵커돼
있어요.

| ID | 체크 | 원전 |
|---|---|---|
| I1  | hedge 비율 ≤ 0.25, 숫자 비율 ≥ 0.10 | L664, L620 |
| I2  | 라우팅 분기에 `Step N → ...` ladder | L515–L537 |
| I3  | refusal 내용이 있으면 reframe-as-signal 조항 필수 | L33 |
| I4  | narration 서두 ("Let me check" 같은 것) 0개 | L536, L560 |
| I5  | 예시마다 rationale 부착 | L710–L750 |
| I6  | directive 수에 비례하는 consequence 문장 | L753–L759 |
| I7  | `{foo}…{/foo}` 블록이 전부 닫힘 | 구조적 |
| I8  | default랑 exception이 같이 등장 | L25, L57–68 |
| I9  | 긴 프롬프트엔 self-check 블록 | L698–L707 |
| I10 | 고위험 규칙엔 ALLCAPS tier label | L640, L657 |
| I11 | Tier 체인 또는 hierarchical override | L657 |

통과/실패 외에 두 가지가 더 붙어요. `verdict` enum (THIN / POOR /
BORDERLINE / GOOD)이랑 placeholder 카운트요 — `<FIXME>`, `[TODO]`,
`TBD`, `???`, `XXX` 같은 잔재가 남아있으면 11개 구조 체크가 다
통과해도 GOOD을 못 받아요.

**BOOST — 10개 슬롯.** 스펙 층 (B1–B7)은 Anthropic 공식 prompt
engineering 문서에, 추론 층 (B8–B10)은
`evidence/smart-prompting-refs.md`에 앵커돼 있어요.

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

슬롯 임팩트 랭킹은 추론된 `task_type`에 따라 달라져요. 코드 태스크는
B10(분해)을 먼저, 에세이는 B4(대상 독자)를 먼저, 짧은 한 방짜리는
추론 층을 아예 건너뛰고요.

---

## 다른 분들 프롬프트에 돌려봤어요

<!-- benchmark:begin -->

CL4R1T4S에서 가져온 2026-04-17 기준 실점수예요.
`python3 skills/opus-mind/scripts/benchmark.py --update-readme`로 새로
갱신할 수 있어요.

| 출처 | 점수 | Verdict | 주요 미달 |
|---|---|---|---|
| [Claude Opus 4.7](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude-Opus-4.7.txt) | **11/11** | GOOD | — (canonical) |
| [Cursor Prompt](https://github.com/elder-plinius/CL4R1T4S/blob/main/CURSOR/Cursor_Prompt.md) | 6/11 | BORDERLINE | I1, I2, I8, I9, I10 |
| [ChatGPT-5 (Aug 2025)](https://github.com/elder-plinius/CL4R1T4S/blob/main/OPENAI/ChatGPT5-08-07-2025.mkd) | 4/11 | POOR | I1, I2, I3, I5, I6, I9, I11 |
| [Claude Code (2024-03)](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude_Code_03-04-24.md) | 7/11 | BORDERLINE | I2, I3, I8, I10 |

<!-- benchmark:end -->

6/11이라고 해서 제품이 나쁜 건 전혀 아니에요. 그 프롬프트가
12-primitive 스타일로 쓰이지 않았다는 뜻일 뿐이에요. 짧은 프롬프트는
I9 (self-check는 긴 프롬프트용이에요)이랑 I10 (tier label은 고위험
규칙용이에요)에서 자연스럽게 점수가 낮게 나와요. 프롬프트가 짧거나
위험도가 낮으면 이 invariant들이 애초에 요구되지도 않거든요.

---

## 못 하는 것도 있어요

- **규칙이 맞는지는 판단 못 해요.** 모양이랑 규율을 볼 뿐, 의미적
  정당성은 못 봐요. 11/11 받은 프롬프트도 내용은 틀릴 수 있어요 —
  다만 drift는 안 하고요.
- **보안 리뷰 도구는 아니에요.** jailbreak 탐지기도 아니고 red-team
  도구도 아니에요. Primitive 09(reframe-as-signal)는 방어적이긴 한데,
  나머지는 구조 체크예요.
- **멀티턴 대화는 커버 못 해요.** LINT는 시스템 프롬프트 하나만 봐요.
  턴 간 context drift는 스코프 밖이에요.
- **영어 regex 중심이에요.** 한국어·일본어·스페인어 프롬프트는 Python
  층이 덜 잡아내요. Claude Code 안에서는 스킬이 "Claude가 자기 언어
  판단으로 override해라"라고 지시해둬서 보완이 되지만, Claude Code
  밖이면 비영어 프롬프트 점수는 대략적인 근사치라고 보시면 돼요.
- **`boost expand`가 완성된 프롬프트를 돌려주진 않아요.** 둘러싼
  LLM이 적용할 composition 템플릿을 뱉어드려요. Claude Code 안에선
  Claude가 그 템플릿을 읽고 재작성한 프롬프트를 답장해드리고요.
  밖이시면 원하는 LLM에 복붙해서 돌리시면 돼요.

10줄도 안 되고 directive가 3개도 안 되는 파일이면 `audit.py`가
verdict THIN으로 찍고 채점을 거부해요. 구조적으로 볼 게 없는
파일이라서요. 버그가 아니라 의도된 바닥값이에요.

---

## 테스트

156개 통과하고 있어요. 오프라인일 땐 4개가 skip돼요 (네트워크가
필요한 테스트들이라서요).

```
python3 -m pytest tests/ skills/opus-mind/tests/ -q
```

그 중에 `test_dogfood.py`가 좀 특별한데요, 매 실행마다 Opus 4.7 원전을
live-fetch해서 저희 채점기로 여전히 11/11이 나오는지 검증해요. 만약
regex가 원전에서 드리프트하면 이 테스트가 가장 먼저 깨져요. 저희가
잘못 잡고 있으면 CI가 먼저 알려주는 구조예요.

`test_skill_orchestration.py`는 스킬이 의존하는 JSON 스키마 계약을
잠가놓은 거예요 — `audit --json` 구조가 안 깨지는지, 모든 primitive
문서에 TL;DR 섹션이 있는지, 레포 어디에도 몰래 API 콜이 들어가있지
않은지 (grep으로 보증).

---

## 아키텍처

Python 스크립트는 전부 결정론적이에요 — regex, 카운트, 문자열
템플릿만 써요. LLM 호출 안 하고 `ANTHROPIC_API_KEY`도 안 읽어요.
Claude Code 세션 안에서는 합성 작업 (리포트 구성, crosscheck 적용,
비영어 프롬프트 처리 같은 것)이 옆에서 돌고 있는 Claude의 몫이에요.
CLI는 Claude Code가 없는 환경용 탈출구예요 — pre-commit 훅, CI, Ruby
프로젝트 뭐든 상관없이요.

```
skills/opus-mind/
├── SKILL.md                  주 UX: phase-based flow + JSON 스키마
├── hooks.json                Claude Code / Cursor / Codex lifecycle 훅
└── scripts/
    ├── audit.py              LINT — 11 invariants, --json 우선
    ├── plan.py               LINT — 도메인 추론 + 필요 primitive 계산
    ├── fix.py                LINT — slop 재작성 + 스켈레톤 주입
    ├── decode.py             LINT — primitive 라벨링
    ├── seed.py               LINT — task type별 스켈레톤 6종
    ├── boost.py              BOOST — check / ask / expand, 10 슬롯
    ├── symptom_search.py     DEBUG — 증상 → primitive 포인터
    ├── benchmark.py          CI — CL4R1T4S에서 live 리더보드
    ├── critic.sh             audit → plan → fix → re-audit 루프
    ├── install-skill.sh      ~/.claude/skills/opus-mind/에 등록
    ├── install-hook.sh       git pre-commit 설치
    └── opus-mind             bash wrapper / CLI 엔트리포인트
```

---

## 출처

1,408줄 Opus 4.7 시스템 프롬프트는 이 레포에 호스팅하지 않아요.
[CL4R1T4S 미러](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude-Opus-4.7.txt)에
있고, [@elder-plinius](https://github.com/elder-plinius) 님이 관리하고
계세요. Anthropic은 이 프롬프트를 공식적으로 발표하지 않았어요. 이
레포는 독립 제3자 분석입니다 — 후원, 리뷰, 파트너십 같은 거 아니에요.

분석 파일의 인용은 전부 15단어 이내고 라인 번호에 앵커돼 있어서,
원전 맥락을 직접 확인해보실 수 있어요.

혹시 저작권자이신데 특정 인용에 대한 공정 이용 판단이 틀렸다고
보시면 이슈로 알려주세요. 같은 날 대응드릴게요. 분석
프레임워크(primitives, 도구, 테스트)는 독립 창작물이라 범위 밖이고,
직접 인용만 범위 안이에요.

MIT 라이선스예요. 포크하시고, 확장하시고, 반박도 환영입니다.

---

## 기여

환영하는 것들이에요:

- **다른 유출 프롬프트와의 대조.** 같은 primitive가 GPT / Gemini /
  Grok 에도 나타나는지 궁금해요. 어디서 갈라지는지도요.
- **제가 빠뜨린 BOOST 슬롯.** 10개에 없는 일관된 프롬프트 축을
  발견하셨으면 fixture 2개(filled + empty)랑 근거 인용으로 제안해
  주세요.
- **실패 모드 리포트.** "primitive X를 적용했는데 Y 때문에 깨졌어요"
  같은 거 — 가장 귀한 피드백이에요.

[CHANGELOG](./CHANGELOG.md) · [방법론](./methodology/README.ko.md) ·
[primitives](./primitives/) · [techniques](./techniques/) ·
[evidence / line-refs](./evidence/line-refs.md)
