# FB_auto_Sequence_stack 동작 구조

- **프로젝트**: `PowerCo_Stack_20260421_R142_KJR_R02`
- **CPU**: `Z-AF051.S01.KE01.PLC`
- **경로**: `Program blocks > 100_StackMachine > 130_Auto > Auto_sub1_stack`
- **블록**: `FB_auto_Sequence_stack` [#1101, **GRAPH** 언어]
- **인스턴스 DB**: `DI_auto_Sequence_stack` [#1101]
- **작성일**: 2026-05-11

---

## 1) 호출 체인 (위 → 아래)

```
OB_ASQ_CALL [#135, LAD, ProgramCycle]   ← 사이클릭 OB (자동운전 호출 OB)
   │
   ├─▶ FB_automaticOperation [#19, LAD]                ← 자동운전 메인
   │      │
   │      ├─▶ FB_auto_Sequence_stack [#1101, GRAPH]   ★ 본 시퀀서 (Sub1 스택)
   │      ├─▶ FB_auto_Sequence_Unwinder        (Sub2)
   │      ├─▶ FB_auto_Sequence_Dsheet_L_Cathode (Sub3)
   │      ├─▶ FB_auto_Sequence_Dsheet_R_Anode  (Sub4)
   │      ├─▶ FB_auto_Sequence_Winder           (Sub5)
   │      ├─▶ FB_auto_Sequence_JR_Shuttle / JR_Unloader / Magazine_L/R / Taping
   │      └─▶ FB_applicativeDiagnosis
   │
   ├─▶ FB_Stack_Sequence_Judgment [#2001, LAD]    ← 스택 시퀀스 "전이 조건" 판단
   ├─▶ FB_Unwinder_Sequence_Judgment / Dsheet_L / Dsheet_R / Winder_Sequence_Judgment
   │
   └─▶ 스텝별 동작 FB (Auto_sub1_stack 폴더)
          FB_Auto_Sub1_Stack_100, 200, 300, 400, 500, 600, 700, 800, 900, 1000
          (각각 InstanceDB DI_Auto_Sub1_Stack_n00)
```

즉, **OB_ASQ_CALL → FB_automaticOperation → FB_auto_Sequence_stack (GRAPH 상태기계)** 가 핵심 흐름이고,
매 사이클마다 **FB_Stack_Sequence_Judgment** 가 전이 조건을 만들어주며,
현재 GRAPH 스텝에 해당하는 **FB_Auto_Sub1_Stack_n00** 가 실제 액추에이터 동작을 수행합니다.

---

## 2) `FB_auto_Sequence_stack` 내부 GRAPH 상태기계

### 스텝 (Step) 12개

| Step # | Name | 역할 |
|---|---|---|
| **1** (Init) | `init` | 초기 상태(전원 ON / 시퀀스 리셋 후 진입점) |
| 11 | `Stack_Initial` | 스택 초기 위치 정렬 |
| 12 | `LC_RUN` | Left Cathode 운전 단계 |
| 13 | `RA_RUN` | Right Anode 운전 단계 |
| 14 | `Stack_2` | 적층 2단계 |
| 15 | `Stack_3` | 적층 3단계 |
| 16 | `Stack_4` | 적층 4단계 |
| 17 | `Stack_5` | 적층 5단계 |
| 18 | `Stack_6` | 적층 6단계 |
| 19 | `Stack_7` | 적층 7단계 |
| 20 | `Stack_8` | 적층 8단계 |
| 49 | `Stack_return` | 종료/복귀(원위치) |

각 Step의 `MaximumStepTime = 10s`, `WarningTime = 7s` — 즉 10초 이상 머무르면 알람.

### 트랜지션 (Transition) 21개

| T# | 이름 | 의미 |
|---|---|---|
| T11 | `in_stack_initial` | init → Stack_Initial 진입 |
| T21 | `out_stack_initial` | Stack_Initial 종료 |
| T12 | `starteGrundstellungsfahrt` | LC_RUN/Stack로 진입 (1단) |
| T22 | `grundstellungsfahrtMM2IndexHinten` | 해당 스텝 종료 → return |
| T13~T20 | `starteGrundstellungsfahrt_1` ~ `_8` | 각 Stack_n 진입 트리거 |
| T23~T30 | `grundstellungsfahrtMM2IndexHinten_1` ~ `_8` | 각 Stack_n 종료(복귀) |
| T99 | `out_stack_return` | Stack_return → init 복귀(사이클 종료) |

> Siemens GRAPH 템플릿 명명(독일어)이라 `starteGrundstellungsfahrt` = "기준위치 주행 시작",
> `MM2IndexHinten` = "MM2 인덱스 후방 도달" 의미입니다.
> 각 트랜지션은 LAD로 작성되어 있어 **FB_Stack_Sequence_Judgment** 가 셋팅한 비트를 조건으로 사용합니다.

---

## 3) 표준 GRAPH 인터페이스 입력 (시퀀스 외부 제어)

`DI_auto_Sequence_stack` 인스턴스 DB의 Input 영역(Retain):

- `OFF_SQ` — 시퀀스 OFF (Turn sequence off)
- `INIT_SQ` — 시퀀스를 Initial 상태로 강제 (Set sequence to initial state)
- (그 외 GRAPH 기본: `ACK_EF`, `REG_EF`, `S_PREV`, `S_NEXT`, `MAN_EN`, `T_PUSH`, …)

운전 모드는 HMI/상위에서 이 비트들을 통해 자동/수동/단동/리셋 등을 제어합니다.

---

## 4) 동작 시나리오 요약

1. **OB_ASQ_CALL** 매 PLC 사이클 실행
2. **FB_automaticOperation** 내부에서 자동조건(`bAutoMC`, `bAutoRun` 등) 충족 시 `FB_auto_Sequence_stack` 호출
3. GRAPH FB가 현재 스텝 비트를 `DB_Stack_DATA`(#810) 같은 공용 DB 또는 인스턴스 DB의 스텝 비트 영역에 셋팅
4. **FB_Stack_Sequence_Judgment** 는 센서/위치/연동 신호를 평가해 트랜지션 조건 비트를 만들고
5. **FB_Auto_Sub1_Stack_n00** 시리즈는 "현재 활성 스텝"의 비트를 보고 실제 모터/실린더/모션 명령 출력
6. 트랜지션 만족 → 다음 스텝 이동 → 마지막 스텝 `Stack_return` 완료 시 `init`으로 복귀하여 다음 적층 사이클 시작

---

## 5) 관련 블록 일람 (Auto_sub1_stack 폴더)

### FB (Function Block)
| 블록명 | 번호 | 언어 | 비고 |
|---|---|---|---|
| **FB_auto_Sequence_stack** | #1101 | GRAPH | 메인 시퀀서 |
| FB_Stack_Sequence_Judgment | #2001 | LAD | 전이 조건 판단 |
| FB_Auto_Sub1_Stack_100 | #2100 | LAD | 스텝 동작 |
| FB_Auto_Sub1_Stack_200 | #2200 | LAD | 스텝 동작 |
| FB_Auto_Sub1_Stack_300 | #2300 | LAD | 스텝 동작 |
| FB_Auto_Sub1_Stack_400 | #2400 | LAD | 스텝 동작 |
| FB_Auto_Sub1_Stack_500 | #2500 | LAD | 스텝 동작 |
| FB_Auto_Sub1_Stack_600 | #2600 | LAD | 스텝 동작 |
| FB_Auto_Sub1_Stack_700 | #2700 | LAD | 스텝 동작 |
| FB_Auto_Sub1_Stack_800 | #2800 | LAD | 스텝 동작 |
| FB_Auto_Sub1_Stack_900 | #2900 | LAD | 스텝 동작 |
| FB_Auto_Sub1_Stack_1000 | #2990 | LAD | 스텝 동작 |

### DB
| 블록명 | 번호 | 종류 | 비고 |
|---|---|---|---|
| DB_Stack_DATA | #810 | GlobalDB | 스택 공용 데이터 |
| DI_auto_Sequence_stack | #1101 | InstanceDB | GRAPH 시퀀서 인스턴스 |
| DI_Stack_Sequence_Judgment | #2001 | InstanceDB | Judgment FB 인스턴스 |
| DI_Auto_Sub1_Stack_100 ~ 1000 | #2100 ~ #2990 | InstanceDB | 각 스텝 FB 인스턴스 |

### Sub_FB (보조)
- `FB_LC_Align unit Table_GET` [#8100, LAD]
- `FB_LC_Align unit Table_PUT` [#8101, LAD]

---

## 6) 참고 - 추출된 XML 파일 위치

- `exports\OB_ASQ_CALL.xml`
- `exports\FB_automaticOperation.xml`
- `exports\FB_auto_Sequence_stack.xml`
- `exports\FB_Stack_Sequence_Judgment.xml`
