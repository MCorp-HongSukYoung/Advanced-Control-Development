# VR 축 동작 전체 흐름 (1 Stacking Cycle)

## 전체 사이클 구조

```
1 Stacking Cycle = [ LC_RUN ] + [ LC_STACK ] + [ RA_RUN ] + [ RA_STACK ]  ×  N층 반복
                   └─ PPTime ─┘ └─ManTime ──┘ └─ PPTime ─┘ └─ManTime ──┘
```

---

## 타임라인

```
시간 →
         ┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
         │    LC_RUN        │    LC_STACK       │    RA_RUN        │    RA_STACK       │
         │  (PPMovingTime)  │ (MandrelMovTime)  │  (PPMovingTime)  │ (MandrelMovTime)  │
         ├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
 VR01    │ ████████████████ │                  │                  │                  │
Cathode  │ R/X/Z 3축 CAM   │    대기           │    대기          │    대기          │
Dsheet   │ (흡착→Turn→핸드오프)│               │                  │                  │
         ├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
 VR02    │                  │                  │ ████████████████ │                  │
Anode    │    대기          │    대기           │ R/X/Z 3축 CAM   │    대기          │
Dsheet   │                  │                  │ (흡착→Turn→핸드오프)│              │
         ├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
 VR03    │ ████████████████ │                  │ ████████████████ │                  │
Stack PP │ LC CAM 13축 동기 │    대기           │ RA CAM 13축 동기 │    대기          │
         │ PP1 GET + 정렬   │                  │ PP1 GET + 정렬   │                  │
         │ + PP2 PUT + Swing│                  │ + PP2 PUT + Swing│                  │
         ├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
 VR04    │                  │ ████████████████ │                  │ ████████████████ │
Mandrel  │    대기          │ 9축 CAM 동기     │    대기          │ 9축 CAM 동기    │
         │                  │ LC Mand1/2 Y/Z   │                  │ RA Mand1/2 Y/Z  │
         │                  │ RA Mand1/2 Y/Z   │                  │ RA Mand1/2 Y/Z  │
         │                  │ + TableZ         │                  │ + TableZ         │
         ├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
 VR06    │ ░░░░░░░░░░░░░░░░ │ ████████████████ │ ░░░░░░░░░░░░░░░ │ ████████████████ │
Winding  │  준비(대기 추정) │ Winding 동작     │ 준비(대기 추정)  │ Winding 동작    │
         │                  │ X1/X2/Z1/Z2/Run  │                  │ X1/X2/Z1/Z2/Run  │
         ├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
Unwinder │ ──────────────────────────────────────────────────────────────────────────│
(VR없음) │ Separator 연속 공급 (속도 = JR.Width / 1°전달률 / (PPTime + MandrelTime)) │
         └──────────────────┴──────────────────┴──────────────────┴──────────────────┘
         └─────────────────────────────────────────────────────────────────────────────┘
                                        ×  N층 반복 (Stack_2 ~ Stack_8)
```

> ░ = 확인 필요 구간 (Winding 정확한 트리거 시점 미확인)

---

## VR별 슬레이브 축 상세

### VR01 — CathodeDoubleSheetLeadingAxis
- 속도: `(1.0 / CathodeDoubleSheetActionTime) × 360°`
- CAM 슬레이브 (3축):

```
  VR01 ─┬─ Axis10_CathodeDoubleSheetR_TB103   (R축: Stack PP가 픽업 가능한 각도로 Turn)
        ├─ Axis08_CathodeDoubleSheetX_TB115   (X축: R 회전 중 극판-매거진 간섭 방지 보상)
        └─ Axis09_CathodeDoubleSheetZ_TB114   (Z축: 하강/흡착 ↔ 상승)
```

---

### VR02 — AnodeDoubleSheetLeadingAxis
- 속도: `(1.0 / AnodeDoubleSheetActionTime) × 360°`
- CAM 슬레이브 (3축):

```
  VR02 ─┬─ Axis25_AnodeDoubleSheetR_TB133    (R축: Turn)
        ├─ Axis23_AnodeDoubleSheetX_TB139    (X축: 간섭 방지 보상)
        └─ Axis24_AnodeDoubleSheetZ_TB138    (Z축: 하강/흡착 ↔ 상승)
```

---

### VR03 — StackLeadingAxis
- 속도: `(1.0 / PPMovingTime) × 360°`
- CAM 슬레이브 (13축, LC_RUN 기준 / RA_RUN은 대칭):

```
  VR03 ─┬─ [Align]
        │    ├─ Axis19_CathodeAlignUnitTableθ_TB122  (정렬 테이블 회전)
        │    ├─ Axis17_CathodeAlignUnitTableX_TB120  (정렬 테이블 X)
        │    └─ Axis18_CathodeAlignUnitTableY_TB121  (정렬 테이블 Y)
        │
        ├─ [PP1 GET — 극판 픽업]
        │    ├─ Axis13_CathodeMainP&PHead01X_TB101   (PP1 헤드 X)
        │    └─ Axis14_CathodeMainP&PHead01Z_TB118   (PP1 헤드 Z)
        │
        ├─ [PP2 PUT — 극판 적재]
        │    ├─ Axis15_CathodeMainP&PHead02X_TB104   (PP2 헤드 X)
        │    └─ Axis16_CathodeMainP&PHead02Z_TB119   (PP2 헤드 Z)
        │
        ├─ [Reverse — 뒤집기]
        │    ├─ Axis27_AnodeReverseP&PElectrodeR_TB141  (리버스 R)
        │    └─ Axis26_AnodeReverseP&PElectrodeZ_TB140  (리버스 Z)
        │
        └─ [Swing — 스윙 롤러]
             ├─ Axis39_StackTableSwingRollerR01_TB128   (스윙1 R)
             ├─ (Swing1 Z)
             ├─ (Swing2 R)
             └─ (Swing2 Z)
```

---

### VR04 — MandrelLeadingAxis
- 속도: `(1.0 / MandrelMovingTime) × 360°`
- CAM 슬레이브 (9축):

```
  VR04 ─┬─ [LC Mandrel — Cathode 맨드릴]
        │    ├─ Axis43_CathodeStackTableMandrel01Y_TB123  (맨드릴1 Y)
        │    ├─ Axis41_CathodeStackTableMandrel01Z_TB102  (맨드릴1 Z)
        │    ├─ Axis44_CathodeStackTableMandrel02Y_TB124  (맨드릴2 Y)
        │    └─ Axis42_CathodeStackTableMandrel02Z_TB105  (맨드릴2 Z)
        │
        ├─ [RA Mandrel — Anode 맨드릴]
        │    ├─ Axis47_AnodeStackTableMandrel01Y_TB147   (맨드릴1 Y)
        │    ├─ Axis45_AnodeStackTableMandrel01Z_TB132   (맨드릴1 Z)
        │    ├─ Axis48_AnodeStackTableMandrel02Y_TB148   (맨드릴2 Y)
        │    └─ Axis46_AnodeStackTableMandrel02Z_TB135   (맨드릴2 Z)
        │
        └─ [Stack Table]
             └─ Axis36_StackTableZ_TB125                 (테이블 Z)
```

---

### VR06 — WinderLeadingAxis
- 속도: 별도 확인 필요
- CAM 슬레이브: Winding X1/X2/Z1/Z2/Run (SepaGripper 축)

---

### Unwinder — VR 없음 (속도 직접 제어)
- 속도: `JR.Width / 1°전달률 / (PPMovingTime + MandrelMovingTime)`
- 1°전달률: `(Unwinder_Separator_Diameter × 2 × π) / 360`
- Dancer 위치 기반 보정계수(`statCorrectionFactor`) 적용

---

## CAM 모드 전환 요약

```
  Stack GRAPH 스텝     활성 CAM
  ─────────────────    ────────────────────────────────────────
  LC_RUN           →  VR01 CamIn (Cathode Dsheet)
                       VR03 CamIn (Single_LC_RUN / STACK_LC_RUN)

  LC_STACK         →  VR04 CamIn (LC_STACK: LC+RA Mandrel + TableZ)
                       VR06 CamIn (Winding — 추정)

  RA_RUN           →  VR02 CamIn (Anode Dsheet)
                       VR03 CamIn (Single_RA_RUN / STACK_RA_RUN)

  RA_STACK         →  VR04 CamIn (RA_STACK: LC+RA Mandrel + TableZ)
                       VR06 CamIn (Winding — 추정)
```

---

## 핸드오프 교번 구조

```
  LC_RUN 진입 시:
    VR01 CamIn  (Cathode Dsheet 활성화)
    VR02 CamOut (이전 Anode CAM 해제 ← L_Cathode FB가 Anode 축을 CamOut)

  RA_RUN 진입 시:
    VR02 CamIn  (Anode Dsheet 활성화)
    VR02 CamOut (이전 Anode CAM 해제 ← R_Anode FB 자기 자신 CamOut)
```
