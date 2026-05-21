# Double Sheet (Cathode / Anode) — Motion Profile

> 작성: 2026-05-20
> 소스: `FB_Camin_Dsheet_L_Cathode`, `FB_Camin_Dsheet_R_Anode`, `FB_Dsheet_*_Sequence_Judgment`, `FC_AXIS_TO_CAM_STATUS`, `DB_GdbCam`
> CAM 데이터: TIA Portal Openness export (2026-05-20) — `exports/PowerCo_Stack_20260430_R150_Backup/cam_exports/Cam_Dsheet_*.xml`
> 관련: [`PP_Motion_Profile.md`](PP_Motion_Profile.md), [`Reverse_PP_Motion_Profile.md`](Reverse_PP_Motion_Profile.md), [`Mandrel_Motion_Profile.md`](Mandrel_Motion_Profile.md), [`../OB_CAM/Double_Sheet/Dsheet_CAM_분석.md`](../OB_CAM/Double_Sheet/Dsheet_CAM_분석.md)

---

## 0) 한 줄 결론

> **Double Sheet = 전용 가상 마스터(VR01/VR02) 1사이클 안에서 R(회전)·X(측면)·Z(수직) 3축이 동시 CAM 동기.**
> 매거진에서 전극을 흡착(Z 다이브)하고, 회전(R turn)으로 Stack PP 픽업 각도를 만들고, 회전 중 극판 끝단이 매거진에 닿지 않도록 X로 측면 보상한다.
> Stack 그룹(PP·Mandrel·Reverse·Swing)이 **VR03 1개**를 공유하는 것과 달리, Dsheet는 **재질별 독립 마스터(Cathode=VR01, Anode=VR02)** 를 쓴다.
> Cathode·Anode 커브는 R·X 동일, Z dwell만 0.90 vs 0.95로 미세하게 다르다.

---

## 1) 하드웨어 구성

| 유닛 | 재질 | Axis (R) | Axis (X) | Axis (Z) | 마스터 |
|---|---|---|---|---|---|
| **Unit03** (Dsheet L_Cathode) | Cathode(음극) | Axis_10 (TB103) | Axis_08 (TB115) | Axis_09 (TB114) | VR01_CathodeDoubleSheetLeadingAxis |
| **Unit04** (Dsheet R_Anode) | Anode(양극) | Axis_25 (TB133) | Axis_23 (TB139) | Axis_24 (TB138) | VR02_AnodeDoubleSheetLeadingAxis |

- **R축**: 회전 — 매거진 적재 각도 → Stack PP가 픽업 가능한 Turn 각도
- **X축**: 수평(측면) — R 회전 중 극판 끝단-매거진 간섭 방지용 **보상 이동** (이송 목적 아님)
- **Z축**: 수직 — 하강(진공 흡착) ↔ 상승

> 물리 역할 상세: [`../OB_CAM/Double_Sheet/Dsheet_CAM_분석.md`](../OB_CAM/Double_Sheet/Dsheet_CAM_분석.md) §1.
> Double Sheet는 매거진의 전극을 흡착해 Turn만 해주는 유닛 — 적층 위치로의 실제 이송은 Stack PP가 담당.

---

## 2) CAM 프로파일 목록

총 6개 TO (재질 2 × 축 3):

| 재질 | R축 TO | X축 TO | Z축 TO |
|---|---|---|---|
| **Cathode** | `Cam_Dsheet_L_CathodeR` | `Cam_Dsheet_L_CathodeX` | `Cam_Dsheet_L_CathodeZ` |
| **Anode** | `Cam_Dsheet_R_AnodeR` | `Cam_Dsheet_R_AnodeX` | `Cam_Dsheet_R_AnodeZ` |

> **실측 결과**: R·X는 Cathode=Anode 완전 동일. Z는 dwell 레벨만 다름(Cathode 0.90 / Anode 0.95). 형상은 R 1종·X 1종·Z 1종으로 수렴.

---

## 3) 실측 CAM 커브 데이터

모든 프로파일: `InterpolationMode="CubicSpline"`, `BoundaryConditions="NoConstraint"`, `StandardContinuity="Acceleration"`
마스터 범위: 0°–360° (VR01/VR02 1사이클), 팔로워 범위: 0~1 (정규화)

> **정규화 규약**: Y=0 = `SlaveOffset`(=IN_Start, 사이클 시작 위치), Y=1 = IN_LONG(목표 위치). 실제 mm/deg와 방향(상/하, CW/CCW)은 `FC_AXIS_TO_CAM_STATUS`가 주입하는 `SlaveScaling` 부호로 결정 → §6.

### 3-1. R축 프로파일 (Cathode = Anode 동일)

매거진 각도(0)에서 Turn(1)까지 회전 후 단계적 복귀.

| VR 구간 | Y (정규화) | 설명 |
|---|---|---|
| 0° → 50° | 0.0 (플랫) | 회전 대기 (Z 흡착 다이브 선행) |
| 50° → 112° | 0.00 → 1.00 (CubicSpline) | **주 회전** — Stack PP 픽업 각도로 Turn |
| 112° → 120° | 1.0 (플랫) | 최대 Turn 도달·유지 |
| 120° → 140° | 1.00 → 0.80 | 1차 복귀 (살짝 되돌림) |
| 140° → 180° | 0.80 (플랫) | **핸드오프 dwell** (PP 픽업 대기 각도 유지) |
| 180° → 220° | 0.80 → 0.075 | 본 복귀 |
| 220° → 360° | 0.075 → 0.0 | 완만한 원점 정렬 |

```
Y(R)
1.00 │            ╭──╮
0.80 │           ╱   ╰─────╮
     │          ╱          ╲
0.075│━━━━━━━━━╯            ╰──────────────
0.00 │                                     ╰
     └─────────┬───┬─┬───┬───┬─────────┬─── VR [°]
              50  112 120 140 180      220        360
```

### 3-2. X축 프로파일 (Cathode = Anode 동일)

회전 구간 동안만 측면으로 빠졌다가 복귀하는 **단일 보상 범프**.

| VR 구간 | Y (정규화) | 설명 |
|---|---|---|
| 0° → 121° | 0.0 (플랫) | 보상 대기 (R Turn 시작 전·중) |
| 121° → 141° | 0.00 → 1.00 | **측면 退避** — 극판 끝단 매거진 간섭 회피 |
| 141° → 220° | 1.0 (플랫) | 退避 위치 유지 (핸드오프 윈도우) |
| 220° → 300° | 1.00 → 0.00 | 측면 복귀 |
| 300° → 360° | 0.0 (플랫) | 원점 유지 |

```
Y(X)
1.00 │              ╭──────────╮
     │             ╱            ╲
0.00 │━━━━━━━━━━━━╯              ╰━━━━━━━━━
     └────────────┬─┬──────────┬───────┬── VR [°]
                121 141       220     300
```

> **타이밍 핵심**: X 退避(121°~)는 R이 최대 Turn에 거의 도달한 직후 시작 → 회전으로 극판이 가장 튀어나온 구간에서만 측면을 비켜준다. 이송이 아니라 **간섭 회피 보상**임이 커브로 확인됨.

### 3-3. Z축 프로파일 (Cathode 0.90 / Anode 0.95)

VR 1사이클 안에서 **완전 하강 후 단계적 상승** — 단일 다이브.

| VR 구간 | Y (정규화) | 설명 |
|---|---|---|
| 0° → 2° | 0.0 | 상단 대기 (즉시 하강 개시) |
| 2° → 120° | 0.00 → 1.00 (CubicSpline) | **주 하강** — 매거진 전극 진공 흡착 위치까지 |
| 120° → 135° | 1.00 → 0.90/0.95 | 살짝 리프트 (흡착 후 들기) |
| 135° → 220° | 0.90/0.95 (플랫) | 매거진 흡착·유지 dwell (Z 최저 부근 = Position_02) |
| 220° → 290° | 0.90/0.95 → 0.65 | 상승 개시 |
| 290° → 358° | 0.65 → 0.00 | 상단 복귀 |
| 358° → 360° | 0.0 | 원점 도달 |

```
Y(Z)  (하강 = +, Cathode 기준 0.90)
1.00 │            ╭╮
0.90 │           ╱ ╰────────╮
0.65 │          ╱           ╰───╮
     │         ╱                 ╲
0.00 │━━━━━━━━╯                   ╰━━
     └────────┬────┬────────┬───┬──┬── VR [°]
              2   120 135   220 290 358
```

> Anode는 dwell 구간(135°–220°)이 0.95로 Cathode(0.90)보다 약간 더 내려간 상태를 유지. 양극재 두께/흡착 조건 차이로 추정(§9 요확인).

---

## 4) R·X·Z 복합 동작 — 궤적 해석

세 축은 동일 VR을 마스터로 동시 동기되며, 3축 모두 InSync여야 유효(§7).

```
VR 위상   0°       50°   112°120°  141°       220°    290°  358°
─────────────────────────────────────────────────────────────────
 Z(수직) ─하강 개시(2°)──▶ 1.0 ─lift─ 0.9 ────dwell──── ▲상승──── 0
 R(회전) ──대기──▶ Turn ▶ 1.0 ─────── 0.8 dwell ─── 본복귀 ──── 0
 X(측면) ──────대기────────────── 退避1.0 ── dwell ── 복귀 ──── 0
─────────────────────────────────────────────────────────────────
                          ▲                ▲
                  Z최저=매거진 흡착   turn/退避 유지 (cam 동작 계속 중)
```

- **0°–120°: 흡착·회전 동시 진행** — Z가 먼저(2°) 내려가 매거진 전극을 흡착하고, R이 50°부터 회전 시작. 112°~120°에서 Z=최저(Position_02)·R=최대 Turn 동시 도달.
- **120°–141°: 보상 전환** — Z·R이 살짝 풀리는 사이 X가 측면으로 退避(극판이 가장 튀어나온 시점 간섭 회피).
- **141°–220°: 프레젠테이션·유지** — R(0.8)·X(1.0)·Z(0.9) dwell. ⚠️ 이 구간은 PP 픽업 지점이 **아니다** — 매거진 흡착(`VacuumBlowOn`)은 Sub-200(cam) 중 실행되고, PP 핸드오프(`VacuumBlowOff`)는 **cam 1주기(360°) 종료 후 Sub-300에서 발행**된다. 즉 PP 픽업 타이밍은 특정 cam 각이 아니라 **후속 GRAPH 스텝**에 의해 결정.
- **220°–360°: 복귀** — X→R→Z 순으로 Position_03(Y=0) 복귀.

> **확인된 관찰**: R·X·Z 모두 360°에서 Y=0(=Position_03)로 복귀 → **한 cam 사이클 내 순(net) 재배향은 없다**(R도 시작 방향으로 환원). 따라서 OB_CAM의 "Turn 유닛" 서술과의 정합(픽업이 dwell인지 사이클 종료 후 Sub-300인지, R의 net turn 유무)은 Sub-200/300 GRAPH 스텝 게이팅 분석으로 추가 확정 필요(§9).

---

## 5) 동작 타임라인 — Cathode 기준

VR01이 0°→360° 회전(= 1 ActionTime)하는 동안 3축 동시:

```
VR 각도     Axis10 (R)              Axis08 (X)              Axis09 (Z)
──────────────────────────────────────────────────────────────────────────────
0°~ 2°    대기                    대기                    하강 개시
2°~ 50°   대기                    대기                    하강 중
50°~112°  Turn 회전 ↗             대기                    하강 → 최저(120°)
112°~120° 최대 Turn 유지          대기                    최저 도달 → ▼ 흡착
120°~141° 1차 복귀(→0.8)          ▶ 측면 退避(→1.0)       살짝 리프트(→0.9)
141°~180° 0.8 dwell               1.0 dwell               0.9 dwell (흡착 유지)
180°~220° 본 복귀(→0.075)         1.0 dwell               0.9 dwell (흡착 유지)
220°~300° 원점 정렬               측면 복귀(→0)           상승(→0.65)
300°~360° 0 정렬                  0 유지                  상단 복귀(→0)
──────────────────────────────────────────────────────────────────────────────
```

Anode(VR02 / Axis25·23·24)는 동일 타임라인, Z dwell만 0.95.

> VR 속도: `VR01_Velocity[°/s] = (1.0 / CathodeDoubleSheetActionTime) × 360.0` (출처 `FB_Dsheet_L_Cathode_Sequence_Judgment`).
> VR은 HOME 후 MoveRelative 360° → 슬레이브 3축이 CAM 1주기 완주. ActionTime은 레시피 공급(공정 택타임).

---

## 6) SlaveOffset / SlaveScaling — 동적 주입

커브(0~1 정규화)는 고정이지만, 실제 물리 위치는 매 사이클 동적으로 결정된다.

| 파라미터 | 값 | 역할 |
|---|---|---|
| `MasterOffset` / `MasterScaling` | 1.0 (고정) | VR 0~360° 그대로 사용 |
| `SlaveOffset` | `= IN_Start = Position_03` | Y=0 기준점 = 사이클 시작/종료 위치 → 점프 없는 진입 |
| `SlaveScaling` | `= (IN_Start − IN_LONG)×(−1) = Position_02 − Position_03` | 정규화 0~1 → 실제 이동량(mm/deg)·방향(부호=Position_02−Position_03) |
| MasterSyncPosition | 0.01° | 마스터 0° 직후 동기화 |
| SyncDirection | 3 (양방향) / ApplicationMode 0 (절대) / SyncProfileReference 2 | |

```
FC_AXIS_TO_CAM_STATUS
  ├ SlaveOffset  = IN_Start                    → 현재 위치에서 충격 없는 CAM 진입
  └ SlaveScaling = (IN_Start − IN_LONG)×(−1)   → 총 이동거리·방향
        ↓ DB_GdbCam.Dsheet_*.Cam_*.CamData.{SlaveOffset, SlaveScaling}
        ↓ FB_Camin_Dsheet_* (Network 5/7) → CamIn.{SlaveOffset, SlaveScaling}
```

> **IN_Start/IN_LONG 출처 확인 완료** (`FB_AXIS_TO_CAM_STATUS`가 `FC_AXIS_TO_CAM_STATUS` 호출):
> - Cathode(확인): `IN_Start = DB_StackRecipe.Servo[N].Position_03`, `IN_LONG = …Position_02` (N = 10·8·9 → R·X·Z), `IN_END = Position_03`(미사용), `Pos_range = 0.1`
> - Anode: 동일 구조 `Servo[25·23·24]`의 Position_03/02 (대칭, 미검증)
> - ⚠️ 호출 네트워크는 `.md` 다이제스트에선 누락됨 → `FB_AXIS_TO_CAM_STATUS.xml` 정본 참조 ([[project_md_digest_strips_functions]])
> Winding CAM의 **고정 ScalingFactor**와 달리, Position_02/03은 레시피(`DB_StackRecipe`)로 런타임 주입되는 **완전 동적** 구조 → 실제 mm/deg 수치는 코드 상수가 아니라 레시피 데이터(정적 export로는 확정 불가).

---

## 7) 교번 CamOut 핸드오프 (Cathode↔Anode)

`FB_Camin_Dsheet_L_Cathode`의 **CamOut이 자기(Cathode) 축이 아닌 Anode 축(Axis25/23/24)을 해제**한다. 교번 공정에서 이전 사이클의 반대재질 CAM을 즉시 정리해 축 충돌 없이 전환하기 위한 파이프라인 설계.

```
② Cathode CAMIN 트리거 → L_Cathode FB 실행
     ├ Cathode 축(Axis10/08/09) CamIn 시작
     └ Anode  축(Axis25/23/24) CamOut 동시 발행 ← 이전 사이클 Anode CAM 해제
```

- CamOut 완료를 기다리지 않고 CamIn과 동시 발행 → 전환 지연 최소화.
- 상세·다이어그램: [`../OB_CAM/Double_Sheet/Dsheet_CAM_분석.md`](../OB_CAM/Double_Sheet/Dsheet_CAM_분석.md) §7, 설계 의도는 메모리 `project_cam_handoff_pattern` 참조.
- 3축 집계: `First_Cam_Starting_Position`(N9, 3축 Synchronizing_POS AND), `ERROR`(N10, OR), `InSync`(N11, AND).

---

## 8) 기존 4개 프로파일과 비교

| 항목 | **DSheet** | PP (Main P&P) | Reverse P&P | Mandrel | Swing Roller |
|---|---|---|---|---|---|
| 마스터축 | **VR01 / VR02 (재질별)** | VR03 | VR03 | VR03 | VR03 |
| 동기 축 수 | **3 (R·X·Z)** | 2 (X·Z) | 2 (R·Z) | 2 (Y·Z) | 2 (R·Z)+GEARIN |
| 다이브 | Z 1회 + R Turn 1회 | Z 1회 (180° 최저) | Z 얕은 다이브 2분할 | — | — |
| GET/PUT 구분 | 없음 (1사이클 흡착+핸드오프) | SlaveOffset/Scaling | 프로파일 상이 | GET/PUT 별도 TO | LC/RA 별도 |
| 중간 dwell | **141°–220° (R·X·Z 동시 정지, 흡착 유지)** | 180° 1점 | — | — | — |
| PP 핸드오프 | cam 종료 후 **Sub-300** (VacuumBlowOff) | cam 내 180° | — | — | — |
| Scaling 성격 | 동적(IN_Start/LONG) | 동적 | 동적 | 동적 | 동적 + GEARIN |
| 특이점 | 재질별 마스터 + 교번 CamOut + X 보상범프 | 16 TO 동일 커브 | R/Z 비대칭 | Y+Z 2축 | 1번 CAM·2번 GEARIN |

> Dsheet만 **전용 마스터(VR01/VR02)** 와 **3축 동시(R·X·Z)**를 갖는다 — Stack 그룹(VR03 공유, 2축)과 구조적으로 구분됨. 단 PP 핸드오프는 cam 각이 아니라 cam 종료 후 Sub-300 시퀀스에서 발행된다.

---

## 9) 미확인 항목

| 항목 | 상태 |
|---|---|
| 6개 TO 커브 수치 | ✅ **확인 완료** — R·X 동일, Z dwell만 0.90/0.95 |
| Cathode vs Anode 차이 | ✅ **확인 완료** — R·X 동일, Z dwell 0.90 vs 0.95 |
| R/X/Z 위상 협조 (흡착·Turn·보상·핸드오프) | ✅ **확인 완료** — 커브 위상으로 도출 |
| SlaveOffset/SlaveScaling 출처 | ✅ **확인 완료** — IN_Start=Position_03, IN_LONG=Position_02 (`FB_AXIS_TO_CAM_STATUS.xml`), Y0=Pos03·Y1=Pos02 |
| PP 픽업/핸드오프 위치 | ✅ **확인 완료** — 매거진 흡착=Sub-200 `VacuumBlowOn`, PP 핸드오프=cam 종료 후 Sub-300 `VacuumBlowOff` (dwell 아님) |
| Step 350 매거진 리프트 JOG 보정 | ✅ **Dead Code 확정** — Wire UId62: `NOT(AlwaysTRUE)` Negated 접점(UId43) → 분기 영구 FALSE |
| net 재배향 유무 | ✅ **확인 완료** — R·X·Z 모두 360°에서 Y=0 복귀 → 1 cam 사이클 net turn 없음 |
| Position_02/03 실제 mm/deg 값 | ❌ `DB_StackRecipe.Servo[8/9/10·23/24/25]` 런타임 레시피값 — 정적 export로 확정 불가 |
| Position_02 vs 03 절대 방향 (Z 상/하 등) | ❌ 축 극성(TO config) + 레시피값 필요 — Y1=Position_02가 매거진(하강)이라는 건 정황상 강한 추정 |
| Z dwell 0.90 vs 0.95 차이 **사유** | ❌ 값은 CAM 고정값으로 확정, 설계 사유(양극 두께/흡착)는 코드 외 정보 |
| OB_CAM "Turn 유닛" 정합 (픽업이 dwell vs Sub-300, R net turn) | ⚠️ Sub-200/300 GRAPH 스텝 게이팅 분석으로 추가 확정 가능 |
