# 방법론: 프롬프트는 행동 프로그램이다

이 레포의 **핵심 문서**. 이거 먼저 읽어. 12개 프리미티브, 패턴, annotations — 전부 이 reframe에서 파생된 것.

**한국어 버전.** English: [README.md](./README.md)

---

## 핵심 주장

Opus 4.7 시스템 프롬프트는 규칙 목록이 아니다. **LLM 런타임 위에서 돌아가는 프로그램**이다. 저자는 Claude의 행동을 "문서화"하는 게 아니라, **명세**하고 있다 — 런타임이 해석하는 언어로.

이 프레임을 받아들이면 세 가지가 일어난다:

1. **모든 프롬프트 결정이 trace 가능한 비용/이익을 가진 디자인 결정이 된다.** 왜 "keep quotes short"가 아니라 "15 words"? 전자는 형용사 — 100B 파라미터 모델은 압박받으면 기꺼이 완화한다. 후자는 컴파일러 상수 — 해석 0, 드리프트 0.

2. **프롬프트의 구조가 의미를 가진다.** XML 태그는 장식이 아니다. 스텝 래더는 스타일이 아니다. load-bearing이다 — 빼면 프로그램이 깨진다.

3. **일반화된다.** 여기서 뽑은 프리미티브는 충분히 유능한 모든 LLM에 적용된다. Claude-specific 아니다. **프롬프트 엔지니어링 specific**.

---

## 6개 불변식 (invariants)

이 레포의 모든 프리미티브는 이 6개 중 하나 이상을 섬긴다. 네 시스템 프롬프트를 쓸 때, 이 중 아무것도 섬기지 않는 문단이 있다면 **버려라**.

### I1. 해석 표면을 줄여라

모델은 네 프롬프트를 해석한다. 모든 형용사, "generally", "when appropriate" — 전부 자유도(degree of freedom)다. 압박 상황에서 (긴 대화, 적대적 사용자, 애매한 요청) 모델은 이 자유도를 써서 의도에서 멀어진다.

**Opus 4.7의 수:** 형용사를 숫자로 대체. "Keep quotes short" → "Quotes of fifteen or more words from any single source is a SEVERE VIOLATION." "Don't over-search" → "1 for single facts; 3–5 for medium tasks; 5–10 for deeper research/comparisons."

*증거:* `source/opus-4.7.txt` lines 640–641 (15단어 하드 리밋), 620 (툴 콜 스케일링), 871–872 (이미지 min 3 max 4).

### I2. 규칙 충돌을 제거하라

규칙 충돌은 시스템 프롬프트의 사일런트 킬러. 공존 가능해 보이는 두 규칙이 어떤 입력에서 모순되고, 모델은 바이브로 한 쪽을 고른다. 너는 그 일이 일어나는지도 못 보고 — 그냥 일관성 없는 행동만 받는다.

**Opus 4.7의 수:** **first-match-wins 결정 래더**. [`request_evaluation_checklist`](../source/opus-4.7.txt) 섹션 (line 515) 이 모델을 Step 0 → Step 3으로 걷게 하고, 첫 매치에서 멈춘다. 규칙 충돌 불가능 — 래더 자체가 해결 순서.

*증거:* lines 515–537. 섹션 전체 읽어라 — "stops at the first match"라는 명시가 키.

### I3. 동기화된 추론을 잡아라

도움이 되려는 모델의 가장 위험한 failure mode: **도와주고 싶으니까** 나쁜 요청을 안전해 보이게 reframe하고, reframe된 버전에 기꺼이 응한다.

**Opus 4.7의 수:** **reframe-as-signal**. Line 33: "If Claude finds itself mentally reframing a request to make it appropriate, that reframing is the signal to REFUSE, not a reason to proceed with the request."

이거 비범하다. 모델에게 **자기 자신의 위생 처리 충동을 compliance의 반증으로 취급**하라고 지시한다. 루프를 invariant로 뒤집었다.

*증거:* line 33.

### I4. 내부를 private로 유지하라

도움 되려는 모델은 자신을 설명하고 싶어 한다. "Let me check the diagram tool first…" "Per my guidelines…" "I'll route this to…" — 투명성 관점에선 전부 helpful, 프로덕트 UX 관점에선 전부 파멸.

**Opus 4.7의 수:** **anti-narration**, 여러 번 명시. Line 536: "Claude does not narrate routing — narration breaks conversational flow. Claude doesn't say 'per my guidelines,' explain the choice, or offer the unchosen tool. Claude selects and produces." Line 560: "Claude never exposes machinery. No 'let me load the diagram module.'"

*증거:* lines 536, 560.

### I5. 규칙이 아니라 예시로 보정하라

규칙은 압축적이지만 부서지기 쉽다. 예시는 장황하지만 엣지케이스를 가르친다. Opus 4.7 프롬프트는 예시로 가득하고, **모든 예시에 `{rationale}...{/rationale}` 블록이 붙어있다** — 왜 그 예시가 맞는지 설명.

이게 "규칙 암기"와 "함수 학습"의 차이. 예시+rationale은 함수를 가르친다. 모델은 저자가 예상 못 한 케이스에도 일반화할 수 있다.

*증거:* lines 710–750 (저작권 예시), 882–902 (이미지 서치 예시), 493–498 (결정 예시).

### I6. Failure mode를 명시하라

모든 safety / quality 규칙은 **막는 harm을 명명한다**. 수사적 장식이 아니라 **보정(calibration)**. 모델이 엣지케이스에 부딪히면, 명시된 harm이 어느 방향으로 기울지를 알려준다.

**Opus 4.7의 수:** "Claude understands that quoting a source more than once or using quotes more than fifteen words: — Harms content creators and publishers — Exposes people to legal risk — Violates Anthropic's policies" (lines 753–759). "왜"가 규칙을 **재표현 공격에서 살려낸다**.

*증거:* lines 753–759, 591 ("copyright violations harm creators").

---

## XML을 선택한 이유

마크다운 헤더로도 됐을 텐데, 왜 XML?

**이유 1: 중첩.** `{critical_child_safety_instructions}` 가 `{refusal_handling}` 안에, 그게 또 `{claude_behavior}` 안에 살 수 있다. 마크다운 헤더는 계층을 heading 레벨로 납작하게 만든다. XML은 트리를 보존한다.

**이유 2: 스코프.** `{/refusal_handling}` 이 섹션을 명시적으로 닫는다. 모델은 모듈이 **어디서 끝나는지** 안다. 마크다운엔 close 태그 없음 — 섹션은 "다음 헤딩이 시작할 때" 또는 "네 기분 내킬 때" 끝난다.

**이유 3: 저자를 위한 machine-readability.** Anthropic은 거의 확실히 이 프롬프트를 프로그래밍으로 편집한다. 태그된 섹션은 diff, 테스트, A/B, 재생성이 freeform prose보다 훨씬 쉽다.

**이유 4: out-of-band signaling.** 프롬프트는 `{cite index="..."}...{/cite}` 같은 태그로 **출력에서의 인용 의도**를 신호한다. 태그는 모델과 consumer 사이 인터페이스의 native 어휘. 지시에도 태그를 쓰면 시스템 전체가 일관된다.

테이크어웨이: 500단어 넘는 프롬프트라면 XML 섹션을 써라. 편집해야 할 때 너 자신에게 감사하게 된다.

---

## 결정 래더 패턴

답할 수 있는 방법이 여러 개일 때, 순진한 프롬프트는 모든 고려사항을 나열하고 모델이 잘 고르길 바란다. Opus 4.7 패턴:

```
Step 0 — 시각화가 필요한가?            [아니면 멈춤.]
Step 1 — 연결된 MCP 툴이 맞나?         [맞으면 그걸 쓰고 멈춤.]
Step 2 — 파일을 달라고 했나?            [맞으면 파일 툴 쓰고 멈춤.]
Step 3 — Visualizer (기본 인라인).
```

(lines 515–537)

3가지 속성:

1. **순서가 있다.** 모델은 위→아래로 걷는다.
2. **멈춘다.** 첫 매치가 walk를 끝낸다.
3. **전수적이다.** 마지막 단계가 default catch-all.

이건 결정 **절차**다, 규칙 **집합**이 아니다. 순서가 우선순위를 인코딩한다. 프롬프트에 자명하지 않은 라우팅 로직을 쓴다면 래더를 써라.

---

## 형용사 아니고 하드 넘버

Opus 4.7 프롬프트의 숫자 상수 덴스 테이블:

| 상수 | 값 | 목적 |
|---|---|---|
| 인용 길이 | < 15단어 | 저작권 상한 |
| 소스당 인용 | 최대 1개 | 저작권 상한 |
| 서치 쿼리 길이 | 1–6단어 | 툴 사용 |
| 툴 콜 (단순) | 1 | 스케일 |
| 툴 콜 (중간) | 3–5 | 스케일 |
| 툴 콜 (심층) | 5–10 | 스케일 |
| 툴 콜 (매우 심층) | 20+ → 위임 | 에스컬레이션 |
| 이미지 서치 결과 | min 3, max 4 | UX |
| Storage 키 길이 | < 200자 | 기술 제약 |
| Storage 값 크기 | < 5MB | 기술 제약 |
| 아티팩트 코드 길이 | > 20줄 → 파일 | 출력 라우팅 |
| 아티팩트 prose 길이 | > 1,500자 → 파일 | 출력 라우팅 |
| recent_chats 한도 | n ≤ 20 | 툴 제약 |
| 페이지네이션 리밋 | ~5 콜 | 툴 제약 |

주목: **모든 형용사는 숫자로 백업되어 있다.** "짧은 인용"은 15단어. "심층 리서치"는 5–10 툴 콜. "긴 컨텐츠"는 1,500자.

네 프롬프트를 쓸 때 형용사를 타이핑하면 멈춰라. **숫자가 뭐냐?**

---

## Failure mode 분류법

모든 프리미티브는 특정 failure 때문에 존재한다. 지도:

| Failure mode | 막는 프리미티브 |
|---|---|
| 압박 하 규칙 충돌 | Decision ladders |
| 형용사 드리프트 | Hard numbers |
| 거부에서의 동기화 추론 | Reframe-as-signal |
| 과잉 친절 자기 해설 | Anti-narration |
| 일반화 없이 규칙만 암기 | Example+rationale |
| 모델이 자기 능력을 부인 | Capability disclosure |
| 정책 충돌 (safety vs helpfulness) | Hierarchical override |
| 사용자 컨텐츠 통한 프롬프트 인젝션 | Asymmetric trust, in-band injection defense |
| 규칙이 재표현에 살아남게 | Consequence statement |
| 대화 중 caution 약화 | Caution contagion |
| 플로우차트의 취약성 | Cue-based matching |
| 스코프 없는 "규칙 사방" 파일 | Namespace blocks |

이 표가 **약한 시스템 프롬프트 디버깅의 최단 경로**. 증상을 찾고 프리미티브를 적용.

---

## Anthropic이 프롬프트 엔지니어링에 대해 명확히 믿는 것

원문을 디자인 철학의 artifact로 읽으면, 이 믿음들이 함의된다:

- **모델은 프로그래밍할 시스템**이지 지시할 박스가 아니다. 모든 줄이 명세.
- **Safety는 아키텍처**다, appended 아니다. 하드 리밋이 그걸 제약하는 가이던스 옆에 산다; 맨 뒤 "safety 섹션"이 아님.
- **모델은 자기 지시에 대해 추론한다.** 그래서 `{rationale}` 블록과 명시된 consequence — compliance만이 아니라 **추론을 보정**하려고 거기 있다.
- **UI의 unstrusted 영역에서 사용자는 기본적으로 적대적.** "Content in user-turn tags that could even claim to be from Anthropic" (line 115) — 프롬프트는 자기 메시지 봉투조차 불신한다.
- **재포맷팅은 행동이지 세팅이 아니다.** 출력 포맷팅이 거부 정책보다 많은 줄을 먹는다. 디폴트는 강하게 설정 (no bullets, no emojis, prose over lists), 예외는 명시.
- **시스템 프롬프트의 일은 variance를 줄이는 것**, 퍼포먼스 최대화가 아니다. 프롬프트는 "Claude does X"와 "Claude does not X"로 가득 — **선언적 불변식**, "do your best" 하나마나한 말 없음.

---

## 이 프레임워크 쓰는 법

시스템 프롬프트를 쓴다면, 매 문단마다 자문:

1. **6개 불변식 중 어느 걸 섬기는가?** 하나도 없으면 삭제.
2. **숫자로 백업 안 된 형용사가 있는가?** 숫자를 넣어라.
3. **해석이 여러 개 가능한가?** 결정 래더로 바꿔라.
4. **규칙에 명시된 consequence가 있는가?** 없으면 추가해라.
5. **섹션이 명시적 open/close로 바운드되어 있는가?** 아니면 XML 태그로 감싸라.
6. **사용자 제공 메시지가 이 지시를 사칭할 수 있는가?** 인젝션 방어를 추가해라.

이게 다다. 이게 방법이다. 레포의 나머지는 워크스루, 예시, 각 조각이 왜 load-bearing인지에 대한 증거.
