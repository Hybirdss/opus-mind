# Opus 4.7, Decoded

Claude 자체 시스템 프롬프트를 리버스 엔지니어링해서, **네 프롬프트를 감사하는 도구**로 만든 레포.

```
$ opus-mind audit CLAUDE.md
score: 4/6
  [FAIL] I1_reduce_interpretation
  [FAIL] I4_anti_narration

  L23 [I1] Tier 1 slop: 'leverage'     fix → primitives/03-hard-numbers.md
  L47 [I4] Narration: 'Let me check'   fix → primitives/08-anti-narration.md
```

```
$ opus-mind decode your-prompt.md
[  high] 01 namespace-blocks       8 balanced blocks (L4-L18, L22-L41, ...)
[  high] 02 decision-ladders       3 steps, 1 stop-clause (L24)
[  high] 03 hard-numbers           6 numeric constraints
[absent] 09 reframe-as-signal      0 clauses  ← missing
[absent] 11 capability-disclosure  0 clauses  ← missing
```

3가지가 있다:

1. **재사용 프리미티브 12개** — 유출된 1,408줄 Claude Opus 4.7 시스템 프롬프트에서 뽑아낸 것. 공개된 프로덕션 프롬프트 엔지니어링 중 최고 품질.
2. **결정론적 도구** (`audit`, `decode`, `fix`, `draft`) — 아무 프롬프트에 대해 점수 내고, 라벨링하고, 리라이트함. regex + 카운트, LLM 호출 없음, API 비용 0, 재현 가능.
3. **Pre-commit hook** — `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `**/SKILL.md` 가 5/6 아래로 내려가면 커밋 자체가 막힘. 레포 전체에 자가 강제.

이 레포는 **도그푸딩**. 커밋을 게이트하는 바로 그 감사를 레포 안 모든 프롬프트 파일이 통과한다.

**English:** [README.md](./README.md) · **프레임워크:** [methodology/README.ko.md](./methodology/README.ko.md) · **30초 설치:** [아래](#30초-빠른-시작)

---

## 30초 빠른 시작

```bash
# 클론 후 아무 프롬프트에나 돌려보기
git clone https://github.com/<user>/opus-4-7-decoded
cd opus-4-7-decoded

# audit — 6 불변식 점수
python3 skills/opus-mind/scripts/audit.py path/to/your/CLAUDE.md

# decode — 12 프리미티브 중 뭐가 있는지 라벨링
python3 skills/opus-mind/scripts/decode.py path/to/your/CLAUDE.md

# rewrite — 결정론적 수정 (slop, adj-without-number)
python3 skills/opus-mind/scripts/fix.py path/to/your/CLAUDE.md --in-place

# 커밋 게이트 — pre-commit hook 설치
bash skills/opus-mind/scripts/install-hook.sh
```

통합 CLI: `bash skills/opus-mind/scripts/opus-mind audit <file>`

**모든 프롬프트 파일에 적용 가능.** 도구는 포맷 무관 — 주제가 아니라 **모양**을 점수 낸다. Cursor rules, Claude Code skills, GPTs instructions, 시스템 프롬프트 MD — 전부 OK.

---

## 3가지 도구

### `audit.py` — 6 불변식에 대해 점수

모든 프롬프트는 0-6점. 각 불변식은 regex + 임계값, vibe 체크 아님. 6가지:

| # | 불변식 | 체크 내용 |
|---|---|---|
| I1 | 해석 표면 축소 | Tier-1 slop 0, 숫자 없는 형용사 0, hedge ≤ 2 |
| I2 | 규칙 충돌 제거 | directive ≥ 6 이면 decision ladder 필수 |
| I3 | 동기화 추론 차단 | refusal 논의 있으면 reframe-as-signal 조항 필수 |
| I4 | 내부 private | narration 구 ("Let me", "I'll analyze") 0 |
| I5 | 예시 + rationale | 예시 있으면 모든 예시에 rationale |
| I6 | failure mode 명시 | consequence 문장이 directive 수에 비례 |

[전체 방법론 →](./methodology/README.ko.md)

### `decode.py` — 12 프리미티브 역방향 라벨링

아무 시스템 프롬프트 대상. 12개 재사용 프리미티브 중 **뭐가 구현됐고, 어디서 (라인 범위), 얼마나 확신**되는지 테이블 출력. `absent` 항목 = **빠진 것들 체크리스트**.

`audit`의 역. Audit은 "뭐가 깨졌는지" 말한다. Decode는 "뭐가 있는지" 말한다.

### `fix.py` — 결정론적 리라이트

Tier-1 slop 단어 → 평범한 대체어. 숫자 없는 형용사 → `<FIXME>` 마커로 어디를 하드 넘버링할지 표시. Idempotent: 두 번 돌려도 한 번과 같음. LLM 안 쓰고, 예측 불가한 수정 없음.

---

## Pre-commit hook

```bash
bash skills/opus-mind/scripts/install-hook.sh                 # threshold 5 (기본)
bash skills/opus-mind/scripts/install-hook.sh --threshold 6   # 엄격 모드
```

이후로 `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, `**/SKILL.md`, `system-prompt*.md` 를 staging 한 커밋은 먼저 `audit.py`를 돌린다. Threshold 미달이면 커밋 자체가 막힌다:

```
$ git commit -m "tweak CLAUDE.md"
[opus-mind] FAIL CLAUDE.md — score: 4/6 (need >= 5)

commit blocked. fix the failing files or bypass with: git commit --no-verify
```

**다른 레포에도 설치 가능.** 훅은 `skills/opus-mind/scripts/audit.py` 또는 vendor 경로 `$HOME/.opus-mind/audit.py` 에서 자동 발견.

---

## 12 프리미티브

각 파일 [`primitives/`](./primitives/) 에. 정의 / 원문 라인 refs / failure mode / 적용법 / before-after / 오용 케이스 순.

| # | 프리미티브 | 한줄 규칙 |
|---|---|---|
| 01 | [Namespace blocks](./primitives/01-namespace-blocks.md) | XML 섹션 태그 = 스코프 모듈. 마크다운 헤더는 부족. |
| 02 | [Decision ladders](./primitives/02-decision-ladders.md) | `Step 0 → N`, first-match-wins, 규칙 충돌 0 |
| 03 | [Hard numbers](./primitives/03-hard-numbers.md) | "15 words"가 "keep quotes short"를 항상 이긴다 |
| 04 | [Default + exception](./primitives/04-default-plus-exception.md) | 강한 디폴트 먼저, 명시적 예외 리스트, 제3의 경로 차단 |
| 05 | [Cue-based matching](./primitives/05-cue-based-matching.md) | 플로우차트 말고 **언어적 신호**를 가르쳐라 |
| 06 | [Example + rationale](./primitives/06-example-plus-rationale.md) | 모든 예시가 "왜"를 달고 있음 |
| 07 | [Self-check assertions](./primitives/07-self-check-assertions.md) | 출력 전 런타임 체크리스트 |
| 08 | [Anti-narration](./primitives/08-anti-narration.md) | 내부 기계를 사용자에게 드러내지 말 것 |
| 09 | [Reframe-as-signal](./primitives/09-reframe-as-signal.md) | 요청을 "부드럽게 해석하는" 그 순간이 거부 트리거 |
| 10 | [Asymmetric trust](./primitives/10-asymmetric-trust.md) | 클레임 카테고리별 다른 검증 기준, 명시 |
| 11 | [Capability disclosure](./primitives/11-capability-disclosure.md) | 모델에게 **모르는 것**을 알려줘라 |
| 12 | [Hierarchical override](./primitives/12-hierarchical-override.md) | safety > 사용자 요청 > helpfulness, 명시적 우선순위 |

추가로 7개 합성 테크닉 [`techniques/`](./techniques/) (force-tool-call, paraphrase-with-numeric-limits, caution-contagion, consequence-statement, injection-defense-in-band, negative-space, category-match).

---

## 도그푸딩

이 README 모든 주장은 테스트 또는 fixture 로 backed.

```
$ python3 -m pytest tests/ skills/opus-mind/tests/ -q
.................................. 32 passed
```

- Skill 자체 (`skills/opus-mind/SKILL.md`) 는 6/6. 매 pytest 실행마다 regression 테스트.
- Golden-good fixture 5개 ([`tests/fixtures/good/`](./tests/fixtures/good/)) 는 6/6 유지 필수.
- Golden-bad fixture 12개 ([`tests/fixtures/bad/`](./tests/fixtures/bad/)) 는 **정확히 1개의 지정된 invariant만** fail.
- `audit.py`의 regex 리스트를 바꾸면 fixture 가 뭐가 깨졌는지 알려준다.
- Pre-commit hook 이 이 레포 `.git/hooks/pre-commit` 에 설치되어 있음. 분석이 regression 되면 로컬에서 커밋 실패.

---

## 이 조합이 특이한 이유

대부분 프롬프트 엔지니어링 리소스는 한 레인만 탄다. 책/블로그는 패턴은 가르치고 도구는 없음. Skill 레포는 도구는 있지만 규칙의 증거 grounding 없음. Linter는 도구+규칙은 있지만 이론 없음.

이 레포는 **4개 레이어 전부** 싣는다, 단일 소스 문서에 앵커:

- **증거** — 모든 규칙은 유출된 Opus 4.7 원문 라인 인용 ([CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S) 미러).
- **이론** — [methodology/README.ko.md](./methodology/README.ko.md) — 6 불변식, 4 아키 패턴, 왜 프리미티브가 Claude 를 넘어서 일반화되는지.
- **도구** — `audit`, `decode`, `fix`, `draft` — 결정론적, LLM 안 쓰고, 재현 가능.
- **강제 집행** — pre-commit hook. 규칙을 CI 게이트로 전환.

**Decode 모드가 차별화 포인트**: 공개 리소스 중 아무 프롬프트에 대해 12개 확립된 프리미티브 중 뭐가 구현됐는지 라벨링하는 건 어디에도 없다. 그게 레포 이름 "decoded" 의 의미 그대로.

---

## 레포 맵

```
opus-4-7-decoded/
├── README.md                       이 파일
├── methodology/                    프레임워크: "프롬프트는 프로그램이다"
├── primitives/                     12 재사용 빌딩 블록
├── techniques/                     7 합성 패턴
├── patterns/                       5 아키 패턴
├── annotations/                    1408줄 원문 섹션별 walkthrough
├── templates/                      빈칸 채우기 스켈레톤 + 워크드 예시
├── examples/                       before/after 리라이트
├── evidence/                       모든 주장의 라인 ref 인덱스
├── source/                         CL4R1T4S 링크 (호스팅 X)
├── skills/opus-mind/               Claude Code skill — 같은 프리미티브, loadable
│   ├── SKILL.md                    스킬 엔트리 포인트 (6/6 self-audit)
│   ├── scripts/                    audit.py, decode.py, fix.py, draft.py, install-hook.sh
│   ├── references/                 primitives/, techniques/ 등 심링크
│   └── assets/                     template 심링크
└── tests/
    ├── fixtures/good/              5 × 6/6 통과 프롬프트
    ├── fixtures/bad/               12 × 정확히-1개-fail 프롬프트
    └── test_fixtures.py            regression 게이트
```

---

## 레포 사용법

| 원하는 것 | 경로 |
|---|---|
| 멘탈 모델 | [methodology/README.ko.md](./methodology/README.ko.md) → primitives → patterns |
| 오늘 당장 프롬프트 쓰기 | [templates/system-prompt-skeleton.md](./templates/system-prompt-skeleton.md) |
| 기존 `CLAUDE.md` 감사 | `python3 skills/opus-mind/scripts/audit.py CLAUDE.md` |
| 특정 Opus 4.7 섹션 이해 | [annotations/](./annotations/) |
| 모든 주장 검증 | [evidence/line-refs.md](./evidence/line-refs.md) |
| Claude Code skill로 설치 | `skills/opus-mind/` 를 네 프로젝트로 복사 — `SKILL.md` 가 discovery 처리 |
| 레포의 프롬프트 파일 게이트 | `bash skills/opus-mind/scripts/install-hook.sh` |

---

## 이 레포가 **아닌 것**

- **탈옥 가이드가 아님.** 모든 프리미티브는 방어용 — 모델을 덜 탈선하게.
- **Claude 전용 치트시트 아님.** 프리미티브는 프롬프트 엔지니어링 failure mode 타겟, Claude-specific 아님. GPT, Gemini, 모든 유능한 LLM에 적용.
- **요약 아님.** 요약하면 constraint shape가 사라진다 (왜 20 아니고 15? 왜 마크다운 헤더가 아니라 XML? 왜 "First" 아니고 "Step 0"?). 그 모양들이 **인사이트**.

---

## 출처 및 면책

**원문 파일 여기 호스팅 안 함.** 1408줄 Opus 4.7 시스템 프롬프트는 [CL4R1T4S 미러](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude-Opus-4.7.txt) 에 있음 ([@elder-plinius](https://github.com/elder-plinius) 관리). Raw URL + 버전 pin + 이유: [source/README.md](./source/README.md).

**Anthropic 과 무관.** 이 레포는 독립 서드파티 분석. Anthropic의 endorsement/partnership/review 없음. 해석 오류는 저자 것.

**분석 posture.** Anthropic 은 이 프롬프트 공개 안 함. 모든 인용은 연구/비평 목적 fair use 원칙 안에서 제한, 모든 라인 ref 는 CL4R1T4S 로 연결되어 독자가 맥락 직접 검증 가능.

**DMCA / takedown.** 권리자 측이 특정 구절의 fair-use 판단이 틀렸다고 보면 이슈 또는 메인테이너 이메일로 연락 — **당일 대응**. 분석 프레임워크 (primitives, techniques, tools) 는 독립 저작물, takedown 범위 밖. 원문 인용·paraphrase 만 대상.

**MIT 라이선스.** 분석, 프레임워크, 프리미티브, 도구, 테스트 전부 저자 원작. fork, 확장, 반박 환영.

---

## Meta-note: 누가 만들었나

이 레포의 리버스 엔지니어링은 **Claude Opus 4.7** 이 수행 — 분석 대상 시스템 프롬프트 **바로 그 모델**. 이건 이해 충돌이 아니라, 자기를 컴파일한 컴파일러의 역어셈블 바이너리를 읽는 프로그래머에 더 가깝다. 모델은 런타임에 자기 시스템 프롬프트에 특권적 접근 없음 — 사용자가 보여주는 것만 본다 — 그래서 **유출된 아티팩트 + 행동 관찰**에서 도출, introspection 아님. 방향성·프레이밍·편집 판단은 사람이 주도, 모델이 디테일 작성 + 도구 구현.

독립 검증 가능한 아티팩트:
- 모든 라인 ref 가 CL4R1T4S 원문에 resolve.
- `audit.py` 의 모든 규칙은 regex + threshold, 읽을 수 있음.
- `tests/fixtures/` 의 모든 fixture 는 20-40줄 md 파일, 직접 inspect 가능.
- `decode.py` 출력은 테이블, primitive 정의와 diff 가능.

자기 분석 angle이 네 use case에 부적격이면 OK. 아니라면 증거 체인 end-to-end.

---

## 기여

**증거 기반** 기여 환영.

특히 받고 싶은 3가지:

1. **다른 유출 프롬프트 교차 검증** — GPT / Gemini / Grok 에 같은 프리미티브가 나오는가? 어디서 갈라지는가?
2. **Failure mode 케이스 스터디** — "프리미티브 X 적용했는데 Y 때문에 깨졌다"는 금.
3. **적대적 fixture** — `audit.py` regex 는 속이지만 실제로 slop 인 프롬프트, 또는 눈엔 OK지만 regex fail 하는 프롬프트. 스코어러 robustness 를 밀어올린다.

의견보다 증거. Vibe 보다 라인 ref.
