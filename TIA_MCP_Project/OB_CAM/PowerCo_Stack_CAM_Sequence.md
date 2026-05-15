# PowerCo_Stack — CAM Step Sequence 상세 조건 및 CAM 전환 조건

> 생성: 2026-05-14  
> 소스: exports/PowerCo_Stack/_root/ 다이제스트 + Auto_Sub FB 코드 분석  

---

## 1. 전체 아키텍처 — "Auto_Number + 불리언 플래그"

```
FB_automaticOperation
  ├─ FB_auto_Sequence_stack (GRAPH)
  │    ├─ ASQ_CMD.LC_RUN_CMD    → FB_Auto_Sub1_Stack_200
  │    ├─ ASQ_CMD.RA_RUN_CMD    → FB_Auto_Sub1_Stack_300
  │    ├─ ASQ_CMD.LC_Single_CMD → FB_Auto_Sub1_Stack_600
  │    ├─ ASQ_CMD.RA_Single_CMD → FB_Auto_Sub1_Stack_700
  │    └─ ...
  ├─ FB_auto_Sequence_Dsheet_L_Cathode (GRAPH)
  │    └─ FB_Auto_Sub3_Dsheet_L_Cathode_100 / 200 / 300
  └─ FB_auto_Sequence_Dsheet_R_Anode (GRAPH)
       └─ FB_Auto_Sub4_Dsheet_R_Anode_100 / 200 / 300
```

### 핵심 인터페이스

| 방향 | 신호 | 설명 |
|------|------|------|
| GRAPH → Sub_FB | `DB_Stack_DATA.ASQ_CMD.*_CMD` (Bool) | 스텝 진입 허가 |
| Sub_FB → GRAPH | `DB_Stack_DATA.ASQ_END.*_END` (Bool) | 스텝 완료 트리거 |
| 내부 진행 | `DI_Auto_Number.Auto_Number_Stack` (Int) | 마이크로 스텝 카운터 |
| CAM 제어 | `DB_Global_Cam_Control.*_CAMIN / CAMOUT` (Bool) | MC_CAMIN/CAMOUT Execute 핀 |

---

## 2. CAM 자동 시작 전제조건

`FB_automaticOperation` Network 1 — **자동 운전 시작 버튼**을 눌렀을 때 아래 조건이 모두 참이어야 `AUTO_TEST_START`가 세트됩니다.

```
[I_OP Pushbutton SW Start on]
AND Cam_Dsheet_R_Anode_Contol.Fist.First_Cam_Starting_Position   ← VR02 전체 축 동기화 완료
AND Cam_Dsheet_L_Cathode_Contol.Fist.First_Cam_Starting_Position ← VR01 전체 축 동기화 완료
AND (
    Cam_STACK_LC_STACK_Contol.Fist.First_Cam_Starting_Position   ← LC_STACK 맨드릴 9축 동기화
    OR
    Cam_STACK_RA_STACK_Contol.Fist.First_Cam_Starting_Position   ← RA_STACK 맨드릴 9축 동기화
)
```

> **의미:** VR01 (Cathode Dsheet), VR02 (Anode Dsheet), VR04 (Mandrel) 세 VR 그룹이 모두 첫 번째 동기화 위치에 도달해야 자동 운전 가능.

---

## 3. Stack 시퀀스 — VR03 (PP 축) CAM 전환 상세

VR03은 13개 PP(Pick & Place) 축을 구동하는 리딩 축입니다.  
LC_RUN과 RA_RUN이 교번으로 VR03 캠을 점유합니다.

### 3-1. LC_RUN 스텝 (FB_Auto_Sub1_Stack_200)

GRAPH `LC_RUN` 스텝 활성 → `LC_RUN_CMD = TRUE` → Sub_200 동작

| Auto_Number | 조건 / 동작 | 의미 |
|-------------|------------|------|
| 200 → 210 | `LC_RUN_CMD = TRUE` 진입 확인 | 스텝 진입 |
| 210 → 220 | `VR03.ActualPosition == 0.0` AND `VR03.StatusWord` | VR03 원점 대기 |
| **220** | **`RESET DB_Global_Cam_Control.STACK_LC_RUN_CAMIN`** | **LC_RUN CAM 해제 (CAMOUT 발동)** |
| 230 (유지) | `VR.RUN` — VR03 이동 시작 | |
| 230 (병행) | `VR03 ≥ 80.0mm` → RA 1st/2nd Surface Vision Trg | RA 비전 타이밍 |
| 230 (병행) | `VR03 ≥ 170.0mm` → LC 1st/2nd Surface Vision Trg | LC 비전 타이밍 |
| 230 (병행) | `120.0mm ≤ VR03 ≤ 180.0mm` → Align Vision Trg[18] | 정렬 비전 타이밍 |
| 230 (병행) | `VR03 ≥ 200.0mm` → LC Align Table VAC on | 진공 흡착 타이밍 |
| **230 → 240** | **`MC_MOVERELATIVE.Done`** AND **`Cam_STACK_RA_RUN_Contol.Fist.First_Cam_Starting_Position`** | **VR03 이동 완료 + RA_RUN 전 축 Synchronizing_POS 도달** |
| 240 → 299 | Axis Position Bit SET (다음 스텝 서보 위치 준비) | |
| **299** | **`ASQ_END.LC_RUN_END = TRUE`** | **GRAPH → RA_RUN 스텝 전환** |

---

### 3-2. RA_RUN 스텝 (FB_Auto_Sub1_Stack_300)

GRAPH `RA_RUN` 스텝 활성 → `RA_RUN_CMD = TRUE` → Sub_300 동작

| Auto_Number | 조건 / 동작 | 의미 |
|-------------|------------|------|
| 300 → 310 | `RA_RUN_CMD = TRUE` 진입 확인 | 스텝 진입 |
| 310 → 320 | `VR03.ActualPosition == 0.0` AND `VR03.StatusWord` | VR03 원점 대기 |
| **320** | **`RESET DB_Global_Cam_Control.STACK_RA_RUN_CAMIN`** | **RA_RUN CAM 해제** |
| 330 (유지) | `VR.RUN` — VR03 이동 시작 | |
| 330 (병행) | `VR03 ≥ 80.0mm` → LC 1st/2nd Surface Vision Trg | LC 비전 (LC/RA 역전) |
| 330 (병행) | `VR03 ≥ 120.0~180.0mm` → Align Vision Trg[16] | 정렬 비전 |
| 330 (병행) | `VR03 ≥ 170.0mm` → RA 1st/2nd Surface Vision Trg | RA 비전 |
| **330 → 340** | **`MC_MOVERELATIVE.Done`** AND **`Cam_STACK_LC_RUN_Contol.Fist.First_Cam_Starting_Position`** | **VR03 이동 완료 + LC_RUN 전 축 Synchronizing_POS 도달** |
| 340 → 399 | Axis Position Bit SET | |
| **399** | **`ASQ_END.RA_RUN_END = TRUE`** | **GRAPH → 다음 스텝 전환** |

---

### 3-3. LC_Single / RA_Single 스텝 (Sub_600 / Sub_700)

전극 낱장 픽앤플레이스 (P&P 헤드 독립 서보 제어, VR03 CAM 미사용).

| 스텝 | CMD 신호 | 주요 동작 |
|------|---------|---------|
| Sub_600 | `LC_Single_CMD` | LC P&P Head Z/X, Align Table, Reverse PP: 독립 위치 명령 |
| Sub_700 | `RA_Single_CMD` | RA P&P Head Z/X, Align Table, Reverse PP: 독립 위치 명령 |

**전극 버퍼 관리:** `DB_Info.Electrode_Cathode[0..4]` / `DB_Info.Electrode_Anode[0..4]` 배열로 전극 존재 여부 추적.  
`FDB_Zone01.Pause_State`가 활성화돼야 전극 이송 스텝 진입 가능.

---

## 4. Dsheet 시퀀스 — VR01/VR02 CAM 조건

### 4-1. Dsheet_L_Cathode (Sub3_100) — VR01 기반

| Auto_Number | 조건 / 동작 | 의미 |
|-------------|------------|------|
| **110 분기** | `Cam_Dsheet_L_Cathode_Contol.Cam_Starting_Position = TRUE` → 120 | **정상 경로: VR01 동기화 확인** |
| 110 분기 | `AlwaysTRUE` → 140 | 백업 경로 (MGZ JOG) |
| 125 | `Axis_8` (Cathode Double Sheet X) → Position[3] | X축 이동 |
| 126 | `Axis_9` (Cathode Double Sheet Z) → Position[1] | Z축 리트랙트 |
| 127 | `Axis_10` (Cathode Double Sheet R) → Position[3] | R축 이동 |
| 128 | `Axis_9` (Cathode Double Sheet Z) → Position[3] | Z축 전진 |
| **129 → 100** | 루프백 | **다음 더블 시트 사이클 반복** |

---

### 4-2. Dsheet_R_Anode (Sub4_100) — VR02 기반

Dsheet_L_Cathode와 동일 구조. 제어 축만 다름.

| 스텝 | 축 | 설명 |
|------|---|------|
| 125 | `Axis_23` (Anode Double Sheet X) | X축 이동 |
| 126 | `Axis_24` (Anode Double Sheet Z) → Position[1] | Z 리트랙트 |
| 127 | `Axis_25` (Anode Double Sheet R) | R축 이동 |
| 128 | `Axis_24` (Anode Double Sheet Z) → Position[3] | Z 전진 |
| 129 → 100 | 루프백 | |

> **차이점:** Sub4_100 step 110은 CAM_Starting_Position 게이트 없이 항상 step 120으로 진행 (Sub3_100과 달리).

---

## 5. InSync 게이트 — 스텝 진입/전환 허가 조건 전체 목록

| CAM 그룹 | VR | 게이트 신호 | 사용 위치 | 포함 축 |
|---------|---|-----------|---------|--------|
| STACK_LC_RUN | VR03 | `Cam_STACK_LC_RUN_Contol.Fist.First_Cam_Starting_Position` | Sub_300(RA_RUN) 종료 조건 | PP 13축 전체 Synchronizing_POS |
| STACK_RA_RUN | VR03 | `Cam_STACK_RA_RUN_Contol.Fist.First_Cam_Starting_Position` | Sub_200(LC_RUN) 종료 조건 | PP 13축 전체 Synchronizing_POS |
| STACK_LC_STACK | VR04 | `STACK_LC_STACK_InSync` | 자동 기동 전제 조건 | LC 맨드릴 4축(GET) + RA 4축(PUT) CamIn.InSync AND |
| STACK_RA_STACK | VR04 | `STACK_RA_STACK_InSync` | 자동 기동 전제 조건 | GET/PUT 역전, 동일 구조 |
| Dsheet_L_Cathode | VR01 | `Dsheet_L_Cathode_InSync` | Dsheet 시퀀스 내부 | Axis10/08/09 CamIn.InSync AND |
| Dsheet_R_Anode | VR02 | `Dsheet_R_Anode_InSync` | Dsheet 시퀀스 내부 | Axis25/23/24 CamIn.InSync AND |

### InSync 신호 구별

| 신호 | 판정 기준 | 특징 |
|------|---------|------|
| `First_Cam_Starting_Position` | 전체 축 `StatusWord.Synchronizing_POS` AND | 처음 프로파일 시작점에 도달한 상태 |
| `Cam_Starting_Position` | Dsheet Sub3_100 분기 게이트 | `First_Cam_Starting_Position`의 상위 개념 |
| `CamIn.InSync` | MC_CAMIN FB 출력 Bool | 완전 동기화 완료 신호 |

---

## 6. 크로스 핸드오프 패턴 (교번 점유)

```
[LC_RUN 스텝 진행 중]
  → Sub_200 step 230 → 240 전환 조건:
    VR03 이동 완료 AND RA_RUN.First_Cam_Starting_Position ← RA가 이미 동기화 완료 대기

[RA_RUN 스텝 진행 중]
  → Sub_300 step 330 → 340 전환 조건:
    VR03 이동 완료 AND LC_RUN.First_Cam_Starting_Position ← LC가 이미 동기화 완료 대기
```

**패턴 요약:** 현재 활성 스텝이 VR03 이동을 마치기 전에, 반대편 CAM이 동기화를 선행 완료해 대기합니다. 이 "선행 동기화 완료 확인"이 스텝 전환의 핵심 게이트 조건입니다.

---

## 7. Dsheet 크로스 핸드오프 (VR01 ↔ VR02)

코드에서 확인된 사실:

- `FB_Camin_Dsheet_L_Cathode`: **CAMOUT 대상이 Axis25/23/24 (VR02의 Anode 축)**
  - `Dsheet_L_Cathode_CAMOUT` → Axis25(AnodeDoubleSheetR), Axis23(X), Axis24(Z) 해제
- `FB_Camin_Dsheet_R_Anode`: CAMIN 대상이 동일한 Axis25/23/24 (VR02)
  - Cathode FB가 Anode 축을 해제하면 → Anode FB가 인계

**의미:** L(Cathode) 더블 시트가 완료되면, L 측이 R(Anode) 축의 CAMOUT을 발동해 R 측에게 VR02 점유를 넘깁니다.

---

## 8. 1 사이클 전체 CAM 전환 흐름

```
[자동 시작 버튼]
  전제: VR01 + VR02 + VR04 모두 First_Cam_Starting_Position
       ↓
┌──────────────────────────────────────────────┐
│ [LC_RUN 스텝] — VR03 PP CAM (LC 측)           │  ← STACK 시퀀스
│   1. RESET STACK_LC_RUN_CAMIN                │
│   2. VR03 이동 (비전 @ 80/170/120~180/200mm)  │
│   3. 종료: VR03 Done AND RA_RUN.Sync 완료     │
│   4. LC_RUN_END → GRAPH 전환                 │
└──────────────────────────────────────────────┘
       ↓ (병렬: Dsheet_L_Cathode VR01 동작 중)
┌──────────────────────────────────────────────┐
│ [RA_RUN 스텝] — VR03 PP CAM (RA 측)           │
│   1. RESET STACK_RA_RUN_CAMIN                │
│   2. VR03 이동 (비전 타이밍 LC/RA 역전)        │
│   3. 종료: VR03 Done AND LC_RUN.Sync 완료     │
│   4. RA_RUN_END → GRAPH 전환                 │
└──────────────────────────────────────────────┘
       ↓ (병렬: Dsheet_R_Anode VR02 동작 중)
┌──────────────────────────────────────────────┐
│ [LC_STACK 스텝] — VR04 Mandrel CAM            │
│   대상: LC_Mandrel1Y/1Z/2Y/2Z_GET             │
│        RA_Mandrel1Y/1Z/2Y/2Z_PUT             │
│        TableZ (현재 주석 처리)                │
│   InSync: 8축 CamIn.InSync AND               │
│   First: 9축 Synchronizing_POS AND           │
└──────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────┐
│ [RA_STACK 스텝] — VR04 Mandrel CAM (역전)     │
│   대상: LC_Mandrel GET↔PUT 역전               │
└──────────────────────────────────────────────┘
       ↓
  N층 반복 → 1셀 완성 → JR Shuttle 출고
```

---

## 9. 미확인 부분 (분석 한계)

| 항목 | 상태 | 위치 추정 |
|------|------|---------|
| `STACK_LC/RA_RUN_CAMIN` **SET** 코드 | 미확인 | Sub_400~500 또는 OB_CAM |
| `FB_Camin_STACK_LC_RUN / RA_RUN` 상세 | 파일 크기 초과 (33KB) | `exports/.../Stack/FB_Camin_STACK_LC_RUN.md` |
| VR04 맨드릴 CAMIN/CAMOUT 전환 트리거 | 부분 확인 | `FB_Camin_STACK_LC_STACK.md` 코드 확인 필요 |

---

## 10. 약어 치트시트

| 약어 | 의미 |
|------|------|
| VR | Virtual Reference (가상 리딩 축) |
| CAMIN | MC_CAMIN — CAM 동기화 진입 FB |
| CAMOUT | MC_CAMOUT — CAM 동기화 해제 FB |
| InSync | MC_CAMIN.InSync — 완전 동기화 완료 출력 |
| Synchronizing_POS | StatusWord 비트 — 처음 캠 시작 위치 도달 |
| PP | Pick & Place |
| LC | Left Cathode (음극, 왼쪽) |
| RA | Right Anode (양극, 오른쪽) |
| GET | 해당 사이클에서 전극을 받는 맨드릴 |
| PUT | 해당 사이클에서 전극을 내려놓는 맨드릴 |
| ASQ | Automatic Sequence |
| FSQ | Function Sequence (수동 기능) |
| ISQ | Initialize Sequence |
| Sub_N00 | 시퀀스 번호 100 단위 (N×100번 스텝 그룹) |
