# LC_RUN 단계 — 가상축 + CAM 동기 구조

- **프로젝트**: `PowerCo_Stack_20260421_R142_KJR_R02`
- **CPU**: `Z-AF051.S01.KE01.PLC`
- **상위 문서**: [`FB_auto_Sequence_stack_구조.md`](FB_auto_Sequence_stack_구조.md)
- **분석 대상 블록**:
  - `FB_Auto_Sub1_Stack_200` [#2200, LAD] — LC_RUN sub-step 실행 FB
  - `FB_Camin_STACK_LC_RUN` [#8003, LAD] — CAM coupling 전담 FB
  - `DB_Global_Cam_Control` [#52, GlobalDB] — 두 FB 사이 핸드셰이크 DB
- **작성일**: 2026-05-11

---

## 0) 한눈에 보기

```
GRAPH 시퀀서 (FB_auto_Sequence_stack)
     │  Step 12 = LC_RUN 활성  → DB_Stack_DATA.ASQ_CMD.LC_RUN_CMD = 1
     ▼
FB_Auto_Sub1_Stack_200 (LAD)                ← 본 FB. 가상축만 직접 명령
     │  내부 sub-step: 200 → 210 → 220 → 230 → 240 …
     │
     │   sub-step 200: LC_RUN_CMD 첫 진입, 다음 단계 enable           (Move 210)
     │   sub-step 210: VR03 ActualPosition == 0.0 & StatusWord.x5=StandStill 확인 (Move 220)
     │   sub-step 220: DB_Global_Cam_Control.STACK_LC_RUN_InSync 확인 후
     │                 STACK_LC_RUN_CAMIN 비트 RESET                   (Move 230)
     │   sub-step 230: ★ 핵심
     │       1) MC_MOVERELATIVE_VR_SUB1 호출
     │            Axis     = VR03_StackLeadingAxis   (Virtual Master)
     │            Distance = 360.0 (한 사이클 = 1회전)
     │            Velocity = DB_Stack_DATA.VR03_Velocty
     │       2) ActualPosition 80°/120°/180°/230° 통과 시
     │            Vision Trigger 비트 Set
     │              ├ 80°  : DB_1st_Surface_Vision_LC.Trg[0]
     │              ├ 120° : DB_1st_Surface_Vision_RA.Trg[0]
     │              ├ 180° : DB_2nd_Surface_Vision_LC/RA.Trg[0]
     │              └ 230° : DB_Align_Vision.Trg[18]
     │       3) MOVERELATIVE.Done → Move 240
     ▼
FB_Camin_STACK_LC_RUN  [#8003]              ← CAM coupling 전담 FB (별도 호출)
     │  STACK_LC_RUN_CAMIN 비트가 켜져 있으면 25개 MC_CAMIN 인스턴스 실행
     ▼
실제 SINAMICS 서보 25축이 가상축 위치(0~360°)에 맞춰 동기 추종
```

> **핵심**: 마스터 가상축은 `FB_Auto_Sub1_Stack_200` 이 돌리고,
> 슬레이브 서보 결합(CamIn)은 `FB_Camin_STACK_LC_RUN` 이 한다 —
> 두 FB가 `DB_Global_Cam_Control` 글로벌 비트로 핸드셰이크합니다.

---

## 1) 가상축 — `VR03_StackLeadingAxis`

Stack 영역의 **Leading Master Axis**. 물리 인코더 없이 PLC 내부에서 0~360° 위치를 만들어내는 **TO_PositioningAxis (Virtual)**.

`FB_Auto_Sub1_Stack_200` 의 Static에 다음 4개 모션 인스턴스가 선언되어 있습니다.

| Static 멤버 | Datatype | 역할 |
|---|---|---|
| `MC_POWER_VR_SUB01` | MC_POWER | 가상축 활성화 |
| `MC_HOME_VR_SUB1`   | MC_HOME  | 0°로 직접 세팅 (Mode = direct) |
| `MC_HALT_VR_SUB1`   | MC_HALT  | 비상정지 |
| **`MC_MOVERELATIVE_VR_SUB1`** | MC_MOVERELATIVE | **0 → +360° 회전 (실제 호출은 sub-step 230)** |

> VR03의 한 바퀴(0→360°) = **한 셀(LC 1장 + RA 1장) 적층 사이클**.

---

## 2) sub-step 흐름 상세

`FB_Auto_Sub1_Stack_200` 은 LAD 컴파일유닛이 sub-step 단위로 줄지어 있고, 각 네트워크의 진입 조건이 `DB_Stack_DATA.ASQ_CMD.LC_RUN_CMD = 1` AND `DI_Auto_Number.Auto_Number_Stack == n00` 입니다.

### sub-step 200 → 210
- 조건: `LC_RUN_CMD` 첫 진입 + `Auto_Number_Stack == 200`
- 동작: `Auto_Number_Stack := 210` (Move)

### sub-step 210 → 220
- 조건: `Auto_Number_Stack == 210`
  AND `VR03_StackLeadingAxis.ActualPosition == 0.0`
  AND `VR03_StackLeadingAxis.StatusWord.%X5` (StandStill)
- 동작: `Auto_Number_Stack := 220`
- 의미: **가상축이 0°에 정확히 정지**해 있는지 확인 후 진행 (CamIn 시 마스터/슬레이브 위치 동기화 보장)

### sub-step 220 → 230
- 조건: `Auto_Number_Stack == 220`
  AND (`DB_Global_Cam_Control.STACK_LC_RUN_InSync` OR `AlwaysTRUE`)
- 동작:
  1. `R DB_Global_Cam_Control.STACK_LC_RUN_CAMIN` (CAMIN 요청 비트 리셋)
  2. `Auto_Number_Stack := 230`
- 의미: 25개 슬레이브가 모두 InSync 됐다는 응답을 받으면 CAMIN 트리거를 떨군다 (S7-1500 모션은 `Execute` 한 번 떨어뜨려도 InSync 상태가 유지됨)

### sub-step 230 — ★ 메인 동작
- 조건: `Auto_Number_Stack == 230` AND `LC_RUN_CMD`
- 동작:
  1. **`MC_MOVERELATIVE` 호출** — instance `MC_MOVERELATIVE_VR_SUB1`
     - Axis = `VR03_StackLeadingAxis`
     - Distance = `360.0`
     - Velocity = `DB_Stack_DATA.VR03_Velocty`
  2. `VR03_StackLeadingAxis.ActualPosition` 추적하여 위치별 비전 트리거 Set:
     - `>= 80.0°`  → `DB_1st_Surface_Vision_LC.1st_Surface_LC_SQ_Vision_Trg_Bit[0]`
     - `>= 120.0°` → `DB_1st_Surface_Vision_RA.1st_Surface_RA_SQ_Vision_Trg_Bit[0]`
     - `>= 180.0°` → `DB_2nd_Surface_Vision_LC/RA.2nd_Surface_*_SQ_Vision_Trg_Bit[0]`
     - `>= 230.0°` → `DB_Align_Vision.Align_SQ_Vision_Trg_Bit[18]`
  3. `MC_MOVERELATIVE_VR_SUB1.Done` → `Auto_Number_Stack := 240`
- 의미: **가상축을 한 바퀴 돌리는 동안, 캠 결합된 25개 서보가 동시에 한 사이클 동작 + 4개의 비전 검사 시점에 트리거 발사**

### sub-step 230(보조) — 서보 위치 비트 일괄 리셋
같은 230 단계에서 다수의 `RBitfield`(N=16)로 다음 축들의 `Position[0]` 16비트를 리셋:
- Axis_11~16 (Cathode Reverse/Main P&P)
- Axis_17~19 (Cathode Align Table X/Y/θ)
- Axis_26~31 (Anode Reverse/Main P&P)
- Axis_33~35 (Anode Align Table X/Y/θ)
- Axis_37/39 (Stack table swing roller Z01/R01)
- Axis_2 (Sepa UW Bed EPC1 Y)

→ 다음 사이클 위치 명령 비트맵 클리어 용도.

---

## 3) CAM coupling — `FB_Camin_STACK_LC_RUN` [#8003]

이 FB의 Static 영역에 **MC_CAMIN 25개 + MC_CAMOUT 25개**가 선언되어 있습니다.
각 `MC_CAMIN` 의 입력:
- `Master` = `VR03_StackLeadingAxis` (TO_Axis)
- `Slave`  = 해당 실서보 (TO_SynchronousAxis)
- `CamTable` = 미리 엔지니어링된 캠 프로파일 (TO_Cam)

### 3-1. LC (Cathode) GET → 적층

| CAMIN 인스턴스명 | 결합 슬레이브 (DB_Servo) | 동작 |
|---|---|---|
| `CAMIN_Cam_STACK_LC_AlignT_GET` | Axis_19 Cathode Align Table θ | 음극 정렬 회전 |
| `CAMIN_Cam_STACK_LC_AlignX_GET` | Axis_17 Cathode Align Table X | 음극 정렬 X |
| `CAMIN_Cam_STACK_LC_AlignY_GET` | Axis_18 Cathode Align Table Y | 음극 정렬 Y |
| `CAMIN_Cam_STACK_LC_PP1X_GET` | Axis_13 Cathode Main P&P Head01 X | 1번 P&P 헤드 X (집기) |
| `CAMIN_Cam_STACK_LC_PP1Z_GET` | Axis_14 Cathode Main P&P Head01 Z | 1번 P&P 헤드 Z (상하) |
| `CAMIN_Cam_STACK_LC_PP2X_PUT` | Axis_15 Cathode Main P&P Head02 X | 2번 P&P 헤드 X (놓기) |
| `CAMIN_Cam_STACK_LC_PP2Z_PUT` | Axis_16 Cathode Main P&P Head02 Z | 2번 P&P 헤드 Z |
| `CAMIN_Cam_STACK_LC_ReverseR_PUT` | Axis_12 Cathode Reverse P&P R | 반전 P&P 회전 |
| `CAMIN_Cam_STACK_LC_ReverseZ_PUT` | Axis_11 Cathode Reverse P&P Z | 반전 P&P Z |

### 3-2. RA (Anode) PUT

| CAMIN 인스턴스명 | 결합 슬레이브 |
|---|---|
| `CAMIN_Cam_STACK_RA_AlignT_PUT` | Axis_35 Anode Align Table θ |
| `CAMIN_Cam_STACK_RA_AlignX_PUT` | Axis_33 Anode Align Table X |
| `CAMIN_Cam_STACK_RA_AlignY_PUT` | Axis_34 Anode Align Table Y |
| `CAMIN_Cam_STACK_RA_PP1X_PUT`   | Axis_28 Anode Main P&P Head01 X |
| `CAMIN_Cam_STACK_RA_PP1Z_PUT`   | Axis_29 Anode Main P&P Head01 Z |
| `CAMIN_Cam_STACK_RA_PP2X_GET`   | Axis_30 Anode Main P&P Head02 X |
| `CAMIN_Cam_STACK_RA_PP2Z_GET`   | Axis_31 Anode Main P&P Head02 Z |
| `CAMIN_Cam_STACK_RA_ReverseR_GET` | Axis_27 Anode Reverse P&P R |
| `CAMIN_Cam_STACK_RA_ReverseZ_GET` | Axis_26 Anode Reverse P&P Z |

### 3-3. 적층 테이블 / EPC / 피더

| CAMIN 인스턴스명 | 결합 슬레이브 | 비고 |
|---|---|---|
| `CAMIN_Cam_STACK_Swing1R_LC` / `Swing1Z_LC` | Axis_37 Stack table swing roller Z01 + R | 1번 스윙 롤러 R/Z |
| `CAMIN_Cam_STACK_Swing2R_LC` / `Swing2Z_LC` | Axis_39 Stack table swing roller (2번) | 2번 스윙 롤러 R/Z |
| `CAMIN_Cam_STACK_EPC1Y_N` | Axis_2 Sepa UW Bed EPC1 Y | 셀퍼레이터 사행 보정 #1 |
| `CAMIN_Cam_STACK_EPC2Y_N` | Sepa UW Bed EPC2 Y | 셀퍼레이터 사행 보정 #2 |
| `CAMIN_Cam_STACK_FeederR` | 피더 회전 롤러 | 분리막 송출 |

### 3-4. 의미

> **VR03 의 1회전(360°) 동안 25축이 각자의 캠 프로파일을 따라 동기 동작**.
> 물리적으로는 음극 1장을 매거진에서 집어올려 → 반전 → 얼라인 → 스택 위 안착,
> 동시에 분리막을 EPC로 잡아주며 피더가 보내고, 동시에 양극도 같은 사이클로 처리.

각 CAMIN에는 짝이 되는 `CAMOUT_Cam_STACK_*` (MC_CAMOUT) 인스턴스가 있어 사이클 종료 시 결합 해제 가능.

---

## 4) 두 FB 사이 핸드셰이크 — `DB_Global_Cam_Control` [#52]

`FB_Auto_Sub1_Stack_200` 은 직접 MC_CAMIN을 부르지 않습니다. 대신 글로벌 DB의 비트 토글로 `FB_Camin_STACK_LC_RUN` 에 명령을 전달합니다.

| 비트 / 필드 | 의미 | 누가 Set / Reset |
|---|---|---|
| `STACK_LC_RUN_CAMIN` | "지금 CamIn 걸어라" | 진입 시 다른 시퀀스/모드 FB가 Set, sub-step 220에서 Reset |
| `STACK_LC_RUN_InSync` | "모든 슬레이브 InSync 됐다" | `FB_Camin_STACK_LC_RUN` 이 25개 MC_CAMIN.InSync 합쳐서 Set |
| `Cam_STACK_RA_RUN_Contol.Fist.First_Cam_Starting_Position` | RA 첫 사이클 진입점 보정 | sub-step 230 진행 조건으로 사용 |

### 정상 시퀀스
1. `STACK_LC_RUN_CAMIN` Set → `FB_Camin_STACK_LC_RUN` 이 25축 모두에 `MC_CAMIN.Execute=1`
2. 25축 전부 InSync → `STACK_LC_RUN_InSync` Set
3. `FB_Auto_Sub1_Stack_200` sub-step 220 에서 InSync 확인 → `STACK_LC_RUN_CAMIN` Reset
4. sub-step 230: `MC_MOVERELATIVE` 로 가상축 +360° 시작 → 25개 슬레이브가 캠 따라 같이 움직임
5. 위치별 비전 트리거 발사 (80°/120°/180°/230°)
6. 가상축 Done → sub-step 240 진입 (이후 CAMOUT 호출 단계로 추정)

---

## 5) 보조 인프라

| 블록 | 종류 | 역할 |
|---|---|---|
| `FB_Interpolate_Cam` | FB #53 | 캠 프로파일 보간 (런타임 가변 캠 생성/수정) |
| `FB_AXIS_TO_CAM_STATUS` | FB #57 | 축의 캠 결합 상태(InGear/InSync/CamIndex) 모니터링 |
| `FC_AXIS_TO_CAM_STATUS` | FC #43 | 동일 — 함수 형태 호출용 |
| `DB_GdbCam` | GlobalDB #8900 | 캠 프로파일 데이터 (Profile point arrays) |
| `DB_Global_Cam_Pos` | GlobalDB #346 | 캠 시작/끝/오프셋 위치 파라미터 |
| `FB_Camin_STACK_LC_STACK` | FB #8004 | LC_RUN 이후 Stack_2~8 단계용 별도 캠 세트 (LC) |
| `FB_Camin_STACK_RA_STACK` | FB #8006 | 동일 (RA) |
| `FB_Camin_STACK_RA_RUN`   | FB #8005 | RA_RUN 단계 CAM coupling |
| `FB_Camin_Single_LC_RUN`  | FB #8001 | 단동 모드 LC_RUN CAM coupling |
| `FB_Camin_Single_RA_RUN`  | FB #8002 | 단동 모드 RA_RUN CAM coupling |
| `FB_Camin_Dsheet_L_Cathode` | FB #8010 | 분리막 L (Cathode 측) CAM |
| `FB_Camin_Dsheet_R_Anode`   | FB #8020 | 분리막 R (Anode 측) CAM |
| `FB_Camin_Unwinder` | FB #8030 | 분리막 Unwinder CAM |
| `FB_Initial_STACK_LC_RUN` | FB #69 | 초기 진입 시 캠 위치 정렬 |
| `FB_Manual_STACK_LC_RUN`  | FB #66 | 수동 모드 캠 동작 |
| `FB_Camin_STACK_ActiveBuffer` | FB #8009 | "다음에 적용할 캠" 버퍼 전환 (제품 변경 시 무중단 캠 스왑 추정) |

---

## 6) 한 줄 요약

> **LC_RUN_CMD 가 켜지면, `FB_Auto_Sub1_Stack_200` 은 가상축 `VR03_StackLeadingAxis` 를 `MC_MOVERELATIVE` 로 360° 한 바퀴 돌리는 일만 합니다.
> 실제 25개의 SINAMICS 서보(Cathode/Anode P&P, Reverse, Align Table, Stack Swing roller, EPC, Feeder)는
> 별도 `FB_Camin_STACK_LC_RUN` 이 미리 걸어둔 `MC_CAMIN` 으로 그 가상축을 마스터 삼아 캠 프로파일을 따라가며 적층 동작을 수행합니다.
> 두 FB 의 협조는 `DB_Global_Cam_Control` 의 비트 핸드셰이크(`_CAMIN`/`_InSync`) 로 이뤄집니다.**

---

## 7) 참고 — 추출된 XML 파일 위치

- `exports\FB_Auto_Sub1_Stack_200.xml` (174 KB)
- `exports\FB_Camin_STACK_LC_RUN.xml` (3.4 MB) — MC_CAMIN/CAMOUT 25+25 인스턴스 포함
