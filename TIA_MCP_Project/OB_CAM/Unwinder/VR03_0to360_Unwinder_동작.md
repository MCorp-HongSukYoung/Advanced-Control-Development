# VR03 0°→360° — Unwinder (SepaUWR / Axis01) 동작 분석

## 한 줄 결론
> VR03 1회전(0°→360°) = 분리막 1단 공급 완료.  
> LC 적재(STACK_LC_RUN_CAMIN) / RA 적재(STACK_RA_RUN_CAMIN) 공통으로 하나의 Unwinder CAM이 구동됨.

---

## 전체 구조 다이어그램

```
VR03  0°                  180°              230°        320°       360°
      │<────────── CAM 동기 구간 ──────────>│            │          │
      │  Unwinder CamIn (분리막 공급)       │ 감속/대기  │ 재위치   │
      │                                    │            │          │
      ├── CamIn Execute ON ─────────────────┤CamOut──────┤MoveRel───┤

Axis01_SepaUWR_TB107 (분리막 언와인더 — CAM 슬레이브)
  Master: VR03_StackLeadingAxis
  CAM DB: Unwinder (MC_InterpolateCam으로 런타임 로드)
  SlaveScaling: (JR.Width / 360°) × (1 + 0.01 × Dancer_Angle_Correction)
```

---

## CAM 커플링 파라미터

| 파라미터               | 값                              | 의미                                        |
|----------------------|---------------------------------|---------------------------------------------|
| Master               | VR03_StackLeadingAxis           | 가상 마스터 (0°=사이클 시작)                |
| Slave                | Axis01_SepaUWR_TB107            | 분리막 언와인더 실축                        |
| CAM DB               | Unwinder                        | MC_InterpolateCam으로 런타임 로드           |
| MasterSyncPosition   | 0.01°                           | 마스터 0°에서 즉시 동기화                   |
| SyncDirection        | 3                               | 양방향 동기화                               |
| ApplicationMode      | 0                               | 절대 모드 (슬레이브 위치 직접 지정)         |
| SyncProfileReference | 2                               | 슬레이브 기준 동기 (슬레이브 현재 속도 기반)|
| MasterScaling        | 1.0 (고정)                      | 마스터 스케일 불변                          |
| SlaveScaling         | 동적 계산 (아래 공식 참조)       | 권취 직경 변화에 따라 매 사이클 갱신        |
| MasterOffset         | 0 (고정)                        | 마스터 오프셋 없음                          |

---

## 핵심 계산 공식 (FB_Unwinder_Sequence_Judgment)

```
1_degree_Transfer_rate = Diameter × 2 × π / 360
    → 1° 당 분리막 이송 거리 [mm/°]

Transfer_distance = JR.Width / 1_degree_Transfer_rate × (1 + 0.01 × Dancer_Angle)
    → 1사이클 동안 이송해야 할 총 분리막 길이 [°]
    → Dancer 텐션 보정 포함

Unwinder_Velocity = Transfer_distance / (PPMovingTime + MandrelMovingTime)
    → CamIn 전 속도 매칭용 (Step 200에서 MC_MOVEVELOCITY로 사전 투입)
```

> **SlaveScaling = Transfer_distance / 360**  
> VR03가 1회전(360°)하는 동안 슬레이브가 이동할 총 각도를 비율로 환산

---

## VR03 각도 → Unwinder 동작 대응표

| VR03 각도    | Unwinder 상태              | 주요 동작                                              |
|------------|--------------------------|------------------------------------------------------|
| **0°**     | CamIn 동기화 완료          | VR03가 MasterSyncPosition(0.01°) 통과 → InSync=TRUE  |
| **0°~180°**| CAM 동기 구간 (분리막 공급) | VR03 회전에 비례하여 Axis01 전진<br>SlaveScaling으로 직경 보정 적용 |
| **180°~230°**| CAM 후반 / CamOut 구간  | 분리막 공급 완료 → STACK_*_RUN_CAMOUT 트리거<br>CAMOUT_Cam_Unwinder 실행으로 슬레이브 해제 |
| **230°~320°**| 자유 구간 / 위치 보정     | CAM 해제 후 Dancer 텐션 안정화 대기                   |
| **320°~360°**| MoveRelative 재위치       | Step 400: SepaUWR + SepaFeederR MoveRelative 실행<br>다음 사이클 공급 시작 위치로 이동 |
| **360°(=0°)** | 다음 사이클 대기          | 다음 LC/RA 트리거 대기, CamIn 재실행 준비             |

---

## Auto Sequence 흐름 (FB_Auto_Sub2_Unwinder)

```
Step 100 — 초기 대기
  - Unwinder_RUN_CMD 입력 감시
  - CamIn/CamOut 상태 초기화 확인

Step 200 — 속도 매칭 (MC_MOVEVELOCITY)
  - VelocitySource := Unwinder_Velocity (FB_Unwinder_Sequence_Judgment 계산값)
  - Axis01를 VR03 속도에 근접시켜 동기화 충격 최소화
  - InSync 조건 충족 시 Step 300으로 이행

Step 300 — CAM 동기 구간 (CamIn ACTIVE)
  - Unwinder_RUN_CMD = TRUE → CamIn Execute 활성
  - DB_Global_Cam_Control.STACK_LC_RUN_CAMIN or STACK_RA_RUN_CAMIN = TRUE
  - VR03 0°~180°+ 구간 Axis01 CAM 추종
  - 공급 완료 → RUN_END 신호
  - CamOut Execute 활성화 → 슬레이브 해제
  - Step 400으로 이행

Step 400 — 재위치 이동 (MC_MOVERELATIVE)
  - SepaUWR (Axis01): 다음 공급 준비 위치로 상대 이동
  - SepaFeederR (Axis05): 피더 롤러 연동 이동
  - 이동 완료 → Step 100으로 복귀
```

---

## Axis 간 역할 분담

| Axis                   | 번호    | CAM 역할               | MoveRelative 역할            |
|------------------------|---------|----------------------|------------------------------|
| Axis01_SepaUWR_TB107   | Axis01  | CAM 슬레이브 (분리막 공급) | Step 400 재위치             |
| Axis05_SepaFeederR     | Axis05  | 독립 (CAM 없음)        | Step 400 연동 이동           |
| VR03_StackLeadingAxis  | (가상)  | CAM 마스터 (0°~360°)  | —                            |

---

## 5가지 핵심 포인트

1. **LC/RA 공통 단일 Unwinder**  
   `CamIn.Execute = STACK_LC_RUN_CAMIN OR STACK_RA_RUN_CAMIN`  
   → Cathode 적재와 Anode 적재 모두 동일한 분리막 언와인더를 구동.  
   두 신호가 동시에 TRUE가 되는 구조는 아님 (교번 진행).

2. **SlaveScaling 동적 보정**  
   권취 릴 직경이 사이클마다 달라지므로, `FB_Unwinder_Sequence_Judgment`가  
   매 사이클 `Transfer_distance`를 재계산해 SlaveScaling에 반영.  
   Dancer 텐션 각도까지 보정 계수로 포함 (`× (1 + 0.01 × Dancer_Angle)`).

3. **CamIn 직전 속도 매칭 필수 (Step 200)**  
   `MC_MOVEVELOCITY`로 Axis01을 VR03 연동 속도에 미리 맞춘 후 CamIn.  
   이를 생략하면 슬레이브가 충격적으로 당겨지며 분리막 장력 이상 발생.

4. **SyncProfileReference=2 (슬레이브 기준 동기화)**  
   CamIn 진입 시 슬레이브 현재 속도·위치를 기준으로 부드럽게 프로파일 연결.  
   AbsoluteSynchronization 모드보다 전환 충격이 작음.

5. **CAM 해제 후 MoveRelative로 마무리**  
   CamOut 이후 Axis01·Axis05를 고정된 상대 거리만큼 추가 이동(Step 400).  
   이 이동이 다음 단 공급의 시작점을 결정하므로 거리 계산이 공정 정밀도에 직결됨.
