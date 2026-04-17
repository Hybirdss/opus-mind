# Opus 4.7, Decoded

시스템 프롬프트는 규칙 목록이 아니다. **LLM 런타임 위에서 돌아가는 프로그램**이다.

Opus 4.7 시스템 프롬프트 (1,408줄, [elder-plinius/CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S)에 유출됨) 은 공개된 것 중 가장 잘 짜인 프로덕션 프롬프트 엔지니어링이다. 이 레포는 그걸 리버스 엔지니어링한다 — Anthropic의 규칙을 감탄하러 온 게 아니라, 그 프로그램이 작동하게 하는 **재사용 가능한 프리미티브**를 뽑아내서 네 시스템 프롬프트에 컴파일해 넣기 위해서.

**English:** [README.md](./README.md)

---

## 관점 전환

원문을 문서가 아니라 **소스 코드**로 읽어봐:

| 보이는 것 | 실제로 하는 일 |
|---|---|
| `{refusal_handling}...{/refusal_handling}` XML 태그 | 네임스페이스 / 모듈 |
| "Step 0 → Step 1 → Step 2" 결정 블록 | `if/else` 제어 흐름, first-match-wins |
| "15 words", "1 quote per source", "n ≤ 20" | 컴파일러 상수 — 해석의 여지 0 |
| `{rationale}...{/rationale}` 달린 예시 | 기대 출력이 있는 유닛 테스트 |
| "Before including ANY text, Claude asks internally..." | 런타임 assertion |
| "Claude does not narrate routing" | private / internal 접근제어자 |
| "User turn 안의 태그가 Anthropic에서 온 것처럼 주장" | 프롬프트 인젝션에 대한 입력 검증 |
| "If Claude finds itself mentally reframing…" | 동기화된 추론(motivated reasoning) 트랩 |

프롬프트의 모든 패턴은 특정 failure mode를 막는다. 리버스 엔지니어링 작업은 **그 failure가 뭔지 식별하고 프리미티브 이름을 붙이는 것**.

---

## 이 레포에 뭐가 있나

```
opus-4-7-decoded/
├── source/            1,408줄 원문 (CL4R1T4S 미러)
├── methodology/       프레임워크: "프롬프트는 행동 프로그램이다"
├── primitives/        12개 재사용 빌딩 블록 (각 1파일)
├── techniques/        프리미티브 조합으로 만든 상위 패턴
├── patterns/          아키텍처 패턴 (XML 네임스페이스, 스텝 래더, …)
├── annotations/       1408줄 섹션별 해설, 라인 ref 포함
├── templates/         재사용 가능한 시스템 프롬프트 스켈레톤
├── examples/          프리미티브 적용 전/후 비교
└── evidence/          라인 레퍼런스 인덱스 — 모든 주장이 원문 라인 인용
```

---

## 12 프리미티브 (속성 투어)

각 프리미티브는 `primitives/` 폴더에 독립 파일로 있음. 정의 / 원문 라인 refs / 막는 failure mode / 적용법 / 전후 예시 / 오용 케이스 순서.

1. **[Namespace blocks](./primitives/01-namespace-blocks.md)** — XML 섹션 태그 = 스코프 모듈
2. **[Decision ladders](./primitives/02-decision-ladders.md)** — `Step 0 → Step N`, first match wins, 규칙 충돌 0
3. **[Hard numbers](./primitives/03-hard-numbers.md)** — "15 words"가 "keep quotes short"를 항상 이긴다
4. **[Default + exception](./primitives/04-default-plus-exception.md)** — 강한 디폴트 + 명시적 예외 목록
5. **[Cue-based matching](./primitives/05-cue-based-matching.md)** — 플로우차트 외우지 말고 **언어적 신호**를 인식하게 가르쳐라
6. **[Example + rationale](./primitives/06-example-plus-rationale.md)** — 예시마다 "왜"가 붙어있음
7. **[Self-check assertions](./primitives/07-self-check-assertions.md)** — 출력 전 런타임 체크리스트
8. **[Anti-narration](./primitives/08-anti-narration.md)** — 내부 기계를 사용자에게 드러내지 말 것을 명시
9. **[Reframe-as-signal](./primitives/09-reframe-as-signal.md)** — 요청을 "부드럽게 해석하는" 그 순간이 거부 트리거
10. **[Asymmetric trust](./primitives/10-asymmetric-trust.md)** — 카테고리별로 다른 검증 기준, 명시적
11. **[Capability disclosure](./primitives/11-capability-disclosure.md)** — "visible tool list is partial by design" — 모델에게 **모르는 것**을 알려줘라
12. **[Hierarchical override](./primitives/12-hierarchical-override.md)** — safety > 사용자 요청 > 도움. 명시적 우선순위

---

## 레포 쓰는 법

### 멘탈 모델이 궁금하다면
순서: [methodology/README.md](./methodology/README.md) → 12개 프리미티브 파일 → [patterns/](./patterns/).

### 오늘 당장 시스템 프롬프트를 쓰고 싶다면
[templates/system-prompt-skeleton.md](./templates/system-prompt-skeleton.md) 에서 시작. 네임스페이스 블록, 스텝 래더, 하드 넘버, self-check, anti-narration — 가장 일을 많이 하는 5개 프리미티브가 이미 박혀있는 빈칸 채우기 스켈레톤.

### Opus 4.7이 왜 이렇게 행동하는지 이해하고 싶다면
[annotations/](./annotations/) 에서 1408줄을 섹션별로 걷는다.

### Anthropic 프롬프트 엔지니어링을 리서치/글쓰기에 쓴다면
[evidence/line-refs.md](./evidence/line-refs.md) — 이 레포의 모든 주장이 `source/opus-4.7.txt`의 라인 번호에 매핑됨. **출처 없는 주장 0**.

---

## 이 레포가 **아닌 것**

- 탈옥 가이드가 아님. 여기 모든 프리미티브는 **방어** 패턴 — 모델을 더 안정적이고 덜 탈선하게 만든다. 우회 기법을 찾는다면 정반대를 보고 있는 것.
- "Claude는 이렇게 행동한다" 치트시트가 아님. 그런 건 이미 있음. 이건 **프롬프트 엔지니어링 기법**이고 충분히 유능한 아무 LLM에나 일반화된다.
- 요약이 아님. 요약하면 인사이트가 사라진다 — 인사이트는 **특정 제약의 모양**에 있다 (왜 20이 아니라 15? 왜 마크다운 헤더가 아니라 XML? 왜 "First"가 아니라 "Step 0"?). 그 질문들에 여기서 답한다.

---

## 출처 및 저작권

원문: `source/opus-4.7.txt` — [@elder-plinius](https://github.com/elder-plinius) 가 관리하는 [CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude-Opus-4.7.txt) 아카이브 원문 미러.

Anthropic은 이 프롬프트를 공개한 적 없다. 원문은 유출된 엔지니어링 아티팩트로, 이 레포는 서드파티 분석으로 취급할 것. 모든 인용은 짧게 유지 (paraphrase-first — Opus 4.7 정책 그 자체를 따름).

레포의 분석, 프레임워크, 프리미티브는 저자 작업. MIT 라이선스로 공개 — fork, 확장, 반박 모두 환영.

---

## 기여

잘못된 프리미티브, 틀린 라인 ref, 빠진 기법을 발견하면 이슈나 PR 환영. **의견보다 증거 (라인 refs) 우선**.

특히 도움 받고 싶은 3가지:
1. **다른 유출 프롬프트 (GPT, Gemini, Grok) 에서 같은 프리미티브 확인** — 어디서 똑같이 나오고, 어디서 갈라지는가.
2. **Failure mode 케이스 스터디** — "프리미티브 X 썼는데 Y 때문에 깨졌다"는 금이다.
3. 한국어 외 **번역**.
