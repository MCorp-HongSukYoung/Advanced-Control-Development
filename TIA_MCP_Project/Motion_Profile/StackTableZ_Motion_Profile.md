# Stack Table Z Motion Profile — Axis36 적층 테이블 Z(인덱싱)

> 근거: TIA Portal Openness 직접 export (2026-06-02)
> 대상 TO: `Cam_STACK_TableZ_GET`, `Cam_STACK_TableZ_PUT`
> 마스터: **VR04_MandrelLeadingAxis** (STACK Phase 전용, VR03과 별개 — Mandrel과 동일 마스터)
> 관련: [`Mandrel_Motion_Profile.md`](Mandrel_Motion_Profile.md), [`SwingRoller_Motion_Profile.md`](SwingRoller_Motion_Profile.md)

---

## 1) 하드웨어 구성

### 1-1. 축

| Axis | 명칭 | 역할 | TB | Phase |
|------|------|------|-----|-------|
| **Axis36** | Stack Table Z | 적층 테이블 승강(전 적층 단계 공용) | TB125 | LC_STACK · RA_STACK 모두 능동 |

> Mandrel Y/Z(Axis41~48)는 LC/RA 측이 분리돼 한 Phase에 한쪽만 움직이지만, **Stack Table Z는 테이블 1대를 공용으로 쓰므로 두 Phase 모두에서 동일 프로파일로 동작**한다.

### 1-2. 물리 배치

```
Stack Table (측면 뷰)

   [LC/RA P&P] ─▶ 전극 안착 (적층 높이 = 일정)
   ─────────────────────────────  ← 적층면 높이는 매 단 고정
        ▓▓▓▓▓ 셀 스택 (점점 두꺼워짐)
        ▓▓▓▓▓
   ┌───────────┐
   │ Stack Table│  ▲ Axis36 Z
   └───────────┘  │  적층 1단마다 한 피치씩 인덱싱 (하강)
        VR04 캠 추종
```

> 셀이 한 단 쌓일 때마다 스택이 두꺼워지므로, 적층면(P&P/Mandrel 작업 높이)을 일정하게 유지하려면 테이블이 매 사이클 **한 피치씩 인덱싱**되어야 한다. 그래서 Table Z 캠은 홈 복귀형이 아니라 **단조 인덱싱형**이다(§4 참조).

---

## 2) CAMIN 구조

### 2-1. 결합 정보 (정본)

| 항목 | 값 |
|---|---|
| CAMIN 인스턴스 | `CAMIN_Cam_STACK_TableZ_GET` (MC_CAMIN) |
| CAMOUT 인스턴스 | `CAMOUT_Cam_STACK_TableZ_GET` (MC_CAMOUT) |
| 보간 인스턴스 | `instMC_InterpolateCam_STACK_TableZ_GET` / `_PUT` (MC_INTERPOLATECAM) |
| 마스터 | `VR04_MandrelLeadingAxis` |
| 슬레이브 | `Axis36_StackTableZ_TB125` |
| 사용 캠 프로파일 | `Cam_STACK_TableZ_GET` (**LC_STACK·RA_STACK 양쪽 동일**) |
| FB | `FB_Camin_STACK_LC_STACK` (call ②), `FB_Camin_STACK_RA_STACK` (call ②) |
| Execute 트리거 | STACK Phase CAMIN 비트 (`STACK_LC_STACK_CAMIN` / `STACK_RA_STACK_CAMIN`) |
| MasterOffset / MasterScaling | 1.0 / 1.0 |
| SlaveOffset / SlaveScaling | `DB_GdbCam.STACK_TABLE.Cam_STACK_TableZ_GET.CamData.*` (레시피값) |
| DB 경로 | `DB_GdbCam.STACK_TABLE.Cam_STACK_TableZ_GET` (type_Gdb_Cam) |

> **핵심**: `FB_Camin_STACK_LC_STACK`·`FB_Camin_STACK_RA_STACK` 둘 다 `Cam_STACK_TableZ_GET` 프로파일을 `Axis36`에 결합한다. Mandrel처럼 반대 측을 PUT(정지) 프로파일로 가르지 않는다.

### 2-2. 캠 생성 방식 — InterpolateCam 런타임 생성

Mandrel/PP/Swing과 달리 Table Z는 정적 캠 테이블을 쓰지 않고 **`MC_InterpolateCam`이 런타임에 캠을 보간 생성**한다. `FB_Interpolate_Cam`에서:

```
DB_GdbCam.STACK_TABLE.Cam_STACK_TableZ_GET.InterpolateCam.Execute := TRUE;
DB_GdbCam.STACK_TABLE.Cam_STACK_TableZ_PUT.InterpolateCam.Execute := TRUE;
    instMC_InterpolateCam_STACK_TableZ_GET( := Cam_STACK_TableZ_GET, ...);
    instMC_InterpolateCam_STACK_TableZ_PUT( := Cam_STACK_TableZ_PUT, ...);
```

→ 실제 적층 위치(피치·높이)는 `SlaveOffset`/`SlaveScaling`(레시피)로 스케일된다. 아래 곡선은 **정규화 형상(follow −1~1)** 이다.

---

## 3) CAM 프로파일 데이터 (실측)

| 프로파일 | 사용 | 점 수 | 형태 |
|---|---|---|---|
| **`Cam_STACK_TableZ_GET`** | LC_STACK·RA_STACK CAMIN 결합 (실사용) | 4 (+ Line 1) | 0°~168° 홈 유지 → 168°~360° 단조 상승 |
| `Cam_STACK_TableZ_PUT` | InterpolateCam만, CAMIN 미결합 (예비) | 2 | 0→1 선형 램프 |

- InterpolationMode: **CubicSpline**
- DesignLeadingRange: **0~360°** (마스터 VR04)
- DesignFollowingRange: **−1 ~ 1** (정규화 follow)

---

## 4) GET 프로파일 — 인덱싱 (실사용 곡선)

**형태: 0°~168° 완전 홈 유지(Line) → 168°~360° 단조 상승, 360°에서 최대**

| VR04 각도 | Y(정규화) | 설명 |
|---|---|---|
| 0° | 0.000 | 사이클 시작 (직전 사이클 인덱스 완료 지점) |
| 0° ~ 168° | 0.000 | **완전 정지 (Line 구간)** — 적층·압착 동안 테이블 고정 |
| 168° | 0.000 | 인덱싱 시작 |
| 340° | 0.900 | 인덱싱 거의 완료 |
| **360° (= 0°)** | **1.000** | **인덱싱 1피치 완료 → CAMOUT** |

```
Y
1.0 |                                   ●360°
    |                                 /
0.9 |                            ●340°
    |                         /
    |                      /
    |                   /
0.0 |●━━━━━━━━━━━━━━━●168°
    0°             168°      340° 360°
                     VR04 →
```

**특징**:
- **홈 복귀가 없는 단조 곡선** — 0°에서 0, 360°에서 1.0. 다른 STACK 축(Mandrel Y/Z 등)은 360°에 다시 0으로 복귀하지만, Table Z는 사이클 끝에서 1.0에 도달한 뒤 CAMOUT → 다음 사이클 `SlaveOffset`이 새 기준으로 갱신되며 **누적 인덱싱**된다.
- **앞 168°는 명시적 Line(직선) 구간으로 완전 고정** — P&P가 전극을 안착하고 Mandrel이 압착하는 동안 테이블이 흔들리지 않도록 보장.
- **168°~360°에 한 피치 이동** — 적층·압착이 끝난 뒤(셀 1단 완성 후) 다음 단을 위해 테이블을 한 피치 인덱싱.
- 실제 이동 방향/크기는 레시피 `SlaveScaling` 부호·크기로 결정(스택이 두꺼워지므로 적층면 높이를 유지하려면 통상 하강 방향).

---

## 5) PUT 프로파일 — 예비 (CAMIN 미결합)

```
Point X=0   Y=0
Point X=360 Y=1
```

→ 0→1 선형 램프. `FB_Interpolate_Cam`에서 보간은 되지만, `FB_Camin_STACK_LC/RA_STACK`의 CAMIN 호출은 **GET 프로파일만** Axis36에 결합한다. 즉 PUT은 현재 결합 경로에서 미사용(예비/대칭용).

---

## 6) Mandrel과의 타이밍 비교

```
Mandrel Y | 홈──전진──────180°(최대)──────복귀──홈(322°)
Mandrel Z | 홈·완속접근──────급속압착 220°(최대)──복귀──홈(360°)
Table  Z  | ━━━━홈 고정━━━━━168°│──────인덱싱──────▶ 360°(1피치)
                                │
VR04: 0°        168°    180°  220°            340° 360°
                 │        │     │
                 │        │     └── Mandrel Z 최대 압착
                 │        └──────── Mandrel Y 최대 전진
                 └───────────────── Table Z 인덱싱 시작
```

**시퀀스 해석**:
1. **0°~168°**: Table Z 고정. 이 구간에 P&P 안착, Mandrel Y 전진(180° 피크)·Z 압착(220° 피크)이 일어난다 → 작업 중 테이블이 움직이면 안 되므로 Line으로 완전 고정.
2. **168°~360°**: 압착이 끝나가는 시점부터 Table Z가 한 피치 인덱싱 → 다음 단 적층 높이를 맞춤.
3. **360°**: 인덱싱 완료 + CAMOUT → 다음 사이클은 갱신된 기준 위치에서 다시 0°부터 시작.

---

## 7) 다른 기구와 비교

| 기구 | 마스터 | 곡선 형태 | 최대 위치 각도 | 복귀 | 설계 특징 |
|---|---|---|---|---|---|
| **Stack Table Z** | VR04 | 홈고정→단조상승 | **360°** | **없음(인덱싱)** | 매 셀 1피치 누적 이동 |
| Mandrel Y | VR04 | 대칭 벨 커브 | 180° | 있음 | 수평 정렬 |
| Mandrel Z | VR04 | 3단 속도 | 220° | 있음 | 완속→급속 압착 |
| PP Z | VR03 | 단일 곡선 | 180° | 있음 | 부드러운 승강 |
| Swing Z | VR03 | 압착 후 유지 | 72°~288° | 있음 | 분리막 덮기 |

**Table Z만 다른 점**: 유일하게 **사이클 내 홈 복귀가 없는 인덱싱 축**. 다른 모든 축은 1 사이클 = 1 왕복(홈→동작→홈)이지만, Table Z는 1 사이클 = 1피치 누적 전진.

---

## 8) Phase별 동작 요약

| Phase | 마스터 | Axis36 Table Z |
|---|---|---|
| **LC_STACK** | VR04 | **능동** — GET 프로파일 (1피치 인덱싱) |
| **RA_STACK** | VR04 | **능동** — GET 프로파일 (1피치 인덱싱, LC와 동일) |
| LC_RUN / RA_RUN | VR03 | CAMIN 비활성 |

> Cathode 단이든 Anode 단이든 한 단 적층할 때마다 동일하게 한 피치 인덱싱한다.

---

## 9) 참고 자료

- export 파일:
  - `exports/PowerCo_Stack_20260430_R150_Backup/cam_exports/Cam_STACK_TableZ_GET.xml`
  - `exports/PowerCo_Stack_20260430_R150_Backup/cam_exports/Cam_STACK_TableZ_PUT.xml`
- CAMIN FB: `exports/PowerCo_Stack/_root/200_MotionControl/210_CAM/Stack/FB_Camin_STACK_LC_STACK.xml` (그리고 `_RA_STACK`)
- 보간 FB: `exports/PowerCo_Stack/_root/200_MotionControl/210_CAM/FB_Interpolate_Cam.xml`
- 위치 DB: `DB_Global_Cam_Pos.Axis36_StackTableZ_GET_POS` / `_PUT_POS`
- export 스크립트: `scripts/export_tablez_cams.py`
- Mandrel 비교: [`Mandrel_Motion_Profile.md`](Mandrel_Motion_Profile.md)

---

## 10) 문서 정합성 메모

- `VR_축_동작_전체_흐름.md`는 Axis36을 **VR04 슬레이브**로 올바르게 기재함(정본 일치).
- `PowerCo_Stack_CAM_Angle_Sequence.md`는 `STACK_TABLE / TableZ`를 **VR03 종속**으로 기재 — 기구명 기준 분류일 뿐 실제 마스터는 **VR04**다(교정 필요).
