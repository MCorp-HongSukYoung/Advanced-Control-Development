# Winder (Winding / Jelly Roll) — Motion Profile

> 작성: 2026-05-20
> 소스: `FB_WindingMotion`, `FB_WindingSequence`, `FB_CreateCamBasedXYPoints`, `FB_CarculationWindingCamProfile`(FB37), `DB_StackRecipe`
> CAM 데이터: **런타임 계산형** — `FB_CarculationWindingCamProfile`이 JR 치수로 매번 생성 (정적 export 테이블 없음)
> 코드 정본: `exports/PowerCo_Stack_20260430_R150_Backup/.../Winding/*.xml` (XML 직접 검증)
> 관련: [`PP_Motion_Profile.md`](PP_Motion_Profile.md), [`SwingRoller_Motion_Profile.md`](SwingRoller_Motion_Profile.md), [`../OB_CAM/Winder/VR06_Winding_CAM_분석.md`](../OB_CAM/Winder/VR06_Winding_CAM_분석.md)

---

## 0) 한 줄 결론

> **Winder = VR06 마스터를 따라 SepaGripper(X/Z)가 "사각형 JR 코너의 원형 궤적"을 보상 추종하는 런타임 계산형 CAM.**
> 다른 5개 프로파일(PP·Mandrel·Reverse·Swing·DSheet)이 **고정 CAM 테이블**을 쓰는 것과 달리, Winder는 JR 높이·폭으로 **매 사이클 cos/sin 식으로 CAM 포인트를 생성**한다.
> VR06 1회전(360°) = JR 1겹 권취, 1.5회전(540°)이면 360° 시점에서 X2/Z2 CAM으로 **런타임 교체**.

> ⚠️ **분석 주의(중요)**: 이 블록의 자동 `.md` 다이제스트는 `SQRT/SQR/ATAN/COS/SIN` 함수 호출을 **누락**시켜 식을 선형처럼 보이게 만든다. **반드시 `.xml` 원본 또는 본 문서를 정본으로 사용**할 것. (XML 검증 결과 실제 식은 삼각함수 기반)

---

## 1) 하드웨어 구성

| 축 | Axis번호 | 제어 | 역할 |
|---|---|---|---|
| **VR06_WinderLeadingAxis** | 가상 | MoveRelative (360°/+180°) | 권취 마스터 |
| WindingUnit01R | Axis_56 (TB17) | **CamIn (Cam_Run)** + Gear | 권취 맨드릴 회전 1 |
| WindingUnit02R | Axis_57 (TB18) | **Gear** (01R에 동기) | 권취 맨드릴 회전 2 (듀얼 맨드릴) |
| SepaGripper X | Axis_52 (TB11) | **CamIn (Cam_WindingX1/X2)** | 분리막 그리퍼 수평 |
| SepaGripper Z | Axis_53 (TB14) | **CamIn (Cam_WindingZ1/Z2)** | 분리막 그리퍼 수직 |
| Winding Mandrel Y | Axis_54 | 점대점 (Initialize) | 맨드릴 진입/후퇴 |
| Mandrel Clamp Y | Axis_55 | 점대점 (Initialize) | 맨드릴 클램프 |

- **맨드릴(56/57)**: JR 권심 회전 — VR06에 CamIn(Cam_Run)으로 동기, 방향은 SlaveScaling 부호로 결정
- **SepaGripper(52/53)**: 분리막을 잡고 회전하는 사각 JR 면에 밀착되도록 X·Z 보상 이동

---

## 2) CAM 프로파일 목록 — 런타임 생성

| CAM | 슬레이브 | 사용 구간 | 생성원 |
|---|---|---|---|
| `Cam_Run` | Axis56 | 전 구간 | 고정(회전), SlaveScaling ±1.0 |
| `Cam_WindingX1` | Axis52 | 1차 (VR06 0°→360°) | `camProfileX1[0..360]` |
| `Cam_WindingZ1` | Axis53 | 1차 (VR06 0°→360°) | `camProfileZ1[0..360]` |
| `Cam_WindingX2` | Axis52 | 2차 (360°→540°, 540°모드) | `camProfileX2[0..360]` |
| `Cam_WindingZ2` | Axis53 | 2차 (360°→540°, 540°모드) | `camProfileZ2[0..360]` |

생성 파이프라인:
```
FB_WindingMotion
├ FB_CreateCamBasedXYPoints        (시작 시 1회)
│  ├ FB_CarculationWindingCamProfile  → X1/X2/Z1/Z2 [0..360] XY 포인트 수학 계산
│  └ LCamHdl_CreateCamBasedOnXYPoints × 4 → MC_CopyCamData → MC_InterpolateCam (TO_Cam 적재)
└ FB_WindingSequence               (권취 실행 상태기계)
```

> 분리막은 원이 아닌 **사각형 JR**을 감으므로 맨드릴 중심→코너 거리가 각도마다 변한다. SepaGripper는 이 변화를 보상해야 하고, 그 보상 궤적이 곧 X/Z CAM이다.

---

## 3) CAM 커브 — 수학적 정의 (XML 검증)

### 3-0. 사전 계산 (Pre Sequence)

```
Radius = √( (H/2)² + (W/2)² )          ← 맨드릴 중심 → JR 코너 거리 (외접원 반경)
Theta  = atan( (H/2) / (W/2) ) × 180/π ← 코너가 X축과 이루는 각도 [°]
```
- `H = DB_StackRecipe.JR.Height`, `W = DB_StackRecipe.JR.Width`
- ⚠️ `.md` 다이제스트는 이를 `Radius = H/2+W/2`, `Theta = (H/2)/(W/2)×Rad2Deg`로 잘못 표기 → **무시**. XML 정본은 위 삼각함수식.

### 3-1. CW 모드 1차 CAM (X1/Z1), `tempXi = x`(=VR06각)

| 구간 | X1.y | Z1.y |
|---|---|---|
| **0°–180°** | `-R·cos((Theta-x)·D2R) + W/2` | `R·sin((Theta-x)·D2R) - H/2` |
| **181°–270°** | `R·cos((Theta+x)·D2R) + W + W/2 + offset1·(x-180)/180` | `R·sin((Theta+x)·D2R) - H/2` |
| **271°–360°** | `R·cos((x-Theta)·D2R) + W + H + W/2 + offset1·(x-180)/180` | `R·sin((x-Theta)·D2R) - H/2` |

> 구간 경계(180°, 270°)에서 X1·Z1 **연속**(검증). 구간 = "어느 코너가 그리퍼와 접촉 중인가" → 코너 통과 시 cos/sin 원호, 면 통과 시 offset1 선형 보정. 구간 전환마다 X 기준점이 W → W+H로 누적.

### 3-2. 실측 환산 예시 (CW, H=100, W=200, offset1=0)

R = √(50²+100²) = 111.8, Theta = atan(0.5) = 26.57°

| VR06 | X1 [mm] | Z1 [mm] | 비고 |
|---|---|---|---|
| 0° | 0.0 | 0.0 | 시작점 (코너 접촉) |
| 26.6° | −11.8 | −50.0 | X 살짝 후퇴 |
| 90° | 50.0 | −150.0 | |
| 116.6° | 100.0 | **−161.8** | Z 최저 (≈ −(R+H/2)) |
| 180° | 200.0 (=W) | −100.0 | 1면 완료 |
| 243.4° | 300.0 | **−161.8** | Z 2차 최저 |
| 270° | 350.0 | −150.0 | 2면 완료 |
| 360° | **500.0** | −100.0 | 1겹 권취 완료 |

```
X1 [mm] (그리퍼 수평 — 분리막 페이아웃, 단조 증가)
500 ┤                                              ╭─
350 ┤                                   ╭──────────╯
200 ┤                      ╭────────────╯
100 ┤              ╭───────╯
  0 ┤──╮___╭───────╯
    └──┬───┬────────┬────────┬─────────┬─────────┬── VR06[°]
       0  26  90   117      180       270       360

Z1 [mm] (그리퍼 수직 — 사각 코너 회전에 따른 ±진동)
   0 ┤╮                              ╭────╮
 -50 ┤ ╲                            ╱      ╲
-100 ┤  ╲              ╭───────────╯        ╲___╭──
-150 ┤   ╲___╭────────╯                         
-162 ┤      (min @117°)        (min @243°)
    └──┬────────┬──────────┬──────────┬─────────┬── VR06[°]
       0       90         180        270       360
```

> X1은 0 → W(180°) → W+H(270°) → 종단으로 **단조 증가**(분리막을 둘레만큼 풀어줌). Z1은 코너가 상/하로 도는 것을 따라 **−H/2 중심으로 진동**(코너 최원점에서 최저 −161.8mm 2회).
> 실제 값은 레시피 H/W·offset에 따라 달라짐 — 위는 형상 예시.

### 3-3. CCW 모드

`in_windingDirection = TRUE`. CW와 대칭: cos/sin 부호·구간 분할이 0–90–180–270–360 4분할로 바뀌고 X 누적 오프셋이 `+H → +H+H` 식으로 달라진다 (XML §CCW 분기). 형상은 CW의 좌우 반전.

---

## 4) 360° vs 540° — 런타임 CAM 교체

| 항목 | 360° (1회전) | 540° (1.5회전) |
|---|---|---|
| 분리막 길이 | 2W+2H (둘레 1회) | 3W+3H |
| VR06 이동 | MoveRelative 360° | 360° + 180° |
| CAM | X1/Z1만 | X1/Z1 → **360°에서 X2/Z2 교체** |
| ScalingFactor | 2 | 1차 2 → 2차 **5** |

**X2/Z2 2차 SlaveOffset (재동기 기준점)**:
```
statSecondX_SlaveOffset = Servo[52].Position_04 − JR.Width − JR.Height   (Winding End에서 역산)
statSecondZ_SlaveOffset = Servo[53].Position_01            (CW)
                        = Servo[53].Position_01 − JR.Height (CCW)
```
> 360° 시점에 그리퍼가 다른 위치에 있으므로 새 SlaveOffset으로 X2/Z2 CAM 재동기. `ActualCam ≠ statOldCam` 확인으로 교체 완료를 검증 후 ROTATION_SECOND(추가 180°) 진행.

---

## 5) CamIn 파라미터 (FB_WindingSequence, XML 검증)

| 슬레이브 | CAM | SlaveOffset | Scaling | MasterSync | SyncDir / Ref |
|---|---|---|---|---|---|
| Axis56 (맨드릴) | Cam_Run | Axis56.Position | **SlaveScaling ±1.0** (Dir TRUE=+1 / FALSE=−1) | 0.01 | 2 / 3 |
| Axis52 (X) 1차 | Cam_WindingX1 | Axis52.Position | **ScalingFactor 2** | 0.0 | 2 / 3 |
| Axis53 (Z) 1차 | Cam_WindingZ1 | Axis53.Position | **ScalingFactor 2** | 0.0 | 2 / 3 |
| Axis52 (X) 2차 | Cam_WindingX2 | statSecondX_SlaveOffset | **ScalingFactor 5** | 0.01 | 2 / 3 |
| Axis53 (Z) 2차 | Cam_WindingZ2 | statSecondZ_SlaveOffset | **ScalingFactor 5** | 0.01 | 2 / 3 |

- `SlaveOffset = 축 현재 위치` → CamIn 진입 시 점프 없는 동기 (분리막 끊김 방지)
- 속도: `DB_StackRecipe.Servo[56].Velocity_01`
- `in_windingDirection`(0=CW/1=CCW) 규약과 `WindingDirection` 비트 매핑은 명칭이 엇갈리므로 §9 요확인

---

## 6) FB_WindingSequence 상태 흐름 (요약)

```
STATUS_CHECK   PowerOn·Home·Inpos·GearIn·맨드릴클램프 확인
               + X 이동거리 충분성: Position_04−Position_03 > 2W+2H(360°)/3W+3H(540°)
VRAXIS_HOME    MC_HOME(VR06, mode 7)
GEARIN_WINDING MC_GEARIN(맨드릴) → cam:=CAM_FIRST
CAMIN_FIRST    Cam_Run + Cam_WindingX1/Z1 CamIn → 전부 InSync
ROTATION_FIRST MC_MoveRelative(VR06, 360°)
               ├ 360°모드 → CAMOUT
               └ 540°모드 → PrepareSection → CAMIN_SECOND
CAMIN_SECOND   Cam_WindingX2/Z2 (ScalingFactor 5, 2차 Offset) → ActualCam 교체 확인   [540°]
ROTATION_SECOND MC_MoveRelative(VR06, 180°)                                         [540°]
CAMOUT         VR06/Axis56/52/53 MC_HALT → statusWord 0x000F → done
HALT(에러)     전축 MC_HALT
```

> 사전 자세: `FB_WindingInitialize_Sequence` — MandrelClampY/MandrelY PUT → 클램프 Extend → Axis56 GET → Axis53 STANDBY → Axis52 WINDING_START 순.

---

## 7) 기존 5개 프로파일과 비교

| 항목 | **Winder** | PP / Mandrel / Reverse / Swing | DSheet |
|---|---|---|---|
| 마스터축 | **VR06** | VR03 | VR01 / VR02 |
| CAM 성격 | **런타임 계산 (cos/sin)** | 정적 테이블 (export XML) | 정적 테이블 (export XML) |
| 입력 의존 | JR.Height/Width/Direction/offset | 없음 (고정 커브) | 없음 (고정 커브) |
| 동기 축 | Cam(56)+Gear(57) + SepaGripper X/Z | 2축 (±GEARIN) | 3축 R/X/Z |
| 사이클 | 360° 또는 540° (런타임 CAM 교체) | 360° 고정 | 360° 고정 |
| Scaling | ±1.0(회전) / FactorFactor 2→5 | 동적 SlaveOffset/Scaling | 동적 SlaveOffset/Scaling |
| 곡선 형상 | X 단조증가 + Z 진동 (사각 코너 추종) | S-커브 다이브/스윕 | R turn + X 보상 + Z 다이브 |

> Winder만 **프로파일이 데이터(JR 치수)에 의존**한다 — 정적 테이블 5종과 근본적으로 다른 부류. 따라서 "실측 커브"가 아니라 "**생성식**"이 분석 대상.

---

## 8) 핵심 포인트

1. **사각 코너의 원형 궤적 보상** — JR이 사각이라 중심→코너 거리가 각도마다 변함. X/Z CAM이 이를 cos/sin으로 사전 계산해 그리퍼를 면에 밀착시킴.
2. **X 단조 증가 = 분리막 페이아웃** — 1겹 둘레(2W+2H)만큼 X가 풀려나감. STATUS_CHECK에서 X 가용 행정이 부족하면 시작 전 에러.
3. **CW/CCW = 회전 SlaveScaling 부호 + 그리퍼 식 분기** — Cam_Run ±1.0, SepaGripper는 cos/sin 부호·구간 분할이 달라짐.
4. **540°는 런타임 CAM 교체가 핵심** — 360°에서 X2/Z2로 새 SlaveOffset·ScalingFactor(5) 재동기.
5. **SlaveOffset = 현재 위치** — CamIn 점프 방지 (분리막 보호).

---

## 9) 미확인 항목

| 항목 | 상태 |
|---|---|
| Radius=√·, Theta=atan, X/Z=cos/sin 식 | ✅ **XML 검증 완료** (`.md` 다이제스트는 오표기) |
| CamIn 파라미터 (Scaling ±1/2/5, Offset 식) | ✅ **확인 완료** (FB_WindingSequence) |
| 360°/540° CAM 교체·MoveRelative 거리 | ✅ **확인 완료** |
| 실제 JR.Height/Width/offset1/offset2/magnification 값 | ❌ `DB_StackRecipe.JR` / Winding 레시피 확인 필요 |
| `in_windingDirection`(0=CW) vs `WindingDirection` 비트 매핑 | ⚠️ 명칭 엇갈림 — 실기/레시피로 CW·CCW 확정 필요 |
| `in_windingRevolution` 미사용 (인터페이스만 존재) | ⚠️ 데드 파라미터 — 향후 확장/외부참조 여부 확인 |
| magnification 동작 (구간 조건 `≤180/mag` 축소) | ⚠️ 의도 확인 필요 (포인트 밀도 vs 각도 확대) |
| 런타임 적재된 실제 CAM 포인트 (DB_WindingCamX1..) | ❌ 오프라인 Openness로는 확인 불가 — 실기 DB 캡처 또는 FB_HMIMonitoring_ReadCamProfile 필요 |
| 블록명 오타 `Carculation` → `Calculation` | ℹ️ 참고 |
