# Stack Table Reverse P&P — Motion Profile

> 작성: 2026-05-19  
> 수정: 2026-05-21 — §5-1 PUT R(X)축 타임라인 교정(X_PUT 커브와 불일치 수정), §6 RA_RUN 설명·미확인 항목(§9) 재검증, 관련 링크 경로 수정  
> 수정: 2026-05-26 — §9 GET 완료 VAC 확인 항목 ✅로 교정, §10 진공 핸드오프 4-신호 조건 신규 추가 (FB_Auto_Sub1_Stack_600/700 step 628/728/641/741 검증)  
> 소스: `FB_Camin_STACK_LC_RUN`, `FB_Camin_STACK_RA_RUN`, `DB_GdbCam`, `DB_Global_Cam_Control`  
> CAM 데이터: TIA Portal Openness export (2026-05-19) — `exports/.../cam_exports/Cam_STACK_*Reverse*.xml`  
> 관련: [`VR축_0to360_전체동작.md`](../OB_CAM/Stack_Cam_Angle/VR축_0to360_전체동작.md), [`SwingRoller_Motion_Profile.md`](SwingRoller_Motion_Profile.md)

---

## 0) 한 줄 결론

> **Reverse P&P = Cathode/Anode 두 헤드가 VR03 한 사이클 내에서 교번 동작.**  
> LC_RUN에선 Cathode가 PUT·Anode가 GET, RA_RUN에선 반대 — 한 헤드가 놓을 때 다른 헤드는 집는다.  
> GET/PUT 각각 별도 CAMIN, Z/R 각 축마다 별도 CAM 프로파일 (총 8개 TO).

---

## 1) 하드웨어 구성

| 축 | Axis번호 | TB 포트 | 방향 | 역할 |
|---|---|---|---|---|
| Cathode Reverse Z | Axis_11 | TB116 | Z | Cathode P&P 수직 이동 |
| Cathode Reverse R | Axis_12 | TB117 | R | Cathode P&P 수평/회전 이동 |
| Anode Reverse Z | Axis_26 | TB140 | Z | Anode P&P 수직 이동 |
| Anode Reverse R | Axis_27 | TB141 | R | Anode P&P 수평/회전 이동 |

- **Z축**: 전극을 위아래로 올리고 내림 → 픽업(GET) 시 하강, 플레이스(PUT) 시 하강
- **R축**: 수평 이동 (DB_GdbCam에서 "R", TO 이름에서 "X" — 동일 축, 명칭 불일치)

> **명칭 주의**: 축 하드웨어 이름은 "R" (Axis12_CathodeReverseP&PElectrodeR_TB117), TIA Technology Object 이름은 "X" (Cam_STACK_LC_ReverseX_GET) — 같은 물리 축의 이중 명칭.  
> 이 문서에서는 **R축** 으로 통일 표기.

---

## 2) 동작 구조 개요

```
               VR03_StackLeadingAxis (0°→360°, 가상 마스터)
                              │
         LC_RUN Phase         │          RA_RUN Phase
   ┌──────────────────┐       │    ┌──────────────────┐
   │ Cathode P&P PUT  │  CAMIN│    │ Anode P&P PUT    │  CAMIN
   │  Axis11 (Z) ←───┤       │────┤  Axis26 (Z) ←───│
   │  Axis12 (R) ←───┤       │    │  Axis27 (R) ←───│
   │                  │       │    │                  │
   │ Anode P&P GET    │  CAMIN│    │ Cathode P&P GET  │  CAMIN
   │  Axis26 (Z) ←───┤       │    │  Axis11 (Z) ←───│
   │  Axis27 (R) ←───┤       │    │  Axis12 (R) ←───│
   └──────────────────┘       │    └──────────────────┘
```

한 VR03 사이클 안에서 두 P&P 헤드가 동시에 서로 다른 동작(GET/PUT)을 수행한다.

---

## 3) CAM 프로파일 목록

| Phase | 재질 | 동작 | Z축 CAM TO | R축 CAM TO |
|---|---|---|---|---|
| **LC_RUN** | Cathode | **PUT** | `Cam_STACK_LC_ReverseZ_PUT` | `Cam_STACK_LC_ReverseX_PUT` |
| **LC_RUN** | Anode | **GET** | `Cam_STACK_RA_ReverseZ_GET` | `Cam_STACK_RA_ReverseX_GET` |
| **RA_RUN** | Anode | **PUT** | `Cam_STACK_RA_ReverseZ_PUT` | `Cam_STACK_RA_ReverseX_PUT` |
| **RA_RUN** | Cathode | **GET** | `Cam_STACK_LC_ReverseZ_GET` | `Cam_STACK_LC_ReverseX_GET` |

> **실측 결과 (Openness export)**: LC와 RA 동명 프로파일이 **완전히 동일한 커브 데이터**.  
> TO가 8개지만 실질적으로 Z_GET / Z_PUT / X_GET / X_PUT 4종 커브만 존재.

---

## 4) 실측 CAM 커브 데이터

모든 프로파일: `InterpolationMode="CubicSpline"`, `BoundaryConditions="NoConstraint"`  
마스터 범위: 0°–360° (VR03), 팔로워 범위: -1~1 (정규화)

### 4-1. Z축 GET 프로파일 (`*_ReverseZ_GET`, LC=RA 동일)

전극을 **빠르게** 픽업 위치로 내리고, 사이클 끝까지 그 위치 유지.

| VR03 구간 | Y (정규화 위치) | 설명 |
|---|---|---|
| 0° → 6° | 0.0 → 0.1 | 하강 개시 (완만) |
| 6° → 16° | 0.1 → 0.9 | 주 하강 구간 |
| 16° → 22° | 0.9 → 1.0 | 하강 마무리 (픽업 위치) |
| 22° → 360° | 1.0 (플랫) | 픽업 위치 유지 (carry) |

```
Z (하강=+)
1.0 │    ╭──────────────────────────────────
    │   ╱
0.0 │───╯
    └──┬──┬──────────────────────────────── VR03 [°]
       6  22
```

### 4-2. Z축 PUT 프로파일 (`*_ReverseZ_PUT`, LC=RA 동일)

사이클 전반부 carry 후, **3/4 지점**에서 플레이스 위치로 내림.

| VR03 구간 | Y (정규화 위치) | 설명 |
|---|---|---|
| 0° → 252° | 0.0 (플랫) | carry 위치 유지 (위로 들린 상태) |
| 252° → 258° | 0.0 → 0.1 | 하강 개시 |
| 258° → 268° | 0.1 → 0.9 | 주 하강 구간 |
| 268° → 274° | 0.9 → 1.0 | 하강 마무리 (플레이스 위치) |
| 274° → 360° | 1.0 (플랫) | 플레이스 위치 유지 |

```
Z (하강=+)
1.0 │                                    ╭───
    │                                   ╱
0.0 │━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯
    └────────────────────────────┬──┬───┬─── VR03 [°]
                                252 268 274
```

### 4-3. R(X)축 GET 프로파일 (`*_ReverseX_GET`, LC=RA 동일)

사이클 전반부(0°-180°)에 걸쳐 픽업 위치로 이동, 이후 유지.

| VR03 구간 | Y (정규화 위치) | 설명 |
|---|---|---|
| 0° → 20° | 0.0 (플랫) | 시작 위치 대기 |
| 20° → 180° | 0.0 → 1.0 (CubicSpline) | 픽업 위치로 이동 |
| 180° → 360° | 1.0 (플랫) | 픽업 위치 유지 |

```
R 위치
1.0 │              ╭──────────────────────
    │             ╱
    │            ╱
0.0 │━━━━━━━━━━━╯
    └───────────┬──────────────────────── VR03 [°]
                20                       180
```

### 4-4. R(X)축 PUT 프로파일 (`*_ReverseX_PUT`, LC=RA 동일)

사이클 후반부(180°-340°)에 걸쳐 플레이스 위치로 이동.

| VR03 구간 | Y (정규화 위치) | 설명 |
|---|---|---|
| 0° → 180° | 0.0 (플랫) | 초기 위치 대기 |
| 180° → 340° | 0.0 → 1.0 (CubicSpline) | 플레이스 위치로 이동 |
| 340° → 360° | 1.0 (플랫) | 플레이스 위치 유지 |

```
R 위치
1.0 │                          ╭──────
    │                         ╱
    │                        ╱
0.0 │━━━━━━━━━━━━━━━━━━━━━━━╯
    └───────────────────────┬────────── VR03 [°]
                            180        340
```

---

## 5) 동작 타임라인 — VR03 각도 기준

### 5-1. LC_RUN 중 Cathode P&P (PUT) 타임라인

> Z = `Cam_STACK_LC_ReverseZ_PUT` (§4-2), R = `Cam_STACK_LC_ReverseX_PUT` (§4-4)

| VR03 구간 | Z축 동작 | R축 동작 | 물리 상태 |
|---|---|---|---|
| 0° → 180° | 0.0 (carry, 들린 상태) | 0.0 (초기 위치 대기) | 전극 들고 carry 위치에서 대기 |
| 180° → 252° | 0.0 (carry) | 0.0 → (플레이스 방향 이동 중) | R 플레이스 위치로 이동 개시 |
| 252° → 274° | 0.0 → 1.0 (하강) | (이동 중) | **전극 하강(PUT) 개시 — R 이동과 겹침** |
| 274° → 340° | 1.0 (하강 완료) | → 1.0 (플레이스 위치 도달) | Z 내려둔 채 R 이동 마무리 |
| 340° → 360° | 1.0 (유지) | 1.0 (유지) | 플레이스 완료, CAMOUT 대기 |

> ⚠ **교정 (2026-05-21)**: 기존 표는 R축을 GET 커브처럼 "0°→180° 이동 후 도달"로 적었으나, Cathode-R은 LC_RUN에서 `Cam_STACK_LC_ReverseX_PUT`(0°–180° 정지, 180°–340° 이동)을 사용한다.  
> 따라서 Z 하강(252°–274°)이 **R 이동 완료(340°) 이전**에 시작된다 — PUT은 "R 이동 후 하강"이 아니라 R 이동과 Z 하강이 부분적으로 동시에 일어나는 복합 동작. 정확한 기구 동작(대각 삽입 / 하강 후 수평 정렬 등)은 기구 도면 확인 필요.

### 5-2. LC_RUN 중 Anode P&P (GET) 타임라인

> Z = `Cam_STACK_RA_ReverseZ_GET` (§4-1), R = `Cam_STACK_RA_ReverseX_GET` (§4-3)

| VR03 구간 | Z축 동작 | R축 동작 | 물리 상태 |
|---|---|---|---|
| 0° → 22° | 0.0 → 1.0 (빠른 하강) | 0.0 (대기, R은 20°부터 이동 개시) | 픽업 위치로 하강 |
| 22° → 180° | 1.0 (픽업 위치) | 0.0 → 1.0 (이동) | 전극 집어 들고 이동 |
| 180° → 360° | 1.0 (carry) | 1.0 (유지) | 전극 들고 이동/유지 |

### 5-3. 전체 사이클 흐름

```
Phase       Cathode P&P (Axis11/12)     Anode P&P (Axis26/27)
─────────────────────────────────────────────────────────────
LC_RUN      ▶ PUT (전극 내려놓기)       ▶ GET (전극 집어 들기)
            VR03 0°→360°               VR03 0°→360°

LC_STACK    (CAMOUT 완료, 정지)         (CAMOUT 완료, 정지)

RA_RUN      ▶ GET (전극 집어 들기)      ▶ PUT (전극 내려놓기)
            VR03 0°→360°               VR03 0°→360°

RA_STACK    (CAMOUT 완료, 정지)         (CAMOUT 완료, 정지)
─────────────────────────────────────────────────────────────
```

> 두 헤드가 **교대로** PUT/GET — 한 헤드가 놓을 때 다른 헤드는 다음 전극을 집는다.

---

## 6) FB 구조 — `FB_Camin_STACK_LC_RUN` 기준

### 6-1. CAMIN 인스턴스 (활성 CAMIN)

| CAMIN 멤버명 | Slave 축 | CAM TO |
|---|---|---|
| `CAMIN_Cam_STACK_LC_ReverseR_PUT` | Axis12 (Cathode R) | `Cam_STACK_LC_ReverseX_PUT` |
| `CAMIN_Cam_STACK_LC_ReverseZ_PUT` | Axis11 (Cathode Z) | `Cam_STACK_LC_ReverseZ_PUT` |
| `CAMIN_Cam_STACK_RA_ReverseR_GET` | Axis27 (Anode R) | `Cam_STACK_RA_ReverseX_GET` |
| `CAMIN_Cam_STACK_RA_ReverseZ_GET` | Axis26 (Anode Z) | `Cam_STACK_RA_ReverseZ_GET` |

### 6-2. CAMOUT 인스턴스

| CAMOUT 멤버명 | Slave 축 | Execute 소스 |
|---|---|---|
| `CAMOUT_Cam_STACK_LC_ReverseR_PUT` | Axis12 (Cathode R) | `STACK_LC_RUN_CAMOUT` |
| `CAMOUT_Cam_STACK_LC_ReverseZ_PUT` | Axis11 (Cathode Z) | `STACK_LC_RUN_CAMOUT` |
| `CAMOUT_Cam_STACK_RA_ReverseR_GET` | Axis27 (Anode R) | `STACK_LC_RUN_CAMOUT` |
| `CAMOUT_Cam_STACK_RA_ReverseZ_GET` | Axis26 (Anode Z) | `STACK_LC_RUN_CAMOUT` |

> `FB_Camin_STACK_RA_RUN`은 대칭 위상을 담당 — CAMIN이 **Cathode(LC) GET + Anode(RA) PUT**을 동기화(`STACK_RA_RUN_CAMIN` 트리거). 즉 LC_RUN과 GET/PUT 역할이 정확히 뒤바뀜.  
> (참고: RA_RUN FB의 CAMOUT 인스턴스명·DB 경로는 LC_RUN과 동일하게 `LC_…_PUT` / `RA_…_GET`로 남아 있음 — 명명 관성으로 보이며, 트리거만 `STACK_RA_RUN_CAMOUT`으로 다름.)

---

## 7) 진공 (VAC) 연동

Pick & Place 동작에는 진공 흡착이 필요합니다.

| I/O DB | 설명 |
|---|---|
| `DI_Unit01_Stack_LC_Reverse_PP_VAC_1` (iDB5031) | Cathode Reverse P&P 진공 1 |
| `DI_Unit01_Stack_LC_Reverse_PP_VAC_2` (iDB5032) | Cathode Reverse P&P 진공 2 |
| `DI_Unit01_Stack_RA_Reverse_PP_VAC_1` (iDB5037) | Anode Reverse P&P 진공 1 |
| `DI_Unit01_Stack_RA_Reverse_PP_VAC_2` (iDB5038) | Anode Reverse P&P 진공 2 |

> VAC 확인 타이밍(GET 완료 조건)과 CAMIN 흐름의 연동 상세는 IO/Sequence FB 확인 필요.

---

## 8) 축 명칭 불일치 정리

| 컨텍스트 | Z축 표기 | 수평/회전축 표기 |
|---|---|---|
| TIA 축 TO 이름 | `Axis11_CathodeReverseP&PElectrodeZ_TB116` | `Axis12_CathodeReverseP&PElectrodeR_TB117` |
| DB_GdbCam 멤버 | `Cam_STACK_LC_ReverseZ_GET` | `Cam_STACK_LC_ReverseR_GET` |
| CAM TO 이름 | `Cam_STACK_LC_ReverseZ_GET` | `Cam_STACK_LC_ReverseX_GET` |
| 이 문서 표기 | Z축 | R축 (TO에서는 X) |

---

## 9) 미확인 항목

| 항목 | 상태 |
|---|---|
| CAM 커브 수치 | ✅ **확인 완료** — Openness export (§4 참조) |
| LC/RA 프로파일 실제 차이 | ✅ **확인 완료** — 완전 동일한 커브 (Z_GET/Z_PUT/X_GET/X_PUT 4종) |
| GET/PUT 동작 타이밍 | ✅ **확인 완료** — GET: 0°-22° Z하강, 20°-180° R이동; PUT: 180°-340° R이동, 252°-274° Z하강 |
| 축 ↔ CAM TO ↔ Phase 매핑 | ✅ **확인 완료** — FB CAMIN 호출 인자로 검증 (§6). LC_RUN: Cathode=PUT(Axis11/12), Anode=GET(Axis26/27) |
| CAMIN SyncMode/StartMode 파라미터 | 🔶 **부분 확인** — `MC_CAMIN` 인터페이스에 `MasterSyncPosition`·`SyncProfileReference`·`MasterStartDistance`·`Velocity/Accel/Decel/Jerk`·`ApplicationMode`·`SyncDirection` 존재. 모든 CAMIN 호출이 동일 상수 4개(`0.01`, `3`, `0`, `2`)를 전달 — 값↔파라미터 정확 매핑은 XML 정본 필요(.md 다이제스트가 함수 호출의 파라미터명을 생략하므로 `FB_Camin_STACK_LC_RUN.xml` 확인) |
| 정규화 Y=1이 실제 물리 단위로 얼마인지 | 🔶 **확인됨(정적 산출 불가)** — `DB_GdbCam`의 `CamData.SlaveScaling/SlaveOffset`에 export StartValue 없음 → 런타임/레시피에서 기록(FB Network 5·7이 `CamData → CamIn` 복사). 정적 export로는 물리 수치 불명, 런타임 모니터링 필요 |
| "Reverse" 명칭의 물리적 의미 (반전/뒤집기) | ❌ 전극 배향 플립 여부 불명확 — 기구 도면 확인 필요 |
| GET 완료 후 VAC 확인 → 다음 단계 전환 조건 | ✅ **확인 완료** — LC: `FB_Auto_Sub1_Stack_600` step **628** (Network 17 rung 5), RA: `FB_Auto_Sub1_Stack_700` step **728**. 공통 패턴: `Main_PP_VAC_1+2.Detect_BlowOff AND Reverse_PP_VAC_1+2.Detect_BlowOn` (4-신호 AND) → 다음 스텝 + `DB_Info.Electrode_*[1]→[2]` 시프트. PUT 측(641/741)은 `Reverse_PP_BlowOff + Align_Table_BlowOn + IEC_Timer_AUTO_*_VISION.Q` AND. 상세는 §10 참조. |

---

## 10) 진공 (VAC) 핸드오프 — 시퀀스 FB 전환 조건

CAMIN(VR03 cam 모션)이 Reverse P&P의 **위치 궤적**을 담당하고, 진공 흡착 ON/OFF 전환과 다음 시퀀스 진입은 별도의 시퀀스 FB(`FB_Auto_Sub1_Stack_600/700`)가 `DI_Auto_Number.Auto_Number_Stack` 정수 step을 통해 관리한다.

> 소스: `FB_Auto_Sub1_Stack_600.xml` (LC, Cathode 측), `FB_Auto_Sub1_Stack_700.xml` (RA, Anode 측).  
> 단일 ASQ_CMD: LC=`DB_Stack_DATA.ASQ_CMD.LC_Single_CMD`, RA=`DB_Stack_DATA.ASQ_CMD.RA_Single_CMD`.

### 10-1. 한 사이클 내 Reverse P&P 진공 전환 지점

| Step (LC / RA) | 위치 | 진공 명령 (SET) | 전환 조건 (다음 step 진입) |
|---|---|---|---|
| 628 / 728 | Main PP가 Reverse PP 위로 내려와 닿는 지점 (Main Z.Position[3]) | Main_PP_VAC_1+2 → BlowOff, **Reverse_PP_VAC_1+2 → BlowOn** | `Main_PP_VAC_1.Detect_BlowOff AND Main_PP_VAC_2.Detect_BlowOff AND Reverse_PP_VAC_1.Detect_BlowOn AND Reverse_PP_VAC_2.Detect_BlowOn` |
| 641 / 741 | Reverse PP가 Align Table 위에 내려놓는 지점 (CAM 모션 종료 후 Reverse Z down) | **Reverse_PP_VAC_1+2 → BlowOff**, Align_Table_VAC → BlowOn | `Reverse_PP_VAC_1.Detect_BlowOff AND Reverse_PP_VAC_2.Detect_BlowOff AND Align_Table_VAC.Detect_BlowOn AND IEC_Timer_AUTO_*_VISION.Q` |

> **두 진공 핸드오프 모두 4-신호 AND** — 1번/2번 흡착부가 독립적으로 감지되어 한쪽만 OK여서는 절대 다음 스텝으로 넘어가지 않는다.  
> PUT(641/741)에는 **VISION 타이머** 까지 AND로 묶여, 비전 촬영 시간을 보장한 뒤에만 다음 스텝으로 진입한다.

### 10-2. Step 628 (LC) / 728 (RA) 흐름 — Reverse PP GET 완료

```
[Main P&P Head01 Z down to Position[3]]              ← Network 16 (step 627→628)
                │
                ▼
[step 628 진입]
    rung 1: SET LC_Main_PP_Head_VAC_1.Sequence_Command_VacuumBlowOff
    rung 2: SET LC_Main_PP_Head_VAC_2.Sequence_Command_VacuumBlowOff
    rung 3: SET LC_Reverse_PP_VAC_1.Sequence_Command_VacuumBlowOn
    rung 4: SET LC_Reverse_PP_VAC_2.Sequence_Command_VacuumBlowOn
                │
                ▼  (rung 5 전환 조건 4-AND)
[Main 1,2 BlowOff + Reverse 1,2 BlowOn 모두 감지]
                │
                ├── Move Electrode_Cathode[1] → [2]
                ├── RESET Electrode_Cathode[1].Exist
                └── Move INT#629 → Auto_Number_Stack   (Main PP Z 복귀로 진행)
```

> **rung 5에는 분기 B(`AlwaysFALSE`로 막힌 OR 가지)가 존재** — 정상 운전에서는 항상 분기 A(4-신호 AND)로만 전환된다. AlwaysFALSE 가지는 single-suction 등 운전 모드 분기 슬롯으로 보임(현 export에서는 항상 비활성).  
> RA(step 728)도 같은 4-rung 구조 — LC↔RA 동일 패턴, 신호 이름만 `RA_Main_PP_Head_VAC_*` / `RA_Reverse_PP_VAC_*`로 치환.

### 10-3. Step 641 (LC) / 741 (RA) 흐름 — Reverse PP PUT 완료 (Align Table 인계)

```
[Reverse PP CAM 모션 완료 + Reverse R put(R.Position[3]) + Reverse Z down(Z.Position[3])]
                                                     ← Network 26 (step 639→640→641)
                │
                ▼
[step 641 진입]
    rung 1: SET LC_Reverse_PP_VAC_1.Sequence_Command_VacuumBlowOff
    rung 2: SET LC_Reverse_PP_VAC_2.Sequence_Command_VacuumBlowOff
    rung 3: SET LC_Align_Table_VAC.Sequence_Command_VacuumBlowOn
                │
                ▼  (rung 4 전환 조건 4-AND, VISION 타이머 포함)
[Reverse 1,2 BlowOff + Align_Table BlowOn 감지 + IEC_Timer_AUTO_CATHODE_VISION.Q]
                │
                ├── Move Electrode_Cathode[2] → [3]
                ├── RESET Electrode_Cathode[2].Exist
                └── Move INT#642 → Auto_Number_Stack   (Reverse PP Z up으로 진행)

    rung 5: [LC_Single_CMD AND step==641 AND DB_StackRecipe.Auto.Dryrun]
            => DB_Align_Vision.Align_SQ_Vision_Trg_Bit[6]   (Dryrun 시 비전 트리거)
```

> RA(step 741)은 `IEC_Timer_AUTO_ANODE_VISION.Q` 사용 — Cathode/Anode 별도 비전 타이머 인스턴스.

### 10-4. DI 멤버 명세 — VAC 감지 비트

| 멤버 | 의미 |
|---|---|
| `VIO.Sequence_Command_VacuumBlowOn` | 시퀀스가 "흡착 시작" 명령 |
| `VIO.Sequence_Command_VacuumBlowOff` | 시퀀스가 "흡착 해제" 명령 |
| `VIO.Detect_VacuumBlowOn` | 실제 흡착 ON 감지 (압력 도달) |
| `VIO.Detect_VacuumBlowOff` | 실제 흡착 OFF 감지 (압력 해제) |
| `VIO.Interlock_VacuumBlowOn` | 흡착 ON 명령 인터록 (전제 조건) |
| `VIO.Interlock_VacuumBlowOff` | 흡착 OFF 명령 인터록 (전제 조건) |

VAC DI 인스턴스 (이전 §7 보강):

| DI 인스턴스 | iDB | 사용 step |
|---|---|---|
| `DI_Unit01_Stack_LC_Reverse_PP_VAC_1` | iDB5031 | step 628 ON, 641 OFF |
| `DI_Unit01_Stack_LC_Reverse_PP_VAC_2` | iDB5032 | step 628 ON, 641 OFF |
| `DI_Unit01_Stack_RA_Reverse_PP_VAC_1` | iDB5037 | step 728 ON, 741 OFF |
| `DI_Unit01_Stack_RA_Reverse_PP_VAC_2` | iDB5038 | step 728 ON, 741 OFF |
| `DI_Unit01_Stack_LC_Main_PP_Head_VAC_1/2` | — | step 622 ON (Main GET), 628 OFF (Main → Reverse 인계) |
| `DI_Unit01_Stack_LC_Align_Table_VAC` | — | step 641 ON (Reverse → Align 인계) |

### 10-5. CAMIN 사이클과의 정합

```
[step 617/618: Reverse PP 시작 위치(Z up + R get) 도달]
        │
        │   (이 사이에 CAMIN 트리거 — VR03 cam 모션 동안 Reverse PP가 cam 궤적으로 이동)
        │   Reverse PP는 §4-1~4-4 CAM 커브를 따라 VR03 0°→360° 동안 GET 위치 → carry → PUT 위치로 이동
        │
[step 619: 판정] → [step 625-627: Main PP가 Reverse PP 위치로 내려옴]
        │
        ▼
[step 628: 진공 핸드오프 (Main OFF + Reverse ON), 4-신호 AND]   ← GET 완료
        │
        ▼
[step 629-640: Main PP 복귀, Align Table 이동, Reverse PP 다시 Z down]
        │
        ▼
[step 641: 진공 핸드오프 (Reverse OFF + Align ON) + VISION 타이머, 4-신호 AND]   ← PUT 완료
        │
        ▼
[step 642-: Reverse PP 복귀(Z up), Auto_Number_Stack 619 또는 다음 사이클로]
```

> **요점**: CAMIN은 Reverse PP를 **물리적으로** GET↔PUT 위치 사이로 운반만 한다. 흡착 ON/OFF 명령 자체는 Sequence FB가 step 628/641(LC) 또는 728/741(RA)에서 명시적으로 SET하고, 전환은 4-신호 압력 감지가 모두 확보되어야만 일어난다 — 즉 CAM 모션 완료 ≠ GET/PUT 완료, 진공 감지가 GET/PUT 완료의 정의이다.
