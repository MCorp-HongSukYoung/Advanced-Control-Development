# Stack Table PP (Main Pick & Place) — Motion Profile

> 작성: 2026-05-19  
> 소스: `FB_Camin_STACK_LC_RUN`, `FB_Camin_STACK_RA_RUN`, `DB_GdbCam`  
> CAM 데이터: TIA Portal Openness export (2026-05-19) — `exports/.../cam_exports/Cam_STACK_*_PP*.xml`  
> 관련: [`VR축_0to360_전체동작.md`](VR축_0to360_전체동작.md), [`Reverse_PP_Motion_Profile.md`](Reverse_PP_Motion_Profile.md)

---

## 0) 한 줄 결론

> **PP = VR03 한 사이클 내에서 X 직선 이동 + Z 싱글 다이브 구조.**  
> VR03 180°에서 완전 하강 → 픽업 또는 플레이스. 4개 헤드 × GET/PUT 총 16개 TO이지만 커브 형상은 Z 1종·X 1종으로 동일.  
> 물리적 위치(시작/끝점)는 CAMIN의 `SlaveOffset`·`SlaveScaling`으로 축마다 별도 지정.

---

## 1) 하드웨어 구성

| 헤드 | Axis (X) | TB | Axis (Z) | TB | 역할 |
|---|---|---|---|---|---|
| **LC PP1** (CathodeMainP&PHead01) | Axis_13 | TB101 | Axis_14 | TB118 | Cathode: 매거진 → Reverse Table |
| **LC PP2** (CathodeMainP&PHead02) | Axis_15 | TB104 | Axis_16 | TB119 | Cathode: AlignTable → Stack Table |
| **RA PP1** (AnodeMainP&PHead01) | Axis_28 | TB130 | Axis_29 | TB142 | Anode: AlignTable → Stack Table |
| **RA PP2** (AnodeMainP&PHead02) | Axis_30 | TB134 | Axis_31 | TB143 | Anode: 매거진 → Reverse Table |

- **X축**: 수평 이동 — 출발지에서 목적지까지 직선 이송
- **Z축**: 수직 이동 — 하강해서 픽업/플레이스 후 상승

---

## 2) CAM 프로파일 목록

총 16개 TO (헤드 4 × 동작 2 × 축 2):

> ✅ **FB 정본 검증 (`FB_Camin_STACK_LC_RUN` / `_RA_RUN`의 CAMIN static·Network3)** — 헤드쌍 PP1/PP2는 **한 phase 안에서 GET/PUT 반대**로 동작한다 (이전 표의 "한쪽 헤드 둘 다 동일 동작"은 오류였음, 정정).

| Phase | LC PP1 | LC PP2 | RA PP1 | RA PP2 |
|---|---|---|---|---|
| **LC_RUN** | **GET** (`Cam_STACK_LC_PP1X/Z_GET`) | **PUT** (`…LC_PP2X/Z_PUT`) | **PUT** (`…RA_PP1X/Z_PUT`) | **GET** (`…RA_PP2X/Z_GET`) |
| **RA_RUN** | **PUT** (`…LC_PP1X/Z_PUT`) | **GET** (`…LC_PP2X/Z_GET`) | **GET** (`…RA_PP1X/Z_GET`) | **PUT** (`…RA_PP2X/Z_PUT`) |

> 해석: 각 헤드는 §1의 고정 경로(예: LC PP1 = 매거진→Reverse Table)를 가지며, 한 phase에서 GET(소스에서 픽업)하면 다음 phase에서 PUT(목적지에 배치)한다. 같은 side의 PP1/PP2가 GET↔PUT으로 엇갈려 파이프라인을 이룬다.
>
> **실측 결과**: 16개 TO 전부 동일한 커브 데이터. X 1종 + Z 1종으로 수렴 (커브 형상은 GET/PUT 무관, 물리 위치만 SlaveOffset/Scaling로 구분 — §6).

---

## 3) 실측 CAM 커브 데이터

모든 프로파일: `InterpolationMode="CubicSpline"`, `BoundaryConditions="NoConstraint"`  
마스터 범위: 0°–360° (VR03), 팔로워 범위: -1~1 (정규화)

### 3-1. X축 프로파일 (전 헤드·전 동작 동일)

출발지(0)에서 목적지(1)로 비선형 가속·감속 이동.

| VR03 구간 | Y (정규화 위치) | 설명 |
|---|---|---|
| 0° → 36° | 0.0 (플랫) | 출발 위치 대기 |
| 36° → 180° | 0.00 → 0.50 (CubicSpline) | 초반 가속 이동 |
| 180° → 280° | 0.50 → 0.95 (CubicSpline) | 중후반 이동 |
| 280° → 340° | 0.95 → 1.00 (CubicSpline) | 목적지 감속 정렬 |
| 340° → 360° | 1.0 (플랫) | 목적지 도달 후 유지 |

```
X 위치
1.00 │                              ╭────
0.95 │                          ╭──╯
     │                      ╱
0.50 │              ╭──────╯
     │           ╱
0.00 │━━━━━━━━━━━╯
     └────────┬──────────────────┬──┬── VR03 [°]
              36                280 340
```

> **비선형 가속 특성**: 36°-180° 구간에서 이동량의 50%를 소화 (빠른 가속), 280°-340° 구간에서 5%만 남겨 미세 감속 정렬. S-커브 변형.

### 3-2. Z축 프로파일 (전 헤드·전 동작 동일)

VR03 한 사이클 안에서 **완전 하강 후 완전 상승** — 단 한 번의 다이브.

| VR03 구간 | Y (정규화 위치) | 설명 |
|---|---|---|
| 0° → 20° | 0.00 → 0.10 | 하강 개시 (완만) |
| 20° → 50° | 0.10 → 0.60 | 주 하강 구간 (급가속) |
| 50° → 90° | 0.60 → 0.90 | 목표 접근 (감속) |
| 90° → 180° | 0.90 → 1.00 | **소프트 랜딩** (VR03=180°에서 최저점) |
| 180° → 270° | 1.00 → 0.90 | **젠틀 리프트** (들어올림 개시) |
| 270° → 310° | 0.90 → 0.60 | 상승 가속 |
| 310° → 340° | 0.60 → 0.08 | 빠른 상승 |
| 340° → 360° | 0.08 → 0.00 | 상단 복귀 완료 |

```
Z (하강=+)
1.00 │              ╭─────╮         ← VR03=180°: 픽업/플레이스 순간
0.90 │          ╭──╯       ╰──╮
0.60 │       ╭──╯              ╰──╮
0.10 │    ╭──╯                    ╰──╮
0.00 │━━━━╯                          ╰━━
     └────┬──┬────┬──────┬────────┬──┬── VR03 [°]
          20 50  90     180      310 360
```

> **핵심**: VR03=180°에서 최저점 도달 = **이 순간 VAC ON/OFF 전환** (픽업 또는 플레이스).  
> 소프트 랜딩(90°-180°)과 젠틀 리프트(180°-270°)로 전극·기구에 충격 최소화.

---

## 4) X·Z 복합 동작 — 궤적 해석

PP 헤드는 X 이동과 Z 다이브를 동시에 수행한다.

```
높이(Z)
  ↑
0 │ ●─────────────────────────────────────────● 출발/도착 높이
  │  ╲                                       ╱
  │   ╲                                     ╱
  │    ╲         ● VR03=180°               ╱
1 │     ╰───────[ 픽업 또는 플레이스 ]──────╯
  └────────────────────────────────────────────→ X 위치
  출발지(0)                              목적지(1)
```

- 출발 시(X=0, Z=0): 헤드가 출발지 위 상단에서 대기
- VR03=180° (X≈0.5, Z=1.0): 헤드가 경로 중간쯤에서 완전 하강 → 픽업/플레이스
- 도착 시(X=1, Z=0): 헤드가 목적지 위 상단 도달

> **설계 의도**: X 이동 중간(VR03=180°)에 Z 최저점이 오도록 설계 — X가 0.5 위치에서 Z가 픽업/플레이스. 출발지와 목적지의 **중간 공중 경로**에서 전극을 처리.  
> GET의 경우 중간 지점이 매거진/소스 위, PUT의 경우 목적지(Reverse Table/Stack Table) 위가 되도록 SlaveOffset·SlaveScaling 조정.

---

## 5) 동작 타임라인 — LC_RUN 기준

VR03 한 사이클(0°→360°) 동안 4개 헤드가 동시에 동작:

```
VR03 각도    LC PP1 (GET)          LC PP2 (PUT)          RA PP1 (PUT)          RA PP2 (GET)
───────────────────────────────────────────────────────────────────────────────────────────
0°~ 36°    X 대기 / Z 초기        X 대기 / Z 초기        X 대기 / Z 초기        X 대기 / Z 초기
36°~180°   X 이동 / Z 하강 중     X 이동 / Z 하강 중     X 이동 / Z 하강 중     X 이동 / Z 하강 중
    180°   ▼ Z 최저 (픽업)        ▼ Z 최저 (배치)        ▼ Z 최저 (배치)        ▼ Z 최저 (픽업)
180°~360°  X 계속 / Z 상승 중     X 계속 / Z 상승 중     X 계속 / Z 상승 중     X 계속 / Z 상승 중
    360°   픽업 완료(→PUT phase)  배치 완료(→GET phase)  배치 완료(→GET phase)  픽업 완료(→PUT phase)
───────────────────────────────────────────────────────────────────────────────────────────
```

RA_RUN은 §2 표대로 각 헤드의 GET/PUT가 반대로 바뀐다 (LC PP1 PUT·LC PP2 GET·RA PP1 GET·RA PP2 PUT).

> ⚠️ **VAC 타이밍 정정**: VR03=180°는 Z가 기하학적으로 최저(픽/플 지점)인 위상일 뿐, **진공 신호 자체는 cam 각도로 토글되지 않는다.** PP 헤드 진공(`DI_Unit01_Stack_[LC/RA]_Main_PP_Head_VAC_[1/2/3]`)의 `Sequence_Command_VacuumBlowOn/Off`는 **`FB_Auto_Sub1_Stack_600`(LC)/`_700`(RA)** 에서 `Auto_Number_Stack` 스텝 + 축 `Position[n]` 도달로 SET된다 (예: step 622에서 Z `Position[3]` 도달 → `VacuumBlowOn`). 즉 GET=흡착ON / PUT=흡착OFF는 맞지만, 그 발행은 cam이 아니라 시퀀스 스텝이다 (§8).

---

## 6) GET vs PUT 차이 — SlaveOffset/SlaveScaling

커브 형상은 동일하지만 실제 물리 위치는 다르다.

| 파라미터 | 역할 |
|---|---|
| `SlaveOffset` | Y=0 기준점 이동 (출발 위치 보정) |
| `SlaveScaling` | Y=0→1 범위를 실제 mm/deg로 스케일 |

- **GET SlaveOffset/Scaling**: X=0이 소스(매거진/AlignTable) 위, X=1이 경유지 위
- **PUT SlaveOffset/Scaling**: X=0이 경유지 위, X=1이 목적지(Reverse Table/Stack Table) 위
- Z SlaveOffset/Scaling: 각 헤드가 실제 목표물에 닿는 Z 위치로 설정

> ✅ **출처 확인 완료** (`FB_Camin_STACK_LC_RUN` N5/N7 → `CamData.SlaveOffset/Scaling`, 그 값은 `FB_AXIS_TO_CAM_STATUS`가 `FC_AXIS_TO_CAM_STATUS` 호출로 주입):
> - `SlaveOffset = IN_Start`, `SlaveScaling = (IN_Start − IN_LONG)×(−1) = IN_LONG − IN_Start`
> - GET cam(예: `Cam_STACK_LC_PP1X_GET`, Axis13): `IN_Start = DB_StackRecipe.Servo[13].Position_03`, `IN_LONG = …Position_02` — **GET/PUT cam이 서로 다른 Position을 받아** 같은 커브를 다른 물리 위치에 매핑
> - 출처는 `DB_StackRecipe.Servo[N].Position_xx` (레시피 런타임 주입) — 이전에 적힌 `DB_RecipeCfg.setpoints`는 **부정확**. 실제 mm/deg 수치는 정적 export로는 확정 불가 (레시피 데이터)
> - 호출 네트워크는 `.md` 다이제스트에서 누락됨 → `FB_AXIS_TO_CAM_STATUS.xml` 정본 ([[project_md_digest_strips_functions]])

---

## 7) Reverse P&P와의 비교

| 항목 | PP (Main P&P) | Reverse P&P |
|---|---|---|
| Z 다이브 횟수 | 1회 (VR03=180° 1회 완전 하강) | 1회 (GET: 0°-22°, PUT: 252°-274° — 각각 얕은 다이브) |
| X 이동 구간 | 36°-340° (전체 스윕) | GET: 20°-180°, PUT: 180°-340° (각각 절반) |
| GET/PUT 프로파일 차이 | 동일 (SlaveOffset/Scaling으로 구분) | 다름 (Z GET은 빠른 초기 하강, PUT은 후반부 하강) |
| 축 방향 명칭 | X(수평), Z(수직) | R(회전/수평), Z(수직) |

---

## 8) 미확인 항목

| 항목 | 상태 |
|---|---|
| 16개 TO 커브 수치 | ✅ **확인 완료** — 전부 동일, Z 1종·X 1종 |
| LC/RA·GET/PUT 프로파일 차이 | ✅ **확인 완료** — 차이 없음 (형상 동일) |
| VR03=180° 픽업/플레이스 타이밍 | ✅ **확인 완료** — Z 최저점 = pick/place 순간 |
| Phase별 헤드 GET/PUT 매핑 | ✅ **확인 완료 (정정)** — LC_RUN: LC_PP1=GET·LC_PP2=PUT·RA_PP1=PUT·RA_PP2=GET (`FB_Camin_STACK_LC/RA_RUN`). 헤드쌍이 phase 내 반대 동작 (§2) |
| SlaveOffset·SlaveScaling 출처 | ✅ **확인 완료** — `FC_AXIS_TO_CAM_STATUS` 주입, `IN_Start=Servo[N].Position_03·IN_LONG=Position_02`, GET/PUT별 상이 (`DB_RecipeCfg`가 아니라 `DB_StackRecipe.Servo`) |
| VAC 전환 발행 방식 | ✅ **확인 완료 (정정)** — `FB_Auto_Sub1_Stack_600/700`에서 `Auto_Number` 스텝+축 Position 도달로 SET. **VR03=180° cam-각도 토글 아님** (GET=ON/PUT=OFF는 맞음) |
| SlaveOffset·SlaveScaling 실제 mm/deg 값 | ❌ `DB_StackRecipe.Servo[N].Position_02/03` 런타임 레시피값 — 정적 export로 확정 불가 |
| X=0.5 (VR03=180°)가 소스 정확히 위인지 | ◐ 구조 확인 — X@180° = (Position_03+Position_02) 중점. 그 중점이 물리 소스 위인지는 레시피값+레이아웃 필요 |
| 연속 CAM RUN 모드와 Single 시퀀스(600/700)의 관계 | ⚠️ PP 진공 명령이 `*_Single_CMD` 경로에만 존재 — CAM RUN과 stepped 전사(transfer)의 분담 관계는 추가 확인 권장 |
