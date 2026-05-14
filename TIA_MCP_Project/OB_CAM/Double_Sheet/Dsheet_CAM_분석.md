# Dsheet CAM 분석 (L_Cathode / R_Anode)

## 한 줄 결론
> Cathode(VR01)와 Anode(VR02) 각각 별도 가상 마스터로 R/X/Z 3축을 동시 CAM 동기.  
> **CamOut이 자기 축이 아닌 반대편 재질 축을 해제**하는 교번 핸드오프 구조.

---

## 1. Double Sheet 물리적 의미

### 설비 개요

Double Sheet는 **매거진에서 전극 시트를 진공 흡착하여 Stack PP가 픽업할 수 있도록 Turn해주는 유닛**이다.  
실제 적층 위치로의 이송은 Stack PP(Pick & Place)가 담당한다.

```
[매거진]
  │
  │  ← 전극 시트 적재
  ↓
[Dsheet Unit]
  ├── R 축 (Rotation)   : 극판을 Turn — Stack PP가 픽업 가능한 각도로 회전
  ├── X 축 (Horizontal) : 소량 측면 이동 — R 회전 중 극판 끝단이 매거진에 닿아
  │                        손상되는 것을 방지하기 위한 보상 이동 (이송 목적 아님)
  └── Z 축 (Vertical)   : 수직 이송 — 하강(흡착) ↔ 상승
           ↓
[Stack PP]  ← 여기서 극판을 픽업하여 적층 테이블(JR)로 이송
```

- **Unit03** = L_Cathode Double Sheet (음극재 공급)
- **Unit04** = R_Anode Double Sheet (양극재 공급)
- 3개 축이 **단일 가상 마스터(VR01/VR02)** 에 동시 CAM 동기되어 협조 동작

### 1사이클 물리 동작

```
VR = 0°
  → Z 하강: 매거진에서 전극 시트 진공 흡착

VR = 0° → 360° (R 회전 중)
  → R 축: Stack PP가 픽업할 수 있는 각도로 Turn
  → X 축: R 회전 시 극판 끝단이 매거진에 간섭되지 않도록 소량 측면 보상 이동
  → Z 축: 상승

VR ≈ 완료 시점
  → Stack PP가 Dsheet Unit에서 극판 픽업 → 적층 테이블(JR)로 이송

VR = 360° (→ 0°)
  → R 역회전 + Z 하강: 다음 사이클을 위해 매거진으로 귀환
```

---

## 2. 블록 구성

```
210_CAM/
├── Dsheet_L_Cathode/
│   └── FB_Camin_Dsheet_L_Cathode   ← Cathode Double Sheet CAM 래퍼 (VR01 기준)
└── Dsheet_R_Anode/
    └── FB_Camin_Dsheet_R_Anode     ← Anode Double Sheet CAM 래퍼 (VR02 기준)
```

두 블록 모두 동일 패턴: **MC_CamIn × 3 + MC_CamOut × 3**

---

## 3. Axis 구성 및 역할

| 구분 | Master | Slave R | Slave X | Slave Z |
|------|--------|---------|---------|---------|
| **L_Cathode (CamIn)** | VR01_CathodeDoubleSheetLeadingAxis | Axis10_CathodeDoubleSheetR_TB103 | Axis08_CathodeDoubleSheetX_TB115 | Axis09_CathodeDoubleSheetZ_TB114 |
| **R_Anode (CamIn)** | VR02_AnodeDoubleSheetLeadingAxis | Axis25_AnodeDoubleSheetR_TB133 | Axis23_AnodeDoubleSheetX_TB139 | Axis24_AnodeDoubleSheetZ_TB138 |

| 구분 | CamOut 대상 |
|------|------------|
| **L_Cathode (CamOut)** | Axis25 / Axis23 / Axis24 ← **Anode 축** |
| **R_Anode (CamOut)** | Axis25 / Axis23 / Axis24 ← Anode 축 (자기 자신) |

---

## 4. VR01 / VR02 역할 및 속도 공식

### 가상 마스터(VR)란

VR(Virtual Real axis)은 0°→360°를 일정 속도로 회전하는 소프트웨어 마스터 축이다.  
**VR이 360° 회전하는 시간 = 1 공정 사이클 시간(ActionTime)**

### VR 속도 공식

```
VR01_Velocity [°/s] = (1.0 / CathodeDoubleSheetActionTime) × 360.0
VR02_Velocity [°/s] = (1.0 / AnodeDoubleSheetActionTime)   × 360.0
```

출처: `FB_Dsheet_L_Cathode_Sequence_Judgment` / `FB_Dsheet_R_Anode_Sequence_Judgment`

- ActionTime은 레시피(공정 조건 DB)에서 공급
- VR은 MoveRelative로 정확히 360° 이동 → 슬레이브 축들은 CAM 테이블 1주기 완주

### VR01 vs VR02

| 항목 | VR01 | VR02 |
|------|------|------|
| 이름 | CathodeDoubleSheetLeadingAxis | AnodeDoubleSheetLeadingAxis |
| 구동 FB | FB_Dsheet_L_Cathode_Sequence (Sub200) | FB_Dsheet_R_Anode_Sequence (Sub200) |
| CAM 슬레이브 | Axis10(R) / Axis08(X) / Axis09(Z) | Axis25(R) / Axis23(X) / Axis24(Z) |

---

## 5. CAM 커플링 파라미터

| 파라미터 | 값 | 비고 |
|---------|-----|------|
| MasterSyncPosition | 0.01° | 마스터 0° 직후 동기화 |
| SyncDirection | 3 | 양방향 |
| ApplicationMode | 0 | 절대 모드 |
| SyncProfileReference | 2 | 슬레이브 현재 속도 기준 |
| MasterScaling | 1.0 (고정) | |
| MasterOffset | 1.0 (고정) | |
| SlaveScaling | CamData.SlaveScaling (동적) | DB_GdbCam에서 매 사이클 공급 |
| SlaveOffset | CamData.SlaveOffset (동적) | DB_GdbCam에서 매 사이클 공급 |

---

## 6. CamData 주입 구조 (SlaveOffset / SlaveScaling)

### 공급 경로

```
FC_AXIS_TO_CAM_STATUS
  ├── 입력: IN_Start  (현재 축 위치, 흡착 시작점)
  ├── 입력: IN_LONG   (이동 목표 위치, PUT 지점)
  │
  ├── SlaveOffset  = IN_Start                    ← 현재 위치에서 충격 없이 CAM 진입
  └── SlaveScaling = (IN_Start - IN_LONG) × (-1) ← 총 이동 거리
          ↓
  Out_Cam.CamData.SlaveOffset  := SlaveOffset
  Out_Cam.CamData.SlaveScaling := SlaveScaling
          ↓
  DB_GdbCam.Dsheet_L_Cathode / Dsheet_R_Anode
          ↓
  FB_Camin_Dsheet_L_Cathode (Network 5/7): CamIn.SlaveOffset/SlaveScaling 에 전달
```

### 물리적 의미

| 값 | 의미 |
|----|------|
| `SlaveOffset = IN_Start` | CAM 프로파일의 원점을 현재 위치로 평행이동 → 점프 없는 진입 |
| `SlaveScaling = (IN_Start - IN_LONG) × (-1)` | CAM 테이블(0~1 정규화) × Scaling = 실제 이동 거리 |

- IN_Start와 IN_LONG은 공정마다 달라질 수 있어 Winding CAM의 고정 ScalingFactor와 달리 **완전 동적** 구조

### Cam_Starting_Position 판단

```
FB_AXIS_TO_CAM_STATUS Network 4:
  Cam_Dsheet_L_Cathode_Contol.Cam_Starting_Position
    = Axis10[3] AND Axis08[3] AND Axis09[3]
    (→ 3축 모두 Position[3] 도달 여부)

FB_AXIS_TO_CAM_STATUS Network 5:
  Cam_Dsheet_R_Anode_Contol.Cam_Starting_Position
    = Axis25[3] AND Axis23[3] AND Axis24[3]
```

- `Position[3]`은 CAM 진입 직전 대기 위치 (R/X/Z 모두 준비 완료)
- Sub-100 Step 110에서 이 신호를 확인 → False이면 재위치 동작 실행

---

## 7. 핵심 설계 — 교번 CamOut 핸드오프 패턴

### 구조 다이어그램

```
[L_Cathode FB 내부]

  CamIn Execute  ←── DB_Global_Cam_Control.Dsheet_L_Cathode_CAMIN
       ↓
  VR01 → Axis10(R) / Axis08(X) / Axis09(Z) (Cathode 3축) CAM 동기

  CamOut Execute ←── DB_Global_Cam_Control.Dsheet_L_Cathode_CAMOUT
       ↓
  Axis25(R) / Axis23(X) / Axis24(Z) (Anode 축) 해제   ← 반대편 재질 축!

[R_Anode FB 내부]

  CamIn Execute  ←── DB_Global_Cam_Control.Dsheet_R_Anode_CAMIN
       ↓
  VR02 → Axis25(R) / Axis23(X) / Axis24(Z) (Anode 3축) CAM 동기

  CamOut Execute ←── DB_Global_Cam_Control.Dsheet_R_Anode_CAMOUT
       ↓
  Axis25(R) / Axis23(X) / Axis24(Z) (Anode 축) 해제   ← 자기 자신
```

### 왜 L_Cathode가 Anode 축을 CamOut하나?

```
①  Anode CAMIN 실행 중  (VR02 → Axis25/23/24 CAM 추종)

②  Cathode CAMIN 트리거 발생
       ↓
③  L_Cathode FB 실행
       ├── Cathode 축(Axis10/08/09) CamIn  시작
       └── Anode  축(Axis25/23/24) CamOut 동시 실행   ← 이 시점에 Anode CAM 해제

④  Anode 축은 이제 자유 상태 (CAM 속박 없음)

⑤  다음 Anode CAMIN 트리거
       ↓
⑥  R_Anode FB 실행 → Anode 축 다시 CamIn
```

→ **Cathode가 시작할 때 이전 사이클의 Anode CAM을 정리하는 파이프라인 구조**  
→ CamOut 완료를 기다리지 않고 CamIn과 동시 발행 → 전환 지연 최소화

### 교번 패턴의 이점

| 항목 | 설명 |
|------|------|
| 축 충돌 방지 | CAM 해제 전에 새 CAM을 걸면 "이미 결합된 축" 에러 발생 → 교번으로 해결 |
| 전환 지연 제거 | 해제 완료 대기 없이 다음 재질 CAM이 즉시 진입 |
| 단일 신호 구조 | CAMIN/CAMOUT 2개 비트만으로 전체 핸드오프 제어 가능 |

---

## 8. 네트워크별 로직 흐름

```
Network 1: CamOut Execute 세팅
  DB_Global_Cam_Control.Dsheet_[L/R]_CAMOUT
  → 해당 축들 Camout.Execute = TRUE

Network 2: MC_CamOut 실행 (3축 병렬)
  CAMOUT_R / CAMOUT_X / CAMOUT_Z
  SyncDirection=5, 상태 → DB_GdbCam 기록

Network 3: CamIn Execute 세팅
  DB_Global_Cam_Control.Dsheet_[L/R]_CAMIN
  → 해당 축들 CamIn.Execute = TRUE

Network 4: MasterOffset 세팅 (1.0 고정)

Network 5: SlaveOffset 세팅
  CamData.SlaveOffset → CamIn.SlaveOffset (동적, 매 사이클)

Network 6: MasterScaling 세팅 (1.0 고정)

Network 7: SlaveScaling 세팅
  CamData.SlaveScaling → CamIn.SlaveScaling (동적, 매 사이클)

Network 8: MC_CamIn 실행 (3축 병렬)
  CAMIN_R / CAMIN_X / CAMIN_Z → 상태 → DB_GdbCam 기록

Network 9: First_Cam_Starting_Position 집계
  R.Synchronizing_POS AND X.Synchronizing_POS AND Z.Synchronizing_POS
  → 처음 동기화 지점 진입 여부 → DB_Global_Cam_Control

Network 10: ERROR 집계
  R.CamIn.Error OR X.CamIn.Error OR Z.CamIn.Error
  → DB_Global_Cam_Control.Dsheet_[L/R]_ERROR

Network 11: InSync 집계
  R.CamIn.InSync AND X.CamIn.InSync AND Z.CamIn.InSync
  → DB_Global_Cam_Control.Dsheet_[L/R]_InSync
```

---

## 9. 각도별 Auto 시퀀스 동작

### 전체 GRAPH 흐름 (FB_auto_Sequence_Dsheet_L_Cathode)

```
[init]
  ↓
[Dsheet_L_Cathode_Initial]   ← Sub100: CAM 진입 전 위치 확인·보정
  ↓
[Dsheet_L_Cathode_RUN]       ← Sub200: VR01 HOME → MoveRelative 360° (CAM 실행)
  ↓
[Dsheet_L_Cathode_PUT]       ← Sub300: blowoff → PUT → 매거진 리프트 보정
  ↓
[Stack_2 ~ Stack_8]           ← 다단 적층 루프 (Stack Number별 분기)
  ↓
[Dsheet_L_Cathode_return]    ← 복귀 및 다음 사이클 대기
```

### Sub-100: 초기 위치 확인 및 보정

```
Step 100: 시작
Step 110: Cam_Starting_Position 확인
           ├── TRUE  → Step 120 (바로 RUN 진입)
           └── FALSE → Step 140 (재위치 동작)

Step 120: 대기
Step 125: X 축 → Position[3]
Step 126: Z 축 → Position[1]
Step 127: R 축 → Position[3]
Step 128: Z 축 → Position[3]
Step 129: 위치 확인 완료

Step 140~148: JOG forward/backward
              (매거진 리프트 높이 정렬 — 센서 피드백으로 미세 조정)

Step 180→199: Sub100 완료
```

### Sub-200: VR01 MoveRelative (CAM 실행 구간)

```
VR = 0°  (HOME 후 MoveRelative 발행)
  ├── CamIn InSync → 슬레이브 3축 CAM 프로파일 추종 시작

VR = 0° → 360° (1 ActionTime 동안)
  ├── R 축: Turn 프로파일 — 흡착 각도 → Stack PP 픽업 각도 → 복귀
  ├── X 축: 보상 프로파일 — R 회전 중 극판-매거진 간섭 방지 소량 측면 이동
  └── Z 축: 수직 프로파일 — 하강(흡착) → 상승

Step 250: 매거진 리프트 Z 선제 보정
  조건: Auto_Number == 250 AND First_Cam_Starting_Position
        AND Cam_Starting_Position AND NOT Dryrun
  → MC_MOVERELATIVE(Axis07_CathodeMGZUnitElectrodeSupplyZ, Distance = UP_Thichness)
  UP_Thichness = CathodeElectrode.Thickness + 0.005  [mm]
  (픽업 직후 매거진 스택이 1장 낮아졌으므로, 리프트를 극판 두께 + 0.005mm만큼 올려
   다음 사이클 흡착 위치를 유지 — Sub-300 Step 350 JOG 센서 보정의 전 단계)
```

### Sub-300: Stack PP 핸드오프 및 매거진 보정

```
Step 310: RESET JR_PUT_Initial_CMP → Step 320

Step 320 (분기):
  rung 1: PUT_CMD AND Electrode[0].Exist
          → SET VacuumBlowOff (Dsheet 진공 해제 → Stack PP 핸드오프)
          → Step 399 (정상 완료 루트)
  rung 2: PUT_CMD AND Electrode[0].Exist
          AND JR_OUT_CMD AND Stack_Number(1040~1099)
          AND JR_PUT_Initial_CMP == TRUE
          → Step 350 (매거진 리프트 센서 보정 루트)

Step 350: JOGFORWARD 무조건 실행
          → I_Cathode Magazine lift unit Electrode Height Detect_01 감지
             OR Dryrun → Step 351

Step 351: JOGBACKWARD (MC_MOVEJOG Busy 동안)
          → 동일 센서 감지 OR Dryrun → Step 352

Step 352: SET JR_PUT_Initial_CMP → Step 320으로 복귀

Step 399: PUT_END SET → Sub300 완료
```

> ⚠️ **요확인**: XML 원본에서 Step 350 진입 경로(rung 2)에 `NOT(AlwaysTRUE)` 접점이 존재 → 현재 코드상 Dead Code(항상 FALSE).  
> Step 350 JOG 보정이 실제로 동작하는지, 또는 의도적으로 비활성화된 기능인지 실기 확인 필요.

---

## 10. L_Cathode vs R_Anode 비교

| 항목 | L_Cathode | R_Anode |
|------|----------|---------|
| CamIn Master | VR01 (Cathode VR) | VR02 (Anode VR) |
| CamIn Slave R | Axis10_CathodeDoubleSheetR | Axis25_AnodeDoubleSheetR |
| CamIn Slave X | Axis08_CathodeDoubleSheetX | Axis23_AnodeDoubleSheetX |
| CamIn Slave Z | Axis09_CathodeDoubleSheetZ | Axis24_AnodeDoubleSheetZ |
| CamOut 대상 | **Axis25/23/24 (Anode)** | Axis25/23/24 (Anode = 자기 자신) |
| CAM DB (R) | Cam_Dsheet_L_CathodeR | Cam_Dsheet_R_AnodeR |
| CAM DB (X) | Cam_Dsheet_L_CathodeX | Cam_Dsheet_R_AnodeX |
| CAM DB (Z) | Cam_Dsheet_L_CathodeZ | Cam_Dsheet_R_AnodeZ |
| 트리거 | Dsheet_L_Cathode_CAMIN/OUT | Dsheet_R_Anode_CAMIN/OUT |
| InSync 출력 | Dsheet_L_Cathode_InSync | Dsheet_R_Anode_InSync |

---

## 11. DB_GdbCam 상태 구조

```
DB_GdbCam
├── Dsheet_L_Cathode
│   ├── Cam_Dsheet_L_CathodeR
│   │   ├── CamIn.Execute / InSync / Error / EndOfProfile
│   │   ├── CamIn.MasterOffset / SlaveOffset / MasterScaling / SlaveScaling
│   │   ├── Camout.Execute / Done / Error
│   │   ├── CamData.SlaveOffset / SlaveScaling  ← FC_AXIS_TO_CAM_STATUS 주입
│   │   └── StatusWord.Synchronizing_POS
│   ├── Cam_Dsheet_L_CathodeX  (동일 구조)
│   └── Cam_Dsheet_L_CathodeZ  (동일 구조)
└── Dsheet_R_Anode
    ├── Cam_Dsheet_R_AnodeR    (동일 구조)
    ├── Cam_Dsheet_R_AnodeX    (동일 구조)
    └── Cam_Dsheet_R_AnodeZ    (동일 구조)
```

---

## 12. 핵심 포인트 정리

1. **3축 동시 CAM (R/X/Z)**  
   회전(R), 수평(X), 수직(Z)이 동일 VR을 기준으로 동시 동기. 3개 모두 InSync여야 유효.

2. **L_Cathode CamOut이 Anode 축을 해제**  
   Cathode 공정 진입 시 이전 사이클의 Anode CAM을 즉시 정리. 교번 공정에서 축 충돌 없이 전환하기 위한 파이프라인 설계.

3. **SlaveScaling/SlaveOffset은 FC_AXIS_TO_CAM_STATUS가 동적 공급**  
   `SlaveOffset = IN_Start` (충격 없는 진입), `SlaveScaling = (IN_Start - IN_LONG)×(-1)` (총 이동 거리).  
   Winding CAM의 고정 ScalingFactor와 달리 완전 동적 구조.

4. **Cam_Starting_Position = 3축 모두 Position[3]**  
   Sub-100 Step 110에서 이 신호 확인. False이면 X→Z→R→Z 순서로 재위치 후 진행.

5. **First_Cam_Starting_Position (Network 9)**  
   3축 모두 Synchronizing_POS = TRUE일 때 첫 동기화 진입을 상위 시퀀스에 알림.  
   이 신호 기준으로 실제 공정 동작(VR MoveRelative) 시작.
