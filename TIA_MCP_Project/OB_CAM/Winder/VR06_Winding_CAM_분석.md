# Winding CAM 상세 분석 (VR06 기준)

## 한 줄 결론
> VR06 1회전(360°) 또는 1.5회전(540°) = 사각형 JR 1개 권취 완료.  
> SepaGripper X/Z는 사각형 코너가 회전할 때 생기는 불규칙 궤적을 보상하는 CAM을 따라 움직인다.

---

## 전체 블록 구조

```
FB_WindingMotion  (최상위 래퍼, SCL)
├── FB_CreateCamBasedXYPoints   ← CAM 디스크 생성 (시작 시 1회만 실행)
│   ├── FB_CarculationWindingCamProfile  ← XY 좌표 수학적 계산 (FB37, SCL)
│   └── LCamHdl_CreateCamBasedOnXYPoints × 4  ← TO_Cam 오브젝트에 포인트 로드
│       └── MC_CopyCamData → MC_InterpolateCam (Siemens 표준 라이브러리)
└── FB_WindingSequence          ← 권취 실행 시퀀스 (매 사이클, SCL)
    └── FC_LMC_StateTransition  ← mPlus 상태 전환 유틸

보조:
  FB_WindingInitialize_Sequence ← 시퀀스 진입 전 초기 자세 세팅
  FB_HMIMonitoring_ReadCamProfile ← HMI에 CAM 프로파일 시각화 스트리밍
```

---

## 관련 Axis와 CAM 테이블

| Axis | 번호 | 제어 방식 | 역할 |
|------|------|----------|------|
| VR06_WinderLeadingAxis | 가상 | MoveRelative | 권취 마스터 (0°→360° 또는 →540°) |
| Axis56_WindingUnit01R_TB17 | Axis56 | **GearIn + CamIn** | 권취 맨드릴 회전축 1 |
| Axis57_WindingUnit02R_TB18 | Axis57 | GearIn | 권취 맨드릴 회전축 2 (동기 보조) |
| Axis52_SepaGripperX_TB11 | Axis52 | **CamIn** | 분리막 그리퍼 X축 (수평 이동) |
| Axis53_SepaGripperZ_TB14 | Axis53 | **CamIn** | 분리막 그리퍼 Z축 (수직 이동) |

| CAM 이름 | 슬레이브 | 사용 구간 |
|---------|---------|---------|
| `Cam_Run` | Axis56 | 전 구간. WindingDirection에 따라 SlaveScaling=+1.0(CW) 또는 -1.0(CCW) |
| `Cam_WindingX1` | Axis52 | 1차 구간 (VR06 0°→360°) |
| `Cam_WindingZ1` | Axis53 | 1차 구간 (VR06 0°→360°) |
| `Cam_WindingX2` | Axis52 | 2차 구간 (VR06 360°→540°, 540° 모드 전용) |
| `Cam_WindingZ2` | Axis53 | 2차 구간 (VR06 360°→540°, 540° 모드 전용) |

---

## CAM 프로파일 물리적 의미

### 왜 CAM이 필요한가?

```
  JR 단면 (사각형)
  ┌─────────── W ───────────┐
  │                         │  ← 이 코너가 회전하면서
  H       맨드릴             │     SepaGripper가 닿는 지점이
  │                         │     원이 아닌 사각형 경로를 따름
  └─────────────────────────┘

  맨드릴이 일정 속도로 회전해도
  코너까지의 거리가 각도마다 달라짐
    → 그리퍼가 X/Z로 보상 이동 필요
    → 이 보상 궤적이 CAM 프로파일
```

### 핵심 사전 계산 (Pre Sequence)

```
Radius = √((H/2)² + (W/2)²)        // 맨드릴 중심 → 코너까지 거리
Theta  = ATAN(H/2 / W/2) × Rad2Deg // 코너 방향각 [°]
tempXi = tempi × magnification      // CAM 인덱스 스케일 (보통 magnification=1)
```

### CW 모드 구간별 공식 (in_windingDirection = FALSE)

```
구간 1: tempi = 0 ~ 180  (VR06 0°~180°)
  ← 초기 코너에서 첫 번째 면(Width 면)을 지나는 구간

  X1[i].y = -Radius × COS((Theta - tempXi) × Deg2Rad) + W/2
  Z1[i].y =  Radius × SIN((Theta - tempXi) × Deg2Rad) - H/2

구간 2: tempi = 181 ~ 270  (VR06 180°~270°)
  ← 두 번째 면(Height 면)을 지나는 구간. X에 W만큼 오프셋 추가

  X1[i].y = Radius × COS((Theta + tempXi) × Deg2Rad) + W + W/2
              + offset1 × (tempXi - 180) / 180
  Z1[i].y = Radius × SIN((Theta + tempXi) × Deg2Rad) - H/2

구간 3: tempi = 271 ~ 360  (VR06 270°~360°)
  ← 세 번째 면(Width 면 반대)을 지나고 시작점으로 복귀하는 구간

  X1[i].y = Radius × COS((tempXi - Theta) × Deg2Rad) + W + H + W/2
              + offset1 × (tempXi - 180) / 180
  Z1[i].y = ...
```

**offset1**: 면 중간 구간에서 그리퍼가 JR 면을 따라 선형으로 보정하는 값.  
**magnification**: CAM 포인트 밀도 배율 (1이면 1°당 1포인트).

### CW 모드 공식 유도 — 왜 저렇게 나오는가?

**0단계 — 기본 세팅**

```
JR 단면을 위에서 봤을 때:

         Z↑
          │   ← 이 코너가 Radius 거리에 있음
    ┌─────┼─────┐
    │     │  H/2│
    │  JR │     │
  ──┼─────┼─────┼──→ X
    │     │  H/2│
    └─────┼─────┘
         W/2  W/2

Radius = √((W/2)² + (H/2)²)  ← 중심→코너 거리
Theta  = ATAN(H/2 / W/2)      ← 코너가 X축과 이루는 각도
```

**1단계 — 코너가 회전하면 어디에 있나?**

맨드릴이 CW로 α° 회전하면, 오른쪽 위 코너 위치:

```
코너 X = Radius × COS(Theta - α)
코너 Z = Radius × SIN(Theta - α)

α=0°  : COS(Theta) = W/2/Radius → X = W/2  (시작점)
α=90° : 코너가 오른쪽 아래로 이동
α=180°: 코너가 왼쪽 아래로 이동
```

그리퍼는 이 코너를 따라가야 하므로, α=0일 때 기준점(0)이 되도록 보정:

```
X1.y = -Radius × COS(Theta - α) + W/2    ← α=0이면 -W/2+W/2 = 0 ✓
Z1.y =  Radius × SIN(Theta - α) - H/2    ← α=0이면  H/2-H/2 = 0 ✓
```

이것이 구간 1 (0~180°) 공식.

**2단계 — 왜 구간이 3개인가?**

```
CW로 계속 돌면 접촉 코너가 바뀜:

0°~180°:   첫 코너 (오른쪽 위→아래) → Width 면 통과
181°~270°: 두 번째 코너 (왼쪽 아래) → Height 면 통과
271°~360°: 세 번째 코너 (왼쪽 위)  → Width 면 통과 후 복귀
```

코너가 바뀔 때마다 X 기준 오프셋이 누적 증가:

```
구간 1 (0~180°):   X 오프셋 +W/2       ← 첫 코너 기준
구간 2 (181~270°): X 오프셋 +W/2 + W   ← Width 면만큼 추가
구간 3 (271~360°): X 오프셋 +W/2 + W+H ← Height 면까지 추가
```

**3단계 — 전체 X 이동 형상**

```
X 위치
  ↑
W+H─┤               ╭─────╮         ← 구간3 정점 (세 번째 코너)
    │              /       \
W/2─┤    ╭────────╯         \        ← 구간2 (Height 면 이동)
    │    │                   \   ╭── ← 원점 복귀
  0─┤────╯                    ╰──╯
    └──────────────────────────────→ VR06 각도
    0°      90°    180°    270°   360°
         구간1       구간2    구간3
```

**한 줄 요약**

> 각 구간 = "어떤 코너가 그리퍼와 접촉 중인가"  
> 코너 통과 시 → cos/sin 곡선 (원호 추종)  
> 평면 통과 시 → 선형 이동 (offset1로 보정)  
> 구간 전환 시마다 X 기준점이 W 또는 H만큼 누적 증가

### CAM 프로파일 형상 (개념도, CW 기준)

```
SepaGripper X 위치
  ↑
W+H─┤                   ╭─────╮
    │                  /       \
W/2─┤         ╭───────╯         \       ╭─
    │         │                  \     /
  0─┤─────────╯                   ╰───╯
    └──────────────────────────────────→ VR06 각도
    0°       90°      180°     270°    360°

SepaGripper Z 위치
  ↑
  0─┤─────╮                          ╭──
    │      \                        /
-H/2┤       ╰──────────────────────╯
    └──────────────────────────────────→ VR06 각도
    0°       90°      180°     270°    360°
```

---

## VR06 각도 → 실제 동작 대응

| VR06 각도 | Axis56 (WindingR) | Axis52 (SepaGripperX) | Axis53 (SepaGripperZ) |
|---------|-----------------|---------------------|---------------------|
| **0°** | 기어인 + CamIn 진입 | X1 기준점 (SlaveOffset = 현재 위치) | Z1 기준점 |
| **0°~180°** | VR06와 비율 동기 회전 | JR Width 면 추종: X 소폭 변동 | JR 코너 회전: Z 하강 |
| **~180°** | 계속 회전 | X 최대값 도달 (≈W/2 + Radius) | Z 최저점 (≈-H/2) |
| **180°~270°** | 계속 회전 | 두 번째 면 추종: X 점차 감소 | Z 다시 상승 |
| **270°~360°** | 계속 회전 | 세 번째 면 추종: X 감소 후 복귀 | Z 기준점 복귀 |
| **360°** | [360° 모드] GearOut + Halt | CamOut | CamOut |

---

## 360° vs 540° — 물리적 차이

### 왜 540°(1.5회전)가 필요한가?

```
JR 권취 방식에 따라 필요한 분리막 길이가 달라짐:

[360° 권취 — 1회전]
  맨드릴이 1바퀴 돌면서 사각형 JR 외형을 1회 감음
  → 분리막 길이 = 2W + 2H (사각형 둘레 1회)

[540° 권취 — 1.5회전]
  맨드릴이 1.5바퀴 돌면서 추가 감기
  → 분리막이 JR을 1회 + 절반 더 감음
  → 더 두꺼운 JR, 더 많은 레이어가 필요한 경우 사용
  → 필요 X 이동 거리 = 3W + 3H (STATUS_CHECK에서 사전 검증)
```

### 540° 모드에서 CAM이 교체되는 이유

```
VR06 360° 시점에서:
  - SepaGripperX는 시작점(X1[0])으로 돌아왔어야 하나
  - JR은 아직 회전 중 → 그리퍼가 새 위치에서 다시 시작해야 함
  - 새로운 기준점(SlaveOffset2)으로 CAM 재동기 필요

SlaveOffset2(X) = Position_04 - JR.Width - JR.Height
  ← Winding End 위치(Position_04)에서 역산한 2차 시작점
SlaveOffset2(Z, CCW) = Position_01 - JR.Height
SlaveOffset2(Z, CW)  = Position_01

PrepareSection 트리거 → X2, Z2 프로파일로 교체
→ ActualCam 변경 확인 → ROTATION_SECOND (VR06 추가 180°)
```

---

## FB_WindingSequence 상태 흐름 (상세)

```
STATE_STATUS_CHECK
  ① Power ON 확인
     Axis56/57/52/53 StatusWord.X0 AND DB_Monitoring.VR06_PowerOn
  ② Home 확인
     Axis56/57/52/53 StatusWord.X5
  ③ 위치 확인
     - Axis56: DB_Servo_Inpos[2] (GET 위치)
     - Axis52: DB_Servo_Inpos[3] (Winding Start 위치)
     - Axis53: DB_Servo_Inpos[4] (Winding 위치)
     - X 이동 거리 충분성:
       Position_04 - Position_03 > statX_MoveDistanceCalc
       (360°: 2W+2H, 540°: 3W+3H)
  ④ GearIn 확인: DB_Global_Servo.Gearin_WindingUnit_R
  ⑤ 맨드릴 클램프 확인:
     Mandrel_Clamp.Detect_Extend AND JR_Mandrel_Clamp.Detect_Extend
  NG 하나라도 → error + STATE_HALT

STATE_VRAXIS_HOME
  MC_HOME(VR06, HomingMode=7) → Done → 다음 / Error → STATE_HALT

STATE_GEARIN_WINDING
  이미 GearIn? → cam:=CAM_FIRST, 즉시 CAMIN_FIRST로
  아니면 MC_GEARIN → InGear → cam:=CAM_FIRST
  Error → STATUS_GEARIN_ERROR + STATE_HALT

STATE_CAMIN_FIRST  [cam = CAM_FIRST]
  MC_CamIn(VR06, Axis56, Cam_Run)
    SlaveScaling: +1.0(CW) / -1.0(CCW)
    MasterSyncPos: 0.01, SyncDirection: 2, SyncProfileRef: 3
    SlaveOffset: Axis56.Position (현재 실제 위치 기준)
  MC_CamIn(VR06, Axis52, Cam_WindingX1)
    SlaveOffset: Axis52.Position, ScalingFactor: 2
  MC_CamIn(VR06, Axis53, Cam_WindingZ1)
    SlaveOffset: Axis53.Position, ScalingFactor: 2
  모두 InSync → statOldCam_X/Z 저장 → 다음

STATE_ROTATION_FIRST
  MC_MoveRelative(VR06, Distance=360°, Velocity=recipe)
  [360° 모드] Done → STATE_CAMOUT
  [540° 모드] PrepareSection 트리거 → cam:=CAM_SECOND → CAMIN_SECOND
  Error → STATE_HALT

STATE_CAMIN_SECOND  [540°만]
  MC_CamIn(VR06, Axis52, Cam_WindingX2)
    SlaveOffset = Position_04 - JR.Width - JR.Height, ScalingFactor: 5
  MC_CamIn(VR06, Axis53, Cam_WindingZ2)
    SlaveOffset(CCW) = Position_01 - JR.Height, ScalingFactor: 5
  ActualCam ≠ statOldCam → CAM 교체 확인 → 다음

STATE_ROTATION_SECOND  [540°만]
  MC_MoveRelative(VR06, Distance=180°, Velocity=recipe)
  Done → STATE_CAMOUT

STATE_CAMOUT
  VR06: MC_HALT
  Axis56: MC_HALT (CamIn InSync=FALSE 대기)
  Axis52/53: MC_HALT
  statusWord 비트 조합 = 0x000F → done=TRUE

STATE_HALT (에러)
  전 축 MC_HALT (statHaltExecute_All)
  0x0037 = 전 축 Done → done=TRUE / X15 에러 비트 → error=TRUE
```

---

## CAM 생성 흐름 (FB_CreateCamBasedXYPoints, 시작 시 1회)

```
createTrigger ↑ → Step=10

Step 10: FB_CarculationWindingCamProfile 호출
  Input:  JR.Height, JR.Width, WindingDirection, WindingRevolution
          offset1, offset2, magnification
  Output: camProfileX1[0..360], camProfileX2[0..360]
          camProfileZ1[0..360], camProfileZ2[0..360]
          (각 포인트: {x: 마스터각도[°], y: 슬레이브변위[mm]})

Step 20: LCamHdl_CreateCamBasedOnXYPoints 4개 Execute ON (병렬)
  IDLE → FIRST_CYCLE → RESET_CAM (에러 있을 때만)
       → COPY_POINTS → COPY_POINTS_BUSY (MC_CopyCamData)
       → INTERPOLATE_CAM (MC_InterpolateCam)
       → DONE

Step 30: 4개 모두 done → createCompleted = 0x000F → done=TRUE
  이후 FB_WindingSequence에서 TO_Cam 오브젝트 직접 참조
```

---

## FB_WindingInitialize_Sequence (사전 자세 세팅 순서)

```
① MandrelClampY (Axis55) + MandrelY (Axis54)
    → PUT 위치 이동 (Command_Interlock 확인 → Command_bits[PUT_POS] SET)
    → Inpos[PUT_POS] AND Command_bits=FALSE 대기

② JR_Mandrel_Clamp + Mandrel_Clamp (실린더)
    → Sequence_Command_Extend = TRUE
    → Detect_Extend 감지 대기
    → Interlock NG → error

③ Axis56 (WindingUnit01R)
    → GET 위치 이동 (Command_bits[GET_POS])
    → Inpos[GET_POS] 대기

④ Axis53 (SepaGripperZ)
    → STANDBY 위치 이동 (Command_bits[STANDBY_POS])
    → Inpos[STANDBY_POS] 대기

⑤ Axis52 (SepaGripperX)
    → WINDING_START 위치 이동 (Command_bits[WINDING_START_POS])
    → Inpos[WINDING_START_POS] 대기 → done=TRUE
```

---

## 핵심 포인트 5가지

1. **SepaGripper는 사각형 코너의 원형 궤적을 보상**
   JR이 원형이 아닌 사각형이므로 맨드릴 중심→코너 거리가 각도마다 변함.
   X1/Z1 CAM은 이 변화를 cos/sin 함수로 사전 계산하여 그리퍼가 항상 JR 면에 밀착되도록 함.

2. **CW와 CCW는 SlaveScaling 부호만 다름**
   Axis56 CamIn의 `SlaveScaling = +1.0(CW) / -1.0(CCW)`.
   SepaGripper의 SlaveOffset은 방향에 따라 Z 기준점이 달라짐 (Position_01 vs Position_01 - JR.Height).

3. **540° 모드에서 CAM 런타임 교체가 핵심**
   VR06 360° 시점에 SepaGripper가 다른 위치에 있으므로 새 SlaveOffset으로 X2/Z2 CAM을 재동기.
   ActualCam 변경을 확인하여 교체 완료를 검증. ScalingFactor도 2→5로 변경됨.

4. **SlaveOffset = 실축 현재 위치 → 충격 없는 진입**
   CamIn 진입 시 항상 `SlaveOffset := AxisXX.Position`으로 동기화.
   이를 생략하면 CamIn 순간 슬레이브가 급격히 이동하여 분리막 끊김 위험.

5. **statX_MoveDistanceCalc = 위치 충분성 사전 검증**
   STATUS_CHECK에서 `Position_04 - Position_03 > 2W+2H(360°) 또는 3W+3H(540°)` 확인.
   SepaGripper X 이동 가능 범위가 분리막 공급 거리보다 짧으면 권취 불가 → 시작 전 에러.
