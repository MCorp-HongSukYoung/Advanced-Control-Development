# Stack Table Reverse P&P — Motion Profile

> 작성: 2026-05-19  
> 소스: `FB_Camin_STACK_LC_RUN`, `FB_Camin_STACK_RA_RUN`, `DB_GdbCam`, `DB_Global_Cam_Control`  
> CAM 데이터: TIA Portal Openness export (2026-05-19) — `exports/.../cam_exports/Cam_STACK_*Reverse*.xml`  
> 관련: [`VR축_0to360_전체동작.md`](VR축_0to360_전체동작.md), [`SwingRoller_Motion_Profile.md`](SwingRoller_Motion_Profile.md)

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

| VR03 구간 | Z축 동작 | R축 동작 | 물리 상태 |
|---|---|---|---|
| 0° → 180° | 0.0 (carry 위치) | 0.0 → 1.0 (이동 중) | 전극 들고 플레이스 위치로 이동 |
| 180° → 252° | 0.0 (carry) | 1.0 (플레이스 위치 도달) | 플레이스 위치에서 하강 대기 |
| 252° → 274° | 0.0 → 1.0 (하강) | 1.0 (유지) | **전극 내려놓기 (PUT)** |
| 274° → 360° | 1.0 (플레이스 위치) | 1.0 (유지) | CAMOUT 대기 |

### 5-2. LC_RUN 중 Anode P&P (GET) 타임라인

| VR03 구간 | Z축 동작 | R축 동작 | 물리 상태 |
|---|---|---|---|
| 0° → 22° | 0.0 → 1.0 (빠른 하강) | 0.0 (대기) | 픽업 위치로 하강 |
| 20° → 180° | 1.0 (픽업 위치) | 0.0 → 1.0 (이동) | 전극 집어 들고 이동 |
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

> `FB_Camin_STACK_RA_RUN`에는 대칭적으로 RA PUT + LC GET CAMIN/CAMOUT이 존재 (RA_RUN_CAMOUT 트리거).

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
| LC/RA 프로파일 실제 차이 | ✅ **확인 완료** — 완전 동일한 커브 |
| GET/PUT 동작 타이밍 | ✅ **확인 완료** — GET: 0°-22° Z하강, 20°-180° R이동; PUT: 180°-340° R이동, 252°-274° Z하강 |
| CAMIN SyncMode/StartMode 파라미터 | ❌ FB XML에 명시 없음 — 기본값 또는 런타임 설정 추정 |
| 정규화 Y=1이 실제 물리 단위로 얼마인지 | ❌ SlaveScaling, SlaveOffset DB 값 확인 필요 |
| "Reverse" 명칭의 물리적 의미 (반전/뒤집기) | ❌ 전극 배향 플립 여부 불명확 — 기구 도면 확인 필요 |
| GET 완료 후 VAC 확인 → 다음 단계 전환 조건 | ❌ IO/Sequence FB 별도 확인 필요 |
