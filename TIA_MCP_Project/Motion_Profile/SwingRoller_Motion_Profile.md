# Stack Table Swing Roller — Motion Profile

> 작성: 2026-05-19  
> 소스: `FB_Camin_STACK_LC_RUN`, `FB_Camin_STACK_RA_RUN`, `FB_Camin_Single_LC_RUN`, `FB_GEARIN`, `FC_RecipeMatching`, `DB_GdbCam`  
> CAM 데이터: TIA Portal Openness export (2026-05-19) — `exports/.../cam_exports/Cam_STACK_Swing*.xml`  
> 관련: [`VR축_0to360_전체동작.md`](VR축_0to360_전체동작.md), [`PowerCo_Stack_CAM_Angle_Sequence.md`](PowerCo_Stack_CAM_Angle_Sequence.md)

---

## 0) 한 줄 결론

> **Swing Roller = VR03 슬레이브(CAMIN) + GEARIN 이중 제어.**  
> 1번 롤러(Axis37/39)가 캠 프로파일을 직접 추종하고, 2번 롤러(Axis38/40)는 GEARIN으로 1번에 기어 동기된다.  
> 단, `Single_LC/RA_RUN` Phase에서는 2번도 독립 CAMIN Execute가 활성화된다.

---

## 1) 하드웨어 구성

| 축 | Axis번호 | TB 포트 | 방향 | 역할 |
|---|---|---|---|---|
| Swing Roller Z01 | Axis_37 | TB126 | Z | 1번 롤러 승강 |
| Swing Roller Z02 | Axis_38 | TB127 | Z | 2번 롤러 승강 |
| Swing Roller R01 | Axis_39 | TB128 | R | 1번 롤러 회전 |
| Swing Roller R02 | Axis_40 | TB129 | R | 2번 롤러 회전 |

- Z축: 롤러를 위아래로 올리고 내림 → 분리막 들어올리기 / 전극 덮기
- R축: 롤러를 회전 → 분리막을 전극 위로 밀어 씌우기

---

## 2) 제어 구조 개요

```
                         VR03_StackLeadingAxis (0°→360°, 가상 마스터)
                                    │  CAMIN
              ┌─────────────────────┼──────────────────────┐
              ▼                     ▼                      ▼
       Swing1R (Axis39)       Swing1Z (Axis37)     (Swing2 — GEARIN 또는 Single에서 CAMIN)
              │                     │
         GEARIN                GEARIN
              │                     │
       Swing2R (Axis40)       Swing2Z (Axis38)
```

---

## 3) CAM 프로파일 목록

Phase마다 별도 CAM 프로파일이 사용됩니다.

| Phase | R01 (Axis39) | Z01 (Axis37) | R02 (Axis40) | Z02 (Axis38) |
|---|---|---|---|---|
| **LC_RUN** | `Cam_STACK_Swing1R_LC` | `Cam_STACK_Swing1Z_LC` | `Cam_STACK_Swing2R_LC` | `Cam_STACK_Swing2Z_LC` |
| **RA_RUN** | `Cam_STACK_Swing1R_RA` | `Cam_STACK_Swing1Z_RA` | `Cam_STACK_Swing2R_RA` | `Cam_STACK_Swing2Z_RA` |
| **Single_LC_RUN** | `Cam_STACK_Swing1R_LC` | `Cam_STACK_Swing1Z_LC` | `Cam_STACK_Swing2R_LC` | `Cam_STACK_Swing2Z_LC` |
| **Single_RA_RUN** | `Cam_STACK_Swing1R_RA` | `Cam_STACK_Swing1Z_RA` | `Cam_STACK_Swing2R_RA` | `Cam_STACK_Swing2Z_RA` |

> **실측 결과 (Openness export)**: LC와 RA 프로파일이 동일한 커브 데이터를 가짐 — Swing1R/RA, Swing2R/RA 동일; Swing1Z/RA, Swing2Z/RA 동일.  
> LC·RA 별도 TO 객체로 존재하지만 현재 동일한 포인트 데이터가 입력되어 있음. Swing1Z와 Swing2Z는 시작/끝 경계 0.1° 플랫 유무만 다름.

---

## 4) CAMIN 파라미터 상세

### 4-1. FB_Camin_STACK_LC_RUN / FB_Camin_STACK_RA_RUN (주 스태킹 Phase)

| 파라미터 | Swing1R | Swing1Z | Swing2R | Swing2Z |
|---|---|---|---|---|
| Master | VR03_StackLeadingAxis | VR03_StackLeadingAxis | VR03_StackLeadingAxis | VR03_StackLeadingAxis |
| Slave | Axis39 (R01) | Axis37 (Z01) | Axis40 (R02) | Axis38 (Z02) |
| CamTable | Cam_STACK_Swing1R_LC/RA | Cam_STACK_Swing1Z_LC/RA | Cam_STACK_Swing2R_LC/RA | Cam_STACK_Swing2Z_LC/RA |
| Execute | `STACK_LC/RA_RUN_CAMIN` ✓ | `STACK_LC/RA_RUN_CAMIN` ✓ | ⚠️ **주석 처리** | ⚠️ **주석 처리** |
| MasterOffset | 1.0 (고정) | 1.0 (고정) | 1.0 (고정) | 1.0 (고정) |
| SlaveOffset | `DB_GdbCam...CamData.SlaveOffset` | `DB_GdbCam...CamData.SlaveOffset` | `DB_GdbCam...CamData.SlaveOffset` | `DB_GdbCam...CamData.SlaveOffset` |
| MasterScaling | 1.0 (고정) | 1.0 (고정) | 1.0 (고정) | 1.0 (고정) |
| SlaveScaling | `DB_GdbCam...CamData.SlaveScaling` | `DB_GdbCam...CamData.SlaveScaling` | `DB_GdbCam...CamData.SlaveScaling` | `DB_GdbCam...CamData.SlaveScaling` |
| VelocityOffset | 0.01 | 0.01 | 0.01 | 0.01 |
| SyncMode | 3 | 3 | 3 | 3 |
| StartMode | 0 | 0 | 0 | 0 |
| CamLeadIn | 2 | 2 | 2 | 2 |

### 4-2. FB_Camin_Single_LC_RUN / FB_Camin_Single_RA_RUN (버퍼 채우기 Phase)

| 파라미터 | Swing1R | Swing1Z | Swing2R | Swing2Z |
|---|---|---|---|---|
| Execute | `Single_LC/RA_RUN_CAMIN` ✓ | `Single_LC/RA_RUN_CAMIN` ✓ | `Single_LC/RA_RUN_CAMIN` ✓ | `Single_LC/RA_RUN_CAMIN` ✓ |
| VelocityOffset | 0.01 | 0.01 | 0.01 | 0.01 |
| SyncMode | 3 | 2 | 2 | 2 |
| StartMode | 1 | 3 | 3 | 3 |
| CamLeadIn | — (기본값) | 1 | 1 | 1 |

> Single Phase에서는 Swing2 Execute도 활성화됨 — 2번 롤러가 CAMIN으로 독립 제어됨.  
> SyncMode/StartMode가 STACK Phase와 다름 — Single Phase의 마스터 속도 프로파일이 다르기 때문으로 추정.

---

## 5) ⚠️ CAMIN Execute 주석 처리 분석

### 현상

`FB_Camin_STACK_LC_RUN` Network 3 (Execute 설정):
```scl
// 활성
DB_GdbCam.STACK_TABLE.Cam_STACK_Swing1R_LC.CamIn.Execute := STACK_LC_RUN_CAMIN;
DB_GdbCam.STACK_TABLE.Cam_STACK_Swing1Z_LC.CamIn.Execute := STACK_LC_RUN_CAMIN;

// 비활성 (주석)
//"DB_GdbCam".STACK_TABLE.Cam_STACK_Swing2R_LC.CamIn.Execute := "DB_Global_Cam_Control".STACK_LC_RUN_CAMIN;
//"DB_GdbCam".STACK_TABLE.Cam_STACK_Swing2Z_LC.CamIn.Execute := "DB_Global_Cam_Control".STACK_LC_RUN_CAMIN;
```

`STACK_LC_RUN_InSync` (Phase 전환 게이트):
```scl
DB_Global_Cam_Control.STACK_LC_RUN_InSync :=
  ...
  Cam_STACK_Swing1R_LC.CamIn.InSync AND   // 포함
  Cam_STACK_Swing1Z_LC.CamIn.InSync AND   // 포함
  //Cam_STACK_Swing2R_LC.CamIn.InSync AND  // 주석 — 전환 조건 미포함
  //Cam_STACK_Swing2Z_LC.CamIn.InSync AND  // 주석 — 전환 조건 미포함
  ...
```

RA_RUN도 동일 패턴.

### 영향 분석

| 항목 | Swing Roller 1번 | Swing Roller 2번 (STACK Phase) |
|---|---|---|
| CAMIN Execute | 활성 → VR03 캠 직접 추종 | 비활성 → 캠 추종 없음 |
| InSync 포함 여부 | Phase 전환 게이트에 포함 | 미포함 |
| CAMOUT 등록 | 됨 | 됨 (CAMOUT은 활성) |
| 실제 움직임 | CAMIN 캠 프로파일 | **GEARIN으로 1번 축을 따라 동기** |

### 결론

> 2번 롤러가 STACK Phase에서 움직이지 않는 것이 아니라, **GEARIN을 통해 1번 롤러와 기어 연결된 채로 함께 움직이는 설계**.  
> 개별 캠 추종 없이 1번과 동일한 프로파일로 움직이므로 Execute를 별도로 올릴 필요가 없음.  
> `Single_LC/RA_RUN`에서는 마스터 속도 패턴이 달라 2번도 독립 CAMIN이 필요한 것으로 추정.

---

## 6) GEARIN 구조

`FB_GEARIN`에서 MC_GEARIN으로 쌍을 연결합니다.

| Gearin 신호 | 마스터 축 | 슬레이브 축 | 활성 조건 |
|---|---|---|---|
| `Btn_Gearin_StackTableSwingRoller_Z` | Axis37 Z01 | Axis38 Z02 | Z01/Z02 모두 Ready |
| `Btn_Gearin_StackTableSwingRoller_R` | Axis39 R01 | Axis40 R02 | R01/R02 모두 Ready |

- `DB_Global_Servo.Gearin_StackTableSwingRoller_Z/R` 플래그로 런타임 활성화 상태 확인 가능
- Home도 별도 인스턴스 존재: `MC_HOME_Instance_SwingRollerZ/R`

---

## 7) 동작 타임라인 (VR03 각도 기준 — **실측 CAM 데이터**)

CAM export로 확인된 실제 포인트:

### 7-1. R축 (Swing1R / Swing2R — 4개 프로파일 동일)

| VR03 구간 | Y (정규화 위치) | 물리 동작 |
|---|---|---|
| 0° → 36° | 0.0 (플랫) | 홈 자세 유지 (회전 없음) |
| 36° → 324° | 0.0 → 1.0 (CubicSpline) | 스윕 회전 — 분리막 밀어 씌우기 |
| 324° → 360° | 1.0 (플랫) | 완전 전개 자세 유지 |
| 360° = 0° (다음 사이클) | 1.0 → 0.0 (CAMOUT 후 복귀) | STACK Phase 동안 홈으로 복귀 |

```
R 위치
1.0  │              ╭──────────────────╮
     │             ╱                   ║
     │            ╱                    ║
0.0  │────────────                     ════
     └─────┬──────────────────────┬────┬─── VR03 [°]
           36                   324  360
```

### 7-2. Z축 (Swing1Z / Swing2Z)

| VR03 구간 | Y (정규화 위치) | 물리 동작 | Swing1Z vs Swing2Z |
|---|---|---|---|
| 0° → ~0.1° | 0.0 (플랫) | 상단 유지 | Swing1Z만 0.1° 플랫, Swing2Z는 0°부터 즉시 하강 |
| 0°/0.1° → 36° | 0.0 → 0.5 (CubicSpline) | 중간 지점까지 하강 | 동일 |
| 36° → 72° | 0.5 → 1.0 (CubicSpline) | 완전 하강 (롤러 압착) | 동일 |
| 72° → 288° | 1.0 (플랫) | 하단 압착 유지 (216° 구간) | 동일 |
| 288° → 324° | 1.0 → 0.5 (CubicSpline) | 중간 지점까지 상승 | 동일 |
| 324° → ~360° | 0.5 → 0.0 (CubicSpline) | 완전 상승 복귀 | Swing1Z: 359.9°에 도달, Swing2Z: 360° 정확히 도달 |

```
Z 위치 (하강 방향이 +)
0.0  │━━━━━━━━╮                              ╭━━━
     │         ╲                            ╱
0.5  │          ╲                          ╱
     │           ╲                        ╱
1.0  │            ╰────────────────────────╯
     └─────┬────┬─┬────────────────────┬───┬── VR03 [°]
           0   36 72                  288 324/360
```

### 7-3. R과 Z의 시간적 관계

```
VR03 각도      Z (승강, 하강=아래)              R (회전, 1.0=완전 전개)
──────────────────────────────────────────────────────────────────
 0° ~  36°   | ▼ 하강 시작 (0→0.5)            | 홈 유지 (0.0)
36° ~  72°   | ▼ 하강 지속 (0.5→1.0)           | ▶ 회전 시작 (0.0→~0.08)
72° ~ 288°   | 하단 압착 유지 (1.0)             | ▶ 회전 지속 (0.08→0.96) ← 주 작업 구간
288° ~ 324°  | ▲ 상승 시작 (1.0→0.5)           | ▶ 회전 마무리 (0.96→1.0)
324° ~ 360°  | ▲ 상승 지속 (0.5→0.0)           | 완전 전개 유지 (1.0)
STACK Phase  | 홈 복귀 (CAMOUT 후)              | 홈 복귀 (CAMOUT 후)
──────────────────────────────────────────────────────────────────
```

> **설계 의도**: Z가 먼저 내려가 분리막을 고정·압착한 뒤 R이 스윕 → Z를 누른 채로 R이 분리막을 밀어 전극을 완전히 덮음 → Z가 올라오는 동안 R은 완전 전개 자세 유지 → 둘 다 STACK Phase에서 홈 복귀.

---

## 8) 레시피 파라미터 구조

각 축마다 `DB_StackRecipe.Servo[N]`에 레시피가 저장되며, `FC_RecipeMatching`이 `DB_RecipeCfg.setpoints_REAL[index]`에서 읽어 씁니다.

| 축 | Axis | setpoints_REAL 인덱스 범위 | 항목 |
|---|---|---|---|
| Swing Roller Z01 | 37 | [1080] ~ [1108] | Position01-10, Velocity01-10, RampUpTime, RampDownTime, Jerk, JOG×4, HomingRetryLimPos, HomeOffset |
| Swing Roller Z02 | 38 | [1110] ~ [1138] | 동일 구조 |
| Swing Roller R01 | 39 | [1140] ~ [1168] | 동일 구조 |
| Swing Roller R02 | 40 | [1170] ~ [1198] | 동일 구조 |

> 각 축 10개 Position + 10개 Velocity 슬롯은 Sequential 이동(JR/Manual/Initial)에서 사용되며, CAMIN 동작 중에는 CAM Technology Object 커브가 우선합니다.

---

## 9) CAMOUT 설정

CAMOUT은 LC/RA 모두 동일하게 4축 전부 등록되어 있습니다.

| CAMOUT 인스턴스 | 축 | Execute 소스 | DecelPhase |
|---|---|---|---|
| `CAMOUT_Cam_STACK_Swing1R_LC` | Axis39 R01 | `STACK_LC/RA_RUN_CAMOUT` | 5 |
| `CAMOUT_Cam_STACK_Swing1Z_LC` | Axis37 Z01 | `STACK_LC/RA_RUN_CAMOUT` | 5 |
| `CAMOUT_Cam_STACK_Swing2R_LC` | Axis40 R02 | `STACK_LC/RA_RUN_CAMOUT` | 5 |
| `CAMOUT_Cam_STACK_Swing2Z_LC` | Axis38 Z02 | `STACK_LC/RA_RUN_CAMOUT` | 5 |

> Swing2의 CAMIN Execute는 주석이지만 CAMOUT은 살아 있음 — Phase 종료 시 정상적으로 동기 해제됨.

---

## 10) Phase별 Swing Roller 상태 요약

| Phase | Swing1 (Axis37/39) | Swing2 (Axis38/40) | 비고 |
|---|---|---|---|
| **LC_RUN** | CAMIN 활성 (`Cam_STACK_Swing1X_LC`) | CAMIN Execute ✗, GEARIN으로 1번 추종 | InSync 조건에 Swing1만 포함 |
| **LC_STACK** | CAM 비활성 | CAM 비활성 | VR04 Phase — Swing Roller 정지 |
| **RA_RUN** | CAMIN 활성 (`Cam_STACK_Swing1X_RA`) | CAMIN Execute ✗, GEARIN으로 1번 추종 | InSync 조건에 Swing1만 포함 |
| **RA_STACK** | CAM 비활성 | CAM 비활성 | VR04 Phase — Swing Roller 정지 |
| **Single_LC_RUN** | CAMIN 활성 (`Cam_STACK_Swing1X_LC`) | CAMIN 활성 (`Cam_STACK_Swing2X_LC`) | 4축 모두 InSync 조건 포함 |
| **Single_RA_RUN** | CAMIN 활성 (`Cam_STACK_Swing1X_RA`) | CAMIN 활성 (`Cam_STACK_Swing2X_RA`) | 4축 모두 InSync 조건 포함 |

---

## 11) 미확인 항목

| 항목 | 상태 |
|---|---|
| CAM 커브 수치 (VR03 각도별 Z/R 위치) | ✅ **확인 완료** — Openness export로 실측 (§7 참조) |
| LC_RUN과 RA_RUN CAM 프로파일 실제 차이 | ✅ **확인 완료** — 동일한 커브 데이터 (LC=RA) |
| Swing1Z와 Swing2Z 차이 | ✅ **확인 완료** — 0°/360° 경계 0.1° 플랫 유무만 다름 |
| Swing2 CAMIN Execute 주석 처리 의도 | 추정(GEARIN 대체)이며 코드 주석/커밋 메시지 근거 없음 |
| Single Phase의 SyncMode/StartMode 차이 이유 | 미확인 — 마스터 속도 패턴 차이로 추정 |
| 정규화 Y=0~1이 실제 물리 단위(mm/deg)로 얼마인지 | 미확인 — `SlaveScaling`, `SlaveOffset` DB 값 및 레시피 setpoint 확인 필요 |
