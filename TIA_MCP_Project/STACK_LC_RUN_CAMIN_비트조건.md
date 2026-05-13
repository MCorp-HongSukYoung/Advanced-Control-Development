# `STACK_LC_RUN_CAMIN` 비트 Set/Reset 조건과 시퀀서 연결

- **프로젝트**: `PowerCo_Stack_20260421_R142_KJR_R02`
- **CPU**: `Z-AF051.S01.KE01.PLC`
- **상위 문서**: [`LC_RUN_CAM_구조.md`](LC_RUN_CAM_구조.md)
- **분석 대상 블록**:
  - `FB_Stack_Sequence_Judgment` [LAD] — `STACK_LC_RUN_CAMIN` 비트의 유일한 Set/Reset 주체
  - `FB_auto_Sequence_stack` [#1101, GRAPH] — Stack 영역 상위 GRAPH 시퀀서
  - `FB_Auto_Sub1_Stack_200` [#2200, LAD] — LC_RUN sub-step 실행 FB
  - `DB_Global_Cam_Control` [#52, GlobalDB] — 핸드셰이크 DB
  - `DI_Auto_Number` — 시퀀스 카운터 (`Auto_Number_Stack`)
  - `OB_ASQ_CALL` — 두 FB의 호출 OB
- **작성일**: 2026-05-11

---

## 0) 한 줄 결론

> `STACK_LC_RUN_CAMIN` 비트는 `FB_Stack_Sequence_Judgment` 의 **두 개의 "CAMIN" 타이틀 네트워크**에서 Set/Reset 된다.
> `FB_auto_Sequence_stack` 은 이 비트를 **직접 건드리지 않으며**, 두 FB는 `DI_Auto_Number.Auto_Number_Stack` 카운터와 `DB_Global_Cam_Control` 비트로 **간접 연결**된다.

---

## 1) 검증 사실 (TIA Portal 직접 확인)

| 항목 | 결과 |
|---|---|
| `FB_auto_Sequence_stack.xml` 안에서 `STACK_LC_RUN_CAMIN` 참조 | **0건** |
| `FB_auto_Sequence_stack` 의 `LC_RUN_CMD` 참조 | 3건 (GRAPH transition 조건) |
| `FB_Stack_Sequence_Judgment.xml` 안에서 `STACK_LC_RUN_CAMIN` 참조 | **4건** (2개 네트워크 × Set/Reset 1쌍씩) |
| 두 FB 모두 호출되는 OB | `OB_ASQ_CALL` (line 250 = `FB_Stack_Sequence_Judgment` 호출) |

→ GRAPH 시퀀서는 추상 명령(`LC_RUN_CMD`)만 발행하고, 실제 CAMIN 비트 토글은 LAD FB 가 절대값으로 판단해서 한다.

---

## 2) 네트워크 ① CompileUnit `71` — 정상 사이클 진입 (`Auto_Number_Stack` 500번대)

### 2-1. SCoil = **Set `STACK_LC_RUN_CAMIN`** 조건

AND 직렬 체인 (모든 조건이 참이어야 SCoil 발화):

```
AlwaysTRUE
 ├─OR─( DB_G1.MC.Auto_Mode  ∨  AUTO_TEST_START )
 └─AND─ VR03_StackLeadingAxis.ActualPosition == 0.0
       AND VR03_StackLeadingAxis.StatusWord.%X5      (StandStill)
       AND VR04_MandrelLeadnigAxis.ActualPosition > 352.0
       AND Auto_Number_Stack >= 500
       AND Auto_Number_Stack <  599
       AND NOT STACK_LC_RUN_InSync                   (아직 동기 안 됐을 때만)
       AND Cam_STACK_LC_RUN_Contol.Fist.First_Cam_Starting_Position
       AND Cam_STACK_LC_RUN_Contol.Cam_Starting_Position
       └─▶  SCoil  STACK_LC_RUN_CAMIN
```

| 조건 | 의미 |
|---|---|
| `Auto_Mode ∨ AUTO_TEST_START` | 자동 운전 중 (또는 테스트 모드) |
| `VR03.ActualPosition == 0.0` & StandStill | 마스터 가상축이 0°에 정확히 정지 |
| `VR04 > 352.0` | 와인딩(Mandrel) 측 가상축이 한 사이클 거의 끝남 |
| `500 ≤ Auto_Number_Stack < 599` | 시퀀스 카운터가 500번대(=LC_RUN 단계) |
| `NOT STACK_LC_RUN_InSync` | 25축 슬레이브가 아직 동기되지 않았음 |
| `First_Cam_Starting_Position` & `Cam_Starting_Position` | 캠 시작점 보정 비트들 |

### 2-2. RCoil = **Reset `STACK_LC_RUN_CAMIN`** 조건

```
AlwaysTRUE  AND  STACK_LC_RUN_InSync
 └─▶  RCoil  STACK_LC_RUN_CAMIN
```

→ 25축이 모두 InSync 되면 `FB_Camin_STACK_LC_RUN` 이 `STACK_LC_RUN_InSync` 를 Set 하고, 그 응답을 받아서 여기서 자동으로 CAMIN 트리거를 떨군다 (S7-1500 모션은 Execute 한 번이면 결합 유지).

### 2-3. 같은 네트워크의 다른 코일

이 한 네트워크 안에 **4 쌍**의 (SCoil, RCoil) 이 병렬로 들어있다:
- `STACK_LC_STACK_CAMIN` (SCoil 92 / RCoil 120)
- `STACK_RA_STACK_CAMIN` (SCoil 98 / RCoil 122)
- `STACK_LC_RUN_CAMIN`   (SCoil 111 / RCoil 124)   ← 본 분석 대상
- `STACK_RA_RUN_CAMIN`   (SCoil 117 / RCoil 126)

각각 `Auto_Number_Stack` 범위만 다르다 (200대 / 300대 / 500대 / 400대 등).

---

## 3) 네트워크 ② CompileUnit `7A` — 초기/Test 진입 (`Auto_Number_Stack == 0`)

### 3-1. SCoil = **Set `STACK_LC_RUN_CAMIN`** 조건

```
AlwaysTRUE
 ├─OR─( Auto_Mode ∨ AUTO_TEST_START ∨ (AUTO_TEST_INIT AND NOT AlwaysTRUE) )
 │       ※ 세 번째 가지는 NOT AlwaysTRUE 라 사실상 죽은 패스 (코딩 잔재)
 └─AND─ Auto_Number_Stack == 0
       AND VR03.ActualPosition == 0.0
       AND VR03.StatusWord.%X5                  (StandStill)
       AND NOT STACK_LC_RUN_InSync
       AND NOT STACK_RA_RUN_InSync
       AND DB_Stack_DATA.CathodeStacking        ← LC 적층 모드일 때만
       AND NOT STACK_LC_RUN_InSync              (중복 안전 인터록)
       AND Cam_STACK_LC_RUN_Contol.Fist.First_Cam_Starting_Position
       AND Cam_STACK_LC_RUN_Contol.Cam_Starting_Position
       └─▶  SCoil  STACK_LC_RUN_CAMIN
```

### 3-2. RCoil = **Reset `STACK_LC_RUN_CAMIN`** (안전 일괄 리셋)

```
PowerRail
 → Contact_NEG  AUTO_TEST_START   (= NOT AUTO_TEST_START)
 → Contact      AlwaysTRUE
 → 동시에:
     ├─ MOVE  INT#9999 → Auto_Number_Stack
     ├─ RCoil  STACK_LC_RUN_CAMIN
     ├─ RCoil  STACK_RA_RUN_CAMIN
     ├─ RCoil  STACK_LC_STACK_CAMIN
     └─ RCoil  STACK_RA_STACK_CAMIN
```

→ `AUTO_TEST_START` 가 떨어지면 4개 CAMIN 비트를 일괄 리셋하고 시퀀스 카운터를 안전한 더미값(9999)으로 보낸다.

### 3-3. 같은 네트워크의 부수 RCoil

```
PowerRail
 → Contact  I_OP Pushbutton SW Start off
   ─OR─
   Contact  I_OP Pushbutton SW Home position
 → RCoil    AUTO_TEST_START
```

→ "Start off" 버튼 또는 "Home position" 버튼이 눌리면 `AUTO_TEST_START` 자체를 Reset → 위 3-2 의 조건이 충족되어 CAMIN 일괄 리셋이 따라온다.

---

## 4) `FB_auto_Sequence_stack` 과의 실제 연결 구조

```
FB_auto_Sequence_stack (GRAPH #1101)
   │  ASQ_CMD.LC_RUN_CMD = 1   ← GRAPH 가 LC_RUN 스텝 진입 시 켬 (직접 CAMIN 안 건드림)
   ▼
FB_Auto_Sub1_Stack_200 (#2200)  + 기타 LC sub-FB들
   │  LC_RUN_CMD 보고 Auto_Number_Stack 진행
   │   - 200 → 210 → 220 → 230 → 240 …  (sub-step 영역)
   │   - 사이클 중반에 다른 sub-FB 들이 500~599 영역으로 카운터 진행
   ▼
DI_Auto_Number.Auto_Number_Stack  ← 두 FB 가 공유하는 카운터
   ▲
   │  값만 읽어서 비교 (write 안 함)
FB_Stack_Sequence_Judgment        ← OB_ASQ_CALL 에서 별도로 호출
   │  ┌─ 네트워크 ① : 500 ≤ Stack < 599  →  SCoil STACK_LC_RUN_CAMIN
   │  ├─ 네트워크 ② : Stack == 0 & CathodeStacking →  SCoil STACK_LC_RUN_CAMIN
   │  └─ 두 네트워크 모두 InSync 응답으로 자동 RCoil
   ▼
DB_Global_Cam_Control.STACK_LC_RUN_CAMIN  = 1
   ▼
FB_Camin_STACK_LC_RUN (#8003)
   │  25개 MC_CAMIN.Execute = 1
   ▼
SINAMICS 25 축이 VR03 위치에 캠 프로파일로 동기 추종
```

### 4-1. 핵심 포인트

1. **`FB_auto_Sequence_stack` 은 `STACK_LC_RUN_CAMIN` 을 직접 건드리지 않는다.** GRAPH 시퀀서는 추상 명령(`ASQ_CMD.LC_RUN_CMD`)만 발행한다.
2. 실제 CAMIN 비트 토글은 `FB_Stack_Sequence_Judgment` 가 **`Auto_Number_Stack` 값 범위**(500–599 또는 0) 와 **물리 조건**(가상축 위치 0°, StandStill, InSync) 으로 결정한다.
3. 두 FB 의 핸드셰이크는 **`DI_Auto_Number.Auto_Number_Stack`** (GRAPH→Sub→카운터, Judgment 가 read-only 로 관찰) 과 **`DB_Global_Cam_Control` 의 `_InSync` 응답 비트** 로 이뤄진다.
4. `LC_RUN_CAM_구조.md` §2의 sub-step 220 에서 `STACK_LC_RUN_CAMIN` 을 Reset 하는 것은 **`FB_Auto_Sub1_Stack_200` 내부의 명시적 RST** 이고, `FB_Stack_Sequence_Judgment` 는 그와 **별도로** `STACK_LC_RUN_InSync` 응답이 올라오면 자동으로 Reset 한다 (**이중 안전망**).

### 4-2. 두 SCoil 네트워크의 역할 분담

| 네트워크 | 발화 시점 | 용도 |
|---|---|---|
| ① CompileUnit 71 | `Auto_Number_Stack` 500–598, VR04>352°, InSync 미달 | **연속 사이클** 중 LC_RUN 단계 진입 시 CAMIN 명령 |
| ② CompileUnit 7A | `Auto_Number_Stack == 0`, `CathodeStacking`, VR03 0° StandStill | **초기/Test 진입** 시 첫 CAMIN 결합 |

---

## 5) 추출 XML 파일 위치

- `exports\FB_auto_Sequence_stack.xml`
- `exports\FB_Stack_Sequence_Judgment.xml`
  - CompileUnit ID="71" (line 4421–5322) — 네트워크 ①
  - CompileUnit ID="7A" (line 5323–6134) — 네트워크 ②
- `exports\FB_Auto_Sub1_Stack_200.xml`
- `exports\FB_Camin_STACK_LC_RUN.xml`
- `exports\OB_ASQ_CALL.xml`

---

## 6) 한 줄 요약

> **`STACK_LC_RUN_CAMIN` 비트는 GRAPH 시퀀서(`FB_auto_Sequence_stack`)가 아닌 LAD 판정 FB(`FB_Stack_Sequence_Judgment`)가 켠다.**
> 판정 FB 는 두 곳에서 이 비트를 Set 한다:
> ① 연속 사이클 중 `Auto_Number_Stack ∈ [500,599)` & 가상축 0° StandStill & InSync 미달 &  와인딩 거의 완료(`VR04>352°`),
> ② 초기 진입 시 `Auto_Number_Stack == 0` & `CathodeStacking` 모드 & 가상축 0° StandStill.
> 둘 다 `STACK_LC_RUN_InSync` 응답이 올라오면 자동으로 Reset 된다.
