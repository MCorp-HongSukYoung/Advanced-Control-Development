# PowerCo_Stack — CAM 각도 단위 Unit별 동작 Sequence

> 생성: 2026-05-14 by /onboard-plc 분석  
> 보완: 2026-05-15 — Reverse R/Z CAM·Sequential 동작 추가 (FB_Camin_STACK_LC/RA_RUN, Sub1_600/700); CAM 각도 범위 추가 (TIA Portal 직접 확인: GET=20°~180°, PUT=180°~340°)
> 소스: exports/PowerCo_Stack 디지스트 + Sub FB 코드 분석
> 관련 문서: [PowerCo_Stack_CAM_Sequence.md](PowerCo_Stack_CAM_Sequence.md)

---

## 1 Stacking Cycle 구조

1 Stacking Cycle은 4개 Phase가 순서대로 반복됩니다.

```
[LC_RUN] → [LC_STACK] → [RA_RUN] → [RA_STACK]  × N층
  VR03↑       VR04↑       VR03↑       VR04↑
```

VR01/VR02(Dsheet)는 4개 Phase 내내 상시 회전합니다.

---

## Phase 1: LC_RUN — VR03 (0° → 360°)

**목적**: Cathode P&P Head가 전극을 Align → 픽업 → Stack 위로 이송

- VR03 속도: `360° / PPMovingTime`
- 활성 캠 그룹: STACK_LC (AlignTableX/Y/θ, PP1X/Z, PP2X/Z, **ReverseR/Z**)
- 캠 프로파일 종류: LC 측 **PUT**, RA 측 **GET** (Cathode Reverse가 전극을 AlignTable로 전달, Anode Reverse는 다음 전극 수령 대기)

| VR03 각도 | 동작 | 근거 |
|-----------|------|------|
| 0° | VR03 홈 확인 (`ActualPosition == 0.0` AND `StatusWord` OK), STACK_LC_RUN_CAMIN 진입 대기 | Sub1_200, Step 210 |
| 0° 직후 | `RESET STACK_LC_RUN_CAMIN` (이전 CAM 해제), VR03 RUN 시작.<br>**Reverse R/Z도 이 시점에 CAMIN 등록** (`Cam_STACK_LC_ReverseR_PUT`, `Cam_STACK_LC_ReverseZ_PUT`) | Sub1_200, Step 220→230 |
| 20°~180° | **Anode Reverse R(Axis27) / Z(Axis26) GET** — 다음 Anode 전극 수령 구간 | FB_Camin_STACK_LC_RUN |
| 180°~340° | **Cathode Reverse R(Axis12) / Z(Axis11) PUT** — 전극을 AlignTable 방향으로 이송 | FB_Camin_STACK_LC_RUN |
| 0°~20°, 340°~360° | Reverse Dwell (정지, 위치 유지) | — |
| ~80° | **RA Vision 카메라 트리거** — RA 측 전극 위치 사전 확인 | Sub1_200, Step 230 |
| 120°~180° | **Align Vision 윈도우** — 정렬 카메라 연속 활성 | Sub1_200, Step 230 |
| ~170° | **LC Vision 카메라 트리거** — Cathode 전극 정밀 위치 확인 | Sub1_200, Step 230 |
| ~200° | **LC VAC ON** — PP Head가 Cathode 전극을 흡착 | Sub1_200, Step 230 |
| 360° | `MC_MOVERELATIVE.Done` — VR03 1회전 완료 | Sub1_200 |
| 360° 후 | **AND** `Cam_STACK_RA_RUN_Contol.Fist.First_Cam_Starting_Position` → Step 240 전환 | Sub1_200, Step 230→240 |
| Step 240 | **Reverse 목표 포지션 SET**: `Axis11(Reverse Z).Position[3]`, `Axis12(Reverse R).Position[3]` — LC_Single에서 사용할 다음 이동 목표 예약 | Sub1_200, Step 240 |

> **전환 게이트 의미**: RA_RUN 다음 Phase 준비 완료 여부를 교차 확인 (핸드오프 게이트).
> LC_RUN 단독 완료만으로 전환하지 않고, 반대편 RA 캠이 대기 위치에 있을 때만 진행.

Phase 완료: Step 299 → `ASQ_END.LC_RUN_END = TRUE` → GRAPH 전환 신호

---

## Phase 2: LC_STACK — VR04 (0° → 360°)

**목적**: Mandrel이 Cathode 전극을 셀 적층체에 압착

- VR04 속도: `360° / MandrelMovingTime`
- 활성 캠 그룹: STACK_LC (Mandrel1/2 Y/Z)
- 캠 프로파일 종류: **PUT** (Mandrel이 전극을 적층체에 전달)

| VR04 각도 | 동작 |
|-----------|------|
| 0° | Mandrel 수령 위치 대기, LC_STACK_CAMIN 활성 |
| 0°→180° | Mandrel Y/Z가 PUT 캠 커브 추종 → Cathode 전극을 셀 적층체 위에 내려놓음 |
| 180°→360° | Mandrel 복귀, 전극 분리 확인 |
| 360° | VR04 1회전 완료 |

이후 `LC_Single_CMD` 실행:
- P&P Head X/Z 이동 (다음 전극 대기 위치로)
- `DB_Info.Electrode_Cathode[0..4]` 버퍼에서 다음 전극 준비
- `FDB_Zone01.Pause_State == TRUE` 조건 확인
- Vacuum 제어: `DI_Unit01_Stack_LC_Main_PP_Head_VAC_1/2`, `DI_Unit03_LC_Double_Sheet_VAC`

Phase 완료: `ASQ_END.LC_STACK_END = TRUE`

---

## Phase 3: RA_RUN — VR03 (0° → 360°)

**목적**: Anode P&P Head가 전극을 Align → 픽업 → Stack 위로 이송

LC_RUN과 구조는 동일하나 Vision 트리거 순서가 반전됩니다.

- 활성 캠 그룹: STACK_RA (AlignTableX/Y/θ, PP1X/Z, PP2X/Z, **ReverseR/Z**)
- 캠 프로파일 종류: LC 측 **GET**, RA 측 **PUT** (LC_RUN과 반전 — Anode Reverse가 PUT, Cathode Reverse가 GET)

| VR03 각도 | 동작 | 비고 |
|-----------|------|------|
| 0° | VR03 홈, STACK_RA_RUN_CAMIN 진입 | |
| 0° 직후 | `RESET STACK_RA_RUN_CAMIN`, VR03 RUN 시작.<br>**Reverse R/Z도 CAMIN 등록** (`Cam_STACK_RA_ReverseR_PUT`, `Cam_STACK_RA_ReverseZ_PUT`) | Sub1_300, Step 320 |
| 20°~180° | **Cathode Reverse R(Axis12) / Z(Axis11) GET** — 다음 Cathode 전극 수령 구간 | FB_Camin_STACK_RA_RUN |
| 180°~340° | **Anode Reverse R(Axis27) / Z(Axis26) PUT** — 전극을 AlignTable 방향으로 이송 | FB_Camin_STACK_RA_RUN |
| 0°~20°, 340°~360° | Reverse Dwell (정지, 위치 유지) | — |
| ~80° | **LC Vision 카메라 트리거** | LC_RUN의 80°는 RA였음 — 반전 |
| 120°~180° | **Align Vision 윈도우** | |
| ~170° | **RA Vision 카메라 트리거** | |
| ~200° | **RA VAC ON** — Anode 전극 흡착 | |
| 360° | MC_MOVERELATIVE.Done | |
| 360° 후 | **AND** `Cam_STACK_LC_RUN_Contol.Fist.First_Cam_Starting_Position` → 전환 | LC 측 교차 게이트 |

Phase 완료: Step 399 → `ASQ_END.RA_RUN_END = TRUE`

---

## Phase 4: RA_STACK — VR04 (0° → 360°)

LC_STACK의 Anode 대칭 버전.

- 활성 캠 그룹: STACK_RA (Mandrel1/2 Y/Z)
- 캠 프로파일 종류: **GET** (Mandrel이 Anode 전극을 수령)

| VR04 각도 | 동작 |
|-----------|------|
| 0° | Mandrel 수령 위치 대기, RA_STACK_CAMIN 활성 |
| 0°→360° | Mandrel Y/Z가 GET 캠 커브 추종 → Anode 전극 수령 및 압착 |
| 360° | VR04 1회전 완료 |

이후 `RA_Single_CMD` 실행:
- `DB_Info.Electrode_Anode[0..4]` 버퍼 전극 준비
- `IEC_Timer_AUTO_ANODE_VISION.Q` 게이트 (Anode 비전 타이머 확인)
- Align Unit Table X/Y/θ 복귀

Phase 완료: `ASQ_END.RA_STACK_END = TRUE`

---

## VR01/VR02 — Dsheet 검출 (상시 운전)

4개 Phase와 무관하게 상시 회전합니다.

| VR | Slave 축 | 캠 그룹 | 역할 |
|----|----------|---------|------|
| VR01 | Axis03(CathodeX), Axis04(Z), Axis_R | Dsheet_L_Cathode | Cathode 이중 시트 검출 롤러 |
| VR02 | Axis25(AnodeR), Axis23(X), Axis24(Z) | Dsheet_R_Anode | Anode 이중 시트 검출 롤러 |

### Cross-handoff 패턴

- `FB_Camin_Dsheet_L_Cathode` → VR02의 Anode 축(Axis25/23/24)에 CAMOUT 신호 전송
- Cathode 공정 완료 시 Anode Dsheet 캠을 해제하는 교번 설계
- 반대로 `FB_Camin_Dsheet_R_Anode` → VR01 Cathode 축 CAMOUT

---

## STACK_TABLE / STACK_SEPA — VR03에 종속

VR03 회전 내 특정 각도에서 슬레이브 축들이 동작합니다.

| 그룹 | 캠 프로파일 | GET/PUT | 동작 |
|------|------------|---------|------|
| STACK_TABLE | TableZ | GET / PUT | 적층 테이블 Z축 승강 |
| STACK_TABLE | Swing1 R/Z | LC / RA | 스윙 암 1번 회전·승강 |
| STACK_TABLE | Swing2 R/Z | LC / RA | 스윙 암 2번 회전·승강 |
| STACK_SEPA | ActiveBuffer | GET / PUT | 분리막 피더 활성 버퍼 |
| STACK_SEPA | EPC1Y | N / P | 분리막 사행 보정 1번 (Edge Position Control) |
| STACK_SEPA | EPC2Y | N / P | 분리막 사행 보정 2번 |
| STACK_SEPA | FeederR | (단일) | 분리막 공급 롤러 |

---

## Reverse PP 동작 상세

Reverse PP(반전 픽앤플레이스)는 **두 레이어**에서 동작합니다.

### Layer 1: CAM 추종 (VR03 연동)

RUN Phase 동안 Reverse R/Z는 VR03을 마스터로 캠 프로파일을 추종합니다.  
CAMIN은 **두 개의 신호**로 구분됩니다:

| CAMIN 신호 | 사용 블록 | 동작 |
|------------|-----------|------|
| `STACK_LC_RUN_CAMIN` | `FB_Camin_STACK_LC_RUN` | 주 스태킹 LC RUN Phase에서 Reverse 동기화 |
| `Single_LC_RUN_CAMIN` | `FB_Camin_Single_LC_RUN` | LC_Single 버퍼 채우기 Phase에서 Reverse 동기화 |

**CAMIN 신호별 Slave 축 매핑:**

| CAMIN 신호 | 캠 이름 | Slave 축 | 방향 | VR03 범위 | 역할 |
|------------|---------|----------|------|-----------|------|
| `STACK_LC_RUN_CAMIN` | `Cam_STACK_LC_ReverseR_PUT` | **Axis12** (Cathode Reverse R, TB117) | PUT | **180°~340°** | Cathode 전극 AlignTable 이송 |
| `STACK_LC_RUN_CAMIN` | `Cam_STACK_LC_ReverseZ_PUT` | **Axis11** (Cathode Reverse Z, TB116) | PUT | **180°~340°** | 동상 |
| `STACK_LC_RUN_CAMIN` | `Cam_STACK_RA_ReverseR_GET` | Axis27 (Anode Reverse R, TB141) | GET | **20°~180°** | 다음 Anode 전극 수령 대기 |
| `STACK_LC_RUN_CAMIN` | `Cam_STACK_RA_ReverseZ_GET` | Axis26 (Anode Reverse Z, TB140) | GET | **20°~180°** | 동상 |
| `Single_LC_RUN_CAMIN` | `Cam_STACK_LC_ReverseR_PUT` | **Axis27** (Anode Reverse R, TB141) | PUT | **180°~340°** | ⚠️ STACK_LC_RUN과 다른 축 |
| `Single_LC_RUN_CAMIN` | `Cam_STACK_LC_ReverseZ_PUT` | **Axis26** (Anode Reverse Z, TB140) | PUT | **180°~340°** | ⚠️ STACK_LC_RUN과 다른 축 |
| `STACK_RA_RUN_CAMIN` | `Cam_STACK_RA_ReverseR_PUT` | Axis27 (Anode Reverse R, TB141) | PUT | **180°~340°** | Anode 전극 AlignTable 이송 |
| `STACK_RA_RUN_CAMIN` | `Cam_STACK_RA_ReverseZ_PUT` | Axis26 (Anode Reverse Z, TB140) | PUT | **180°~340°** | 동상 |
| `STACK_RA_RUN_CAMIN` | `Cam_STACK_LC_ReverseR_GET` | Axis12 (Cathode Reverse R, TB117) | GET | **20°~180°** | 다음 Cathode 전극 수령 대기 |
| `STACK_RA_RUN_CAMIN` | `Cam_STACK_LC_ReverseZ_GET` | Axis11 (Cathode Reverse Z, TB116) | GET | **20°~180°** | 동상 |

#### Reverse CAM 각도 범위 (TIA Portal 직접 확인, 2026-05-15)

| 구간 | VR03 범위 | 의미 |
|------|-----------|------|
| GET (전극 수령) | **20°~180°** | Reverse 헤드가 PP Head01로부터 전극을 픽업하는 구간 |
| PUT (전극 전달) | **180°~340°** | Reverse 헤드가 AlignTable에 전극을 이송하는 구간 |
| Dwell (정지) | 0°~20°, 340°~360° | 위치 유지, 다음 동작 준비 |

- R축(회전)과 Z축(승강)은 **동일한 VR03 각도 범위**에서 동작합니다.

> **⚠️ Single_LC_RUN 주의**: 같은 캠 프로파일(`Cam_STACK_LC_ReverseX_PUT`)이 `Single_LC_RUN_CAMIN`에서는 **Anode Reverse 축(Axis26/27)** 에 적용됩니다. STACK_LC_RUN(Cathode Axis11/12)과 대상 축이 다릅니다.

> **InSync 조건**: Reverse R/Z의 `CamIn.InSync`도 `STACK_LC/RA_RUN_InSync` 조건에 AND 포함됩니다.
> 즉, Reverse 동기화가 실패하면 Step 220→230 전환이 차단됩니다.

> **CAM 이름 불일치**: `CAMIN_Cam_STACK_LC_ReverseR_PUT` 호출 시 실제 캠 오브젝트 인자로
> `Cam_STACK_LC_ReverseX_PUT`이 전달됩니다 — R축 캠이 `X`로 네이밍된 불일치가 코드에 존재합니다.

#### CAM 각도 커브 데이터 접근 방법

`Cam_STACK_LC_ReverseX_PUT` 등 캠 오브젝트의 **VR03 각도별 슬레이브 위치 테이블**은 TIA Portal Technology Object로 저장됩니다. 현재 export 툴은 프로그램 블록만 추출하며 Technology Object는 대상이 아닙니다.

| 접근 방법 | 가능 여부 |
|-----------|-----------|
| `.md` / `.xml` export 파일 | ❌ 포함되지 않음 |
| TIA Portal UI → Technology Objects → Cam | ✅ 직접 확인 가능 |
| 런타임 HMI 읽기 (`DB_HMICamValue`, `FB_HMIMonitoring_ReadCamProfile`) | ✅ PLC 실행 중 가능 |
| TIA Portal Openness Technology Object API | 🔧 현재 미구현 |

---

### Layer 2: Sequential 위치 이동 (LC_Single / RA_Single Steps)

CAM Phase 이후 버퍼 파이프라인 `[1]→[2]→[3]` 구간을 Reverse PP가 담당합니다.

#### Cathode (Sub1_600) Reverse 관련 Step 상세

**헤드 초기화 구간 (600→619) 중 Reverse 이동:**

| Step | 동작 | 전환 조건 |
|------|------|-----------|
| 617 | **Reverse Z up** — Axis11(Cathode Reverse Z) Position[2]로 이동 | `Axis11.Position[2]` AND `Command_bits[2]` |
| 618 | **Reverse R get** — Axis12(R) Position[2] 이동 + Axis11(Z) Position[3] 동시 지령 | `Axis12.Position[2]` AND `Command_bits[2]` AND `Axis11.Position[3]` → 619 |

**Step 625 경로 (Reverse GET, 버퍼 `[1]→[2]`):**

| Step | 동작 | 전환 조건 |
|------|------|-----------|
| 625 | PP1 Z Position[1] 이동 | `Axis14.Position[1]` AND `Command_bits[1]` |
| 626 | PP1 X Position[2] 이동 | `Axis13.Position[2]` AND `Command_bits[2]` |
| 627 | PP2 Z/X 이동 | PP2 축 Position 확인 |
| 628 | **VAC 전환**: Main PP VAC OFF → **Reverse PP VAC ON**<br>확인: `Main_VAC_1.Detect_Off` AND `Main_VAC_2.Detect_Off` AND `Reverse_VAC_1.Detect_On` AND `Reverse_VAC_2.Detect_On` | → 버퍼 `[1]→[2]`, 619로 루프백 |

**Step 635 경로 (AlignTable GET, 버퍼 `[2]→[3]`) 중 Reverse 이동:**

| Step | 동작 | 전환 조건 |
|------|------|-----------|
| 639 | **Reverse Z up** — Axis11 Position[2] | `Axis11.Position[2]` AND `Command_bits[2]` |
| 640 | **Reverse R put** — Axis12(R) Position[3] + Axis11(Z) Position[3] 동시 지령 (AlignTable로 전달) | `Axis12.Position[3]` AND `Axis11.Position[3]` AND 각 `Command_bits[3]` |
| 641 | **VAC 전환**: **Reverse PP VAC OFF** → AlignTable VAC ON<br>+ `IEC_Timer_AUTO_CATHODE_VISION.Q` (비전 타이머 만료 대기) | `Reverse_VAC_1/2.Detect_Off` AND `AlignTable_VAC.Detect_On` AND Vision Timer → 버퍼 `[2]→[3]` |

**Step 645 이후 경로 (버퍼 `[2]→[3]`) 중 추가 Reverse 이동:**

| Step | 동작 | 비고 |
|------|------|------|
| 642 | Reverse Z up (Axis11 Position[2]) | 641 완료 후 Reverse 복귀 준비 |
| 643 | Reverse R get (Axis12 Position[2] + Axis11 Position[3]) | 다음 전극 수령 준비 |
| 668 | Reverse Z up (Axis11 Position[2]) | 최종 버퍼 경로 |
| 669 | Reverse R put (Axis12 Position[3] + Axis11 Position[3]) | `[3]→[4]` 전달 준비 |

#### Anode (Sub1_700) — LC_Single의 대칭 구조

동일한 Step 패턴, 축만 Anode 대응 축으로 교체:

| LC 축 | RA 대응 축 |
|-------|-----------|
| Axis11 (Cathode Reverse Z) | Axis26 (Anode Reverse Z, TB140) |
| Axis12 (Cathode Reverse R) | Axis27 (Anode Reverse R, TB141) |
| `IEC_Timer_AUTO_CATHODE_VISION.Q` | `IEC_Timer_AUTO_ANODE_VISION.Q` |

---

## 전체 1 Cycle 각도 타임라인

```
Phase        VR03(°)    VR04(°)    주요 이벤트
─────────────────────────────────────────────────────────────────
LC_RUN       0 → 360    -          0°   : CAMIN 진입, RUN 시작
                                   80°  : RA Vision 트리거
                                   120°~180°: Align Vision 윈도우
                                   170° : LC Vision 트리거
                                   200° : LC VAC ON
                                   360° + RA First_Cam 게이트 → 전환

LC_STACK     -          0 → 360    Mandrel PUT 캠 추종
                                   → Cathode 전극 압착
                                   이후: LC_Single 버퍼 전극 준비
─────────────────────────────────────────────────────────────────
RA_RUN       0 → 360    -          0°   : CAMIN 진입, RUN 시작
                                   80°  : LC Vision 트리거  ← 반전
                                   120°~180°: Align Vision 윈도우
                                   170° : RA Vision 트리거  ← 반전
                                   200° : RA VAC ON
                                   360° + LC First_Cam 게이트 → 전환

RA_STACK     -          0 → 360    Mandrel GET 캠 추종
                                   → Anode 전극 수령
                                   이후: RA_Single 버퍼 전극 준비
─────────────────────────────────────────────────────────────────
         ↑ 위 4 Phase × N층 반복 (N = SeparatorStackingCount)

VR01/VR02    연속 회전   연속 회전  Dsheet 검출 상시 운전
```

---

## 각 Phase별 CAMIN/CAMOUT 전환 정리

| Phase | CAMIN 진입 조건 | CAMOUT 조건 |
|-------|----------------|-------------|
| LC_RUN | `DB_Global_Cam_Control.STACK_LC_RUN_CAMIN = TRUE` | Phase 시작 시 `RESET` (Step 220) |
| LC_STACK | `DB_Global_Cam_Control.STACK_LC_STACK_CAMIN = TRUE` | 다음 Phase 시작 시 `RESET` |
| RA_RUN | `DB_Global_Cam_Control.STACK_RA_RUN_CAMIN = TRUE` | Phase 시작 시 `RESET` (Step 320) |
| RA_STACK | `DB_Global_Cam_Control.STACK_RA_STACK_CAMIN = TRUE` | 다음 Phase 시작 시 `RESET` |
| Dsheet_L_Cathode | `DB_Global_Cam_Control.Dsheet_L_Cathode_CAMIN = TRUE` | `Dsheet_L_Cathode_CAMOUT` 신호 |
| Dsheet_R_Anode | `DB_Global_Cam_Control.Dsheet_R_Anode_CAMIN = TRUE` | `Dsheet_R_Anode_CAMOUT` 신호 |

InSync 확인: `DB_Global_Cam_Control.*_InSync` — **RUN Phase에 등록된 전 축 `CamIn.InSync AND`** 조건 (AlignTable, PP1, PP2, Reverse R/Z, Swing, TABLE, SEPA 모두 포함). Reverse R/Z InSync 실패 시에도 Phase 전환이 차단됨.

---

## Step 전환 조건 상세

### 공통 메커니즘

모든 Step 전환은 동일한 패턴으로 동작합니다:

```
[ASQ_CMD.*_CMD] AND [Auto_Number_Stack == 현재번호] AND [물리 확인 조건]
  → Move src=INT#다음번호 dst=Auto_Number_Stack
```

`AlwaysTRUE`가 OR 연결된 전환은 **바이패스 가능** (디버그/Dryrun 우회 경로)입니다.

---

### LC_RUN Step 전환 (Sub1_200)

| 현재 Step | 다음 Step | 전환 조건 |
|-----------|-----------|-----------|
| 200 | 210 | `LC_RUN_CMD` 수신 즉시 |
| 210 | 220 | `VR03.ActualPosition == 0.0` AND `VR03.StatusWord` |
| 220 | 230 | `STACK_LC_RUN_InSync` OR AlwaysTRUE → RESET CAMIN 후 진행 |
| 230 | 240 | `MC_MOVERELATIVE.Done` AND `Cam_STACK_RA_RUN.Fist.First_Cam_Starting_Position` OR AlwaysTRUE |
| 240 | 299 | `Cam_STACK_RA_RUN.Cam_Starting_Position` OR AlwaysTRUE (축 Position 비트 SET 동시) |
| 299 | — | `Auto_Number == 299` → `ASQ_END.LC_RUN_END = TRUE` |

**Step 230 내부 병렬 이벤트** (전환 조건 아님):

| VR03 각도 조건 | 트리거 |
|----------------|--------|
| `>= 80.0` | `DB_1st/2nd_Surface_Vision_RA.Vision_Trg_Bit[0]` SET |
| `>= 120.0` AND `<= 180.0` | `DB_Align_Vision.Align_SQ_Vision_Trg_Bit[18]` SET |
| `>= 170.0` | `DB_1st/2nd_Surface_Vision_LC.Vision_Trg_Bit[0]` SET |
| `>= 200.0` AND `Electrode_Cathode[2].Exist` | `LC_Align_Table_VAC.VacuumBlowOn` |

---

### RA_RUN Step 전환 (Sub1_300)

LC_RUN과 완전 대칭, Vision Bit 순서만 반전:

| 현재 Step | 다음 Step | 전환 조건 |
|-----------|-----------|-----------|
| 300 | 310 | `RA_RUN_CMD` 수신 즉시 |
| 310 | 320 | `VR03.ActualPosition == 0.0` AND `VR03.StatusWord` |
| 320 | 330 | `STACK_RA_RUN_InSync` OR AlwaysTRUE → RESET CAMIN 후 진행 |
| 330 | 340 | `MC_MOVERELATIVE.Done` AND `Cam_STACK_LC_RUN.Fist.First_Cam_Starting_Position` OR AlwaysTRUE |
| 340 | 399 | `Cam_STACK_LC_RUN.Cam_Starting_Position` OR AlwaysTRUE |
| 399 | — | `Auto_Number == 399` → `ASQ_END.RA_RUN_END = TRUE` |

**Step 330 내부 이벤트** — LC↔RA 반전:

| VR03 각도 조건 | 트리거 |
|----------------|--------|
| `>= 80.0` | **LC** Vision Bit (LC_RUN에서는 RA였음) |
| `>= 120.0` AND `<= 180.0` | Align Vision Bit |
| `>= 170.0` | **RA** Vision Bit (LC_RUN에서는 LC였음) |

---

### LC_Single Step 전환 (Sub1_600) — 전극 버퍼 파이프라인

#### 진입 및 헤드 초기화 (600 → 619)

| Step | → | 전환 조건 |
|------|---|-----------|
| 600 | 610 | `LC_Single_CMD` 수신 즉시 |
| 610 | 615 | 즉시 |
| 615 | 616 | Axis_14(PP1 Z) `Position[1]` AND `Command_bits[1]` AND Axis_16(PP2 Z) 동일 |
| 616 | 617 | Axis_13(PP1 X) `Position[1]` AND `Command_bits[1]` AND Axis_15(PP2 X) 동일 |
| 617 | 618 | Axis_11(Reverse Z) `Position[2]` AND `Command_bits[2]` |
| 618 | 619 | Axis_12(Reverse R) `Position[2]` AND `Command_bits[2]` AND Axis_11(Z) `Position[3]` |

#### Step 619: 분기점 (Sequence_Judgment)

`FDB_Zone01.Pause_State` 가 공통 전제 조건 (구역 일시정지 해제 대기)

| 우선순위 | 조건 | 이동 Step | 의미 |
|---------|------|-----------|------|
| 1 | `[0][1][2][3].Exist` | → 620 | Main PP Head 01 GET |
| 2 | `[1][2][3].Exist` | → 625 | Reverse PP GET |
| 3 | `[2][3][4].Exist` | → 635 | Align Table GET |
| 4 | `[3][4].Exist` | → 645 | Main PP Head 02 GET |
| 5 | `[4][3][2][1].Exist` | → 660 | 전극 5단계 모두 준비완료 |

> **버퍼 배열 의미**:  
> `[0]` 매거진 픽업 → `[1]` PP Head 01 → `[2]` Reverse PP(반전) → `[3]` Align Table(정렬+Vision) → `[4]` PP Head 02

#### 각 경로 종료 조건 (VAC 센서 확인)

| 경로 Step | VAC 전환 조건 | 버퍼 이동 |
|-----------|---------------|-----------|
| 622 | `VAC_1.Detect_On` AND `VAC_2.Detect_On` AND `DoubleSheet_VAC.Detect_Off` | `[0]→[1]` 이동 |
| 628 | `Main_VAC_1.Detect_Off` AND `Main_VAC_2.Detect_Off` AND `Reverse_VAC_1.Detect_On` AND `Reverse_VAC_2.Detect_On` | `[1]→[2]` 이동 |
| 641 | `Reverse_VAC_1.Detect_Off` AND `Reverse_VAC_2.Detect_Off` AND `AlignTable_VAC.Detect_On` AND **`IEC_Timer_AUTO_CATHODE_VISION.Q`** | `[2]→[3]` 이동 |
| 653 | `AlignTable_VAC.Detect_Off` AND `Main_PP_VAC_3.Detect_On` | `[3]→[4]` 이동 |

Step 641에서 `IEC_Timer_AUTO_CATHODE_VISION.Q` 조건 추가 — 비전 검사 타이머 만료 후에만 다음 이동 허용

각 경로 끝 → **619로 루프백** (버퍼 채우기 반복)  
최종 종료: `673 → 699 → ASQ_END.LC_Single_END = TRUE`

---

### RA_Single Step 전환 (Sub1_700) — LC_Single의 Anode 대칭

#### 분기점 Step 719

| 우선순위 | 조건 | 이동 Step |
|---------|------|-----------|
| 1 | `Anode[0][1][2][3].Exist` | → 720 |
| 2 | `[1][2][3].Exist` | → 725 |
| 3 | `[2][3][4].Exist` | → 735 |
| 4 | `[3][4].Exist` | → 745 |
| 5 | `[4][3][2][1].Exist` | → 760 |

Step 741: `IEC_Timer_AUTO_ANODE_VISION.Q` 조건 동일하게 적용  
최종 종료: `773 → 799 → ASQ_END.RA_Single_END = TRUE`

---

### 전환 조건 유형 요약

| 전환 유형 | 실제 확인 조건 |
|-----------|---------------|
| CAM 동기 진입 | `*_InSync` (OR AlwaysTRUE 바이패스) |
| VR 1회전 완료 | `MC_MOVERELATIVE.Done` AND 반대편 `First_Cam_Starting_Position` |
| 축 이동 완료 | `Axis.Position[N]` AND `Axis.Command_bits[N]` 모두 TRUE |
| VAC 전환 완료 | `VIO.Detect_VacuumBlowOn/Off` (실제 진공 센서 감지) |
| 비전 확인 | `IEC_Timer_AUTO_CATHODE/ANODE_VISION.Q` |
| 구역 안전 | `FDB_Zone01.Pause_State` (Single CMD 전 Step 공통) |

---

## 알려진 한계

- **CAM 각도 커브 미확인**: `Cam_STACK_LC_ReverseX_PUT` 등 캠 오브젝트는 TIA Portal Technology Object로 저장되며, 현재 export 툴(`/analyze-plc`, block export)은 프로그램 블록만 대상으로 하여 Technology Object 접근 불가. VR03 몇 도 구간에서 Reverse가 피크 이송을 하는지 확인하려면 TIA Portal UI에서 직접 열거나, 런타임 중 `DB_HMICamValue`(`camSelectionIndex` 설정 후 `readCamTrigger` SET)를 통해 HMI에서 읽어야 함.
- **`STACK_LC_RUN_CAMIN` SET 위치**: Sub1_200은 RESET만 수행. SET 위치(Sub_400/500 또는 별도 OB)는 확인되지 않음.
- **Reverse CAM 이름 불일치**: 코드상 `CAMIN_Cam_STACK_LC_ReverseR_PUT`에 전달되는 캠 오브젝트가 `Cam_STACK_LC_ReverseX_PUT`으로 되어 있음 (R축인데 X 네이밍). 실제 물리 축 방향은 R이 맞으며 코드 의도는 정상이나 명칭 혼동 주의.
- **Sub1_600 Step 627 / 645 이후 일부 Step**: Grep 결과에서 생략(Omitted)된 라인이 있어 세부 조건 일부 미확인.

---

## 약어 정리

| 약어 | 의미 |
|------|------|
| VR | Virtual Reference (가상 기준 축, 0~360° 회전 마스터) |
| CAMIN | MC_CAMIN — 슬레이브 축을 캠 프로파일에 동기화 진입 |
| CAMOUT | MC_CAMOUT — 캠 동기화 해제 |
| PP | Pick & Place (픽앤플레이스 헤드) |
| Reverse PP | 전극을 뒤집어(반전) 다음 스테이지로 넘기는 중간 PP 헤드. Axis11/12(Cathode), Axis26/27(Anode) |
| LC | Leading/Cathode (음극재) |
| RA | Running/Anode (양극재) |
| Dsheet | Double Sheet (이중 시트 검출 유닛) |
| EPC | Edge Position Control (분리막 사행 보정) |
| VAC | Vacuum (진공 흡착) |
| InSync | MC_CAMIN 출력 — 완전 동기화 완료 상태 |
| First_Cam_Starting_Position | 3축 모두 `StatusWord.Synchronizing_POS AND` — Auto Start 게이트 |
| GET | 전극을 받는 방향의 캠 프로파일 |
| PUT | 전극을 전달하는 방향의 캠 프로파일 |
