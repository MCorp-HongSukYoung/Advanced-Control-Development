````md
# FB_Camin_Unwinder

## 블록 기본 정보

| 항목 | 내용 |
|---|---|
| 타입 | FB (Function Block) |
| 이름 | FB_Camin_Unwinder |
| Unit | `_root (200_MotionControl/210_CAM/Unwinder/)` |
| 언어 | LAD (선언부), 실제 로직은 SCL |
| 번호 | FB8030 |

---

# 한 줄 요약

세퍼레이터 Unwinder 슬레이브 축(`Axis01_SepaUWR_TB107`)을  
스택 리딩 마스터 축(`VR03_StackLeadingAxis`)과 CAM 테이블(`Unwinder`) 기반으로 동기화(CamIn) 및 해제(CamOut)하는 래퍼 FB이다.

---

# 주요 인터페이스

## Static 변수

| 이름 | 타입 | 설명 |
|---|---|---|
| `CAMIN_Cam_Unwinder` | MC_CAMIN (V9.0) | Master / Slave CAM 동기 진입 |
| `CAMOUT_Cam_Unwinder` | MC_CAMOUT | CAM 동기 해제 |

---

## 특징

- Input / Output / Temp 영역 없음
- 모든 데이터는 Global DB 기반 참조
- 실제 상태값은 `DB_GdbCam` 및 `DB_Global_Cam_Control`에 저장

---

# 네트워크별 로직

---

# Network 1 — Empty Network

구분자 역할만 수행한다.

실행 로직 없음.

---

# Network 2 — CAMOUT Execute

## SCL

```scl
DB_GdbCam.STACK_SEPA.Cam_Unwinder.Camout.Execute :=
    DB_Global_Cam_Control.Unwinder_CAMOUT;
````

## 설명

글로벌 CAM 제어 DB의 `Unwinder_CAMOUT` 신호를
CamOut Execute 신호로 전달한다.

---

# Network 3 — CAMOUT

## SCL

```scl
CAMOUT_Cam_Unwinder(
    Slave             := Axis01_SepaUWR_TB107,
    Execute           := DB_GdbCam.STACK_SEPA.Cam_Unwinder.Camout.Execute,
    SyncOutDirection  := 5,
    StartSyncOut      => ...Camout.StartSyncOut,
    Done              => ...Camout.Done,
    Busy              => ...Camout.Busy,
    CommandAborted    => ...Camout.CommandAborted,
    Error             => ...Camout.Error,
    ErrorId           => ...Camout.ErrorId
);
```

## 설명

`MC_CamOut`을 호출하여 슬레이브 축의 CAM 동기를 해제한다.

### 주요 설정

| 항목                 | 값   | 의미                             |
| ------------------ | --- | ------------------------------ |
| `SyncOutDirection` | `5` | Shortest Way with Deceleration |

---

# Network 4 — Execute

## SCL

```scl
DB_GdbCam.STACK_SEPA.Cam_Unwinder.CamIn.Execute :=
    DB_Global_Cam_Control.STACK_LC_RUN_CAMIN OR
    DB_Global_Cam_Control.STACK_RA_RUN_CAMIN;
```

## 설명

다음 중 하나라도 활성화되면 CamIn 실행:

* LC(Cathode) Run
* RA(Anode) Run

즉, Unwinder 축은 양 방향 공정에서 공용 사용된다.

---

# Network 5 — MasterOffset

## SCL

```scl
DB_GdbCam.STACK_SEPA.Cam_Unwinder.CamIn.MasterOffset := 1.0;
```

## 설명

Master Offset을 1.0으로 고정한다.

---

# Network 6 — SlaveOffset

## SCL

```scl
DB_GdbCam.STACK_SEPA.Cam_Unwinder.CamIn.SlaveOffset :=
    DB_GdbCam.STACK_SEPA.Cam_Unwinder.CamData.SlaveOffset;
```

## 설명

슬레이브 오프셋을 `CamData`에서 읽어 적용한다.

런타임 중 수정 가능하다.

---

# Network 7 — MasterScaling

## SCL

```scl
DB_GdbCam.STACK_SEPA.Cam_Unwinder.CamIn.MasterScaling := 1.0;
```

## 설명

마스터 축 스케일링을 1.0으로 고정한다.

즉:

* Offset 없음
* Scaling 없음
* 1:1 기준 동작

---

# Network 8 — SlaveScaling

## SCL

```scl
DB_GdbCam.STACK_SEPA.Cam_Unwinder.CamIn.SlaveScaling :=
    DB_GdbCam.STACK_SEPA.Cam_Unwinder.CamData.SlaveScaling;
```

## 설명

슬레이브 스케일링 값을 `CamData`에서 읽어 적용한다.

---

# Network 9 — CAMIN (핵심 네트워크)

## SCL

```scl
CAMIN_Cam_Unwinder(
    Master               := VR03_StackLeadingAxis,
    Slave                := Axis01_SepaUWR_TB107,
    Cam                  := Unwinder,
    Execute              := ...CamIn.Execute,
    MasterOffset         := ...CamIn.MasterOffset,
    SlaveOffset          := ...CamIn.SlaveOffset,
    MasterScaling        := ...CamIn.MasterScaling,
    SlaveScaling         := ...CamIn.SlaveScaling,
    MasterSyncPosition   := 0.01,
    SyncDirection        := 3,
    ApplicationMode      := 0,
    SyncProfileReference := 2,
    StartSync            => ...CamIn.StartSync,
    InSync               => ...CamIn.InSync,
    Busy                 => ...CamIn.Busy,
    CommandAborted       => ...CamIn.CommandAborted,
    Error                => ...CamIn.Error,
    ErrorId              => ...CamIn.ErrorId,
    EndOfProfile         => ...CamIn.EndOfProfile
);
```

---

## 동작 설명

마스터 축:

```text
VR03_StackLeadingAxis
```

슬레이브 축:

```text
Axis01_SepaUWR_TB107
```

마스터 축이 `0.01°` 위치에 도달하면
슬레이브 축이 `Unwinder` CAM Profile을 따라 동기 추종을 시작한다.

---

## 주요 파라미터

| 항목                     | 값      | 의미             |
| ---------------------- | ------ | -------------- |
| `MasterSyncPosition`   | `0.01` | 거의 0°에서 동기 시작  |
| `SyncDirection`        | `3`    | Shortest Way   |
| `ApplicationMode`      | `0`    | Cyclic         |
| `SyncProfileReference` | `2`    | CAM Profile 기준 |

---

# Network 10 — Empty Network

구분자 역할만 수행한다.

---

# Network 11 — Error

## SCL

```scl
DB_Global_Cam_Control.Unwinder_ERROR :=
    DB_GdbCam.STACK_SEPA.Cam_Unwinder.CamIn.Error;
```

## 설명

CamIn Error 상태를 글로벌 DB에 전달한다.

---

# Network 12 — InSync

## SCL

```scl
DB_Global_Cam_Control.Unwinder_InSync :=
    DB_GdbCam.STACK_SEPA.Cam_Unwinder.CamIn.InSync;
```

## 설명

CAM 동기 완료 상태를 글로벌 DB에 전달한다.

---

# Network 13 — Empty Network

마지막 구분자 역할.

---

# 데이터 흐름 요약

```text
DB_Global_Cam_Control
──────────────────────────────

Unwinder_CAMOUT
    └──► CAMOUT Execute

STACK_LC_RUN_CAMIN
STACK_RA_RUN_CAMIN
    └──► CamIn.Execute

──────────────────────────────

Master Axis
    VR03_StackLeadingAxis

Slave Axis
    Axis01_SepaUWR_TB107

──────────────────────────────

DB_GdbCam.STACK_SEPA.Cam_Unwinder

CamData.SlaveOffset
    └──► CamIn.SlaveOffset

CamData.SlaveScaling
    └──► CamIn.SlaveScaling

CamIn.Error
    └──► Unwinder_ERROR

CamIn.InSync
    └──► Unwinder_InSync
```

---

# 특이점 및 주의사항

# 1. LC / RA 공용 Execute 구조

```scl
STACK_LC_RUN_CAMIN OR STACK_RA_RUN_CAMIN
```

구조로 인해:

* LC 방향
* RA 방향

중 하나라도 활성화되면 CAM 동기가 유지된다.

---

# 2. MasterSyncPosition = 0.01

매 사이클 초입에서 즉시 동기 진입한다.

사실상:

```text
0° 근처에서 즉시 CAM Engage
```

의 의미이다.

---

# 3. MasterOffset / MasterScaling 고정

```scl
MasterOffset  := 1.0
MasterScaling := 1.0
```

마스터 측 보정은 수행하지 않는다.

---

# 4. SlaveOffset / SlaveScaling 동적 적용

```scl
CamData.SlaveOffset
CamData.SlaveScaling
```

값을 런타임 중 변경하면 즉시 반영된다.

---

# 5. SyncDirection = 3 (ShortestWay)

동기 진입 시 슬레이브 축이:

```text
최단 거리 방향
```

으로 이동한다.

초기 위치 차이가 크면 급격한 보정이 발생할 수 있다.

---

# 6. FB8030 번호 체계

8000번대 FB는 일반적으로:

* 라이브러리 영역
* Motion Utility 영역

에서 사용되는 경우가 많다.

본 블록은 표준 Motion FB 위에 구성된 프로젝트 전용 Wrapper FB로 추정된다.

```
```