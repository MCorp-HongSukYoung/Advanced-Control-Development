# VR03_StackLeadingAxis 0° → 360° 회전 시 P&P · Stack Table 동작

- **프로젝트**: `PowerCo_Stack_20260421_R142_KJR_R02`
- **CPU**: `Z-AF051.S01.KE01.PLC`
- **마스터 가상축**: `VR03_StackLeadingAxis` (TO_PositioningAxis, Virtual)
- **CAM 결합 FB**: `FB_Camin_STACK_LC_RUN` [#8003]
- **사이클 구동 FB**: `FB_Auto_Sub1_Stack_200` [#2200]
- **상위 문서**: [`LC_RUN_CAM_구조.md`](LC_RUN_CAM_구조.md), [`STACK_LC_RUN_CAMIN_비트조건.md`](STACK_LC_RUN_CAMIN_비트조건.md)
- **작성일**: 2026-05-12

---

## 0) 한 줄 결론

> **VR03 가상축의 1회전(0° → 360°) = 셀 1장 적층 사이클(LC 1장 + RA 1장).**
> P&P 6축, Reverse P&P 4축, Stack Table Swing Roller 4축이 모두 **VR03을 마스터로 한 `MC_CAMIN`** 으로 결합되어, VR03이 도는 동안 각자의 캠 프로파일을 따라 GET → 반전 → 적층 동작을 동시 수행한다.

---

## 1) 동작 구조 요약

```
              [ FB_Auto_Sub1_Stack_200 ]
                         │
                         │  MC_MOVERELATIVE(VR03, +360°)
                         ▼
         ┌──────────────────────────────────┐
         │   VR03_StackLeadingAxis  0 → 360°│   ← 가상 마스터
         └──────────────────────────────────┘
                         │   (CamTable 프로파일)
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   [ Cathode P&P ]  [ Anode P&P ]   [ Stack Table ]
   ─ 메인 1/2 X·Z   ─ 메인 1/2 X·Z   ─ Swing Roller Z01/Z02
   ─ Reverse  Z·R   ─ Reverse  Z·R   ─ Swing Roller R01/R02
```

VR03은 물리 인코더 없는 가상축으로, `FB_Auto_Sub1_Stack_200`의 sub-step 230에서 `MC_MOVERELATIVE`로 한 바퀴 돌린다. 그 한 바퀴 동안, `FB_Camin_STACK_LC_RUN`이 미리 결합해둔 25개 슬레이브가 캠 프로파일을 따라 동작한다.

---

## 2) 결합되는 축 목록 (P&P · Stack Table 한정)

### 2-1. Cathode(LC) Pick & Place — GET 측

| CAMIN 인스턴스 | 슬레이브 축 | 역할 |
|---|---|---|
| `CAMIN_Cam_STACK_LC_PP1X_GET` | Axis_13 Cathode Main P&P Head01 X | 1번 헤드 X 이동 (집기 위치) |
| `CAMIN_Cam_STACK_LC_PP1Z_GET` | Axis_14 Cathode Main P&P Head01 Z | 1번 헤드 Z 하강/상승 (집기) |
| `CAMIN_Cam_STACK_LC_PP2X_PUT` | Axis_15 Cathode Main P&P Head02 X | 2번 헤드 X 이동 (놓기 위치) |
| `CAMIN_Cam_STACK_LC_PP2Z_PUT` | Axis_16 Cathode Main P&P Head02 Z | 2번 헤드 Z 하강/상승 (놓기) |
| `CAMIN_Cam_STACK_LC_ReverseZ_PUT` | Axis_11 Cathode Reverse P&P Z | 반전 P&P Z |
| `CAMIN_Cam_STACK_LC_ReverseR_PUT` | Axis_12 Cathode Reverse P&P R | 반전 P&P 회전(상하 뒤집기) |

### 2-2. Anode(RA) Pick & Place — PUT 측

| CAMIN 인스턴스 | 슬레이브 축 | 역할 |
|---|---|---|
| `CAMIN_Cam_STACK_RA_PP1X_PUT` | Axis_28 Anode Main P&P Head01 X | 1번 헤드 X (놓기 측) |
| `CAMIN_Cam_STACK_RA_PP1Z_PUT` | Axis_29 Anode Main P&P Head01 Z | 1번 헤드 Z |
| `CAMIN_Cam_STACK_RA_PP2X_GET` | Axis_30 Anode Main P&P Head02 X | 2번 헤드 X (집기 측) |
| `CAMIN_Cam_STACK_RA_PP2Z_GET` | Axis_31 Anode Main P&P Head02 Z | 2번 헤드 Z |
| `CAMIN_Cam_STACK_RA_ReverseZ_GET` | Axis_26 Anode Reverse P&P Z | 반전 P&P Z |
| `CAMIN_Cam_STACK_RA_ReverseR_GET` | Axis_27 Anode Reverse P&P R | 반전 P&P 회전 |

> LC 측은 PP1=GET/PP2=PUT 구조, RA 측은 PP1=PUT/PP2=GET 구조 — 두 헤드가 **교대로 일하면서 한 사이클 안에 GET ↔ PUT 동작이 겹치지 않게** 설계되어 있음.

### 2-3. Stack Table Swing Roller

| CAMIN 인스턴스 | 슬레이브 축 | 역할 |
|---|---|---|
| `CAMIN_Cam_STACK_Swing1Z_LC` | Axis_37 Stack Table Swing Roller Z01 | 1번 스윙 롤러 Z 승강 |
| `CAMIN_Cam_STACK_Swing1R_LC` | Axis_39 Stack Table Swing Roller R01 | 1번 스윙 롤러 회전 |
| `CAMIN_Cam_STACK_Swing2Z_LC` | Axis_38 Stack Table Swing Roller Z02 | 2번 스윙 롤러 Z 승강 |
| `CAMIN_Cam_STACK_Swing2R_LC` | Axis_40 Stack Table Swing Roller R02 | 2번 스윙 롤러 회전 |

> Stack Table의 **Z(승강)** 와 **R(회전)** 4축이 VR03 캠을 따라 동작 → P&P 가 전극을 놓는 시점에 맞춰 **Swing Roller가 들렸다 내려오며 분리막을 위 → 아래로 덮어 적층 면을 만든다**.

---

## 3) GET / PUT 교차 구조 — LC ↔ RA 의 거울 동작

### 3-1. CAMIN 인스턴스 이름이 알려주는 역할 분담

CAMIN 인스턴스 이름의 접미사(`_GET` / `_PUT`)에 **각 헤드가 한 사이클 안에서 담당하는 주역할** 이 그대로 박혀 있다.

| 사이드 | PP1 헤드 | PP2 헤드 | Reverse P&P |
|---|---|---|---|
| **LC (Cathode)** | **`PP1X_GET` / `PP1Z_GET`** ← 매거진에서 집기 | `PP2X_PUT` / `PP2Z_PUT` → Stack Table 에 놓기 | `ReverseZ_PUT` / `ReverseR_PUT` (PP1 → Reverse 로 **PUT 받음**) |
| **RA (Anode)** | `PP1X_PUT` / `PP1Z_PUT` → Stack Table 에 놓기 | **`PP2X_GET` / `PP2Z_GET`** ← 매거진에서 집기 | `ReverseZ_GET` / `ReverseR_GET` (Reverse → PP1 으로 **GET 보냄**) |

→ 결론: **LC 와 RA 는 PP1/PP2 의 GET/PUT 역할이 서로 반대로 배치**되어 있다.
→ 즉 같은 시점에 한쪽이 GET 이면 반대쪽은 PUT 이 된다.

### 3-2. 한 사이클 안에서 동시에 흐르는 두 파이프라인

```
[ 파이프라인 ①  LC GET  =  RA PUT  ]   (PP1 라인)
   LC magazine ─▶ LC PP1 (GET) ─▶ LC Reverse(PUT) ─… (다음 사이클로 인계)
                                                    
   …(이번 사이클에 반전 완료된 RA 전극) ─▶ RA PP1 (PUT) ─▶ Stack Table

[ 파이프라인 ②  LC PUT  =  RA GET  ]   (PP2 라인)
   …(이번 사이클에 반전 완료된 LC 전극) ─▶ LC PP2 (PUT) ─▶ Stack Table
                                                    
   RA magazine ─▶ RA PP2 (GET) ─▶ RA Reverse(GET) ─… (다음 사이클로 인계)
```

> 두 파이프라인은 **VR03 한 바퀴 동안 동시에 진행** 된다.
> 현재 사이클의 LC/RA 가 적층될 전극은 **이전 사이클에서 PP1·PP2 가 Reverse 로 넘겨놓고 반전된 것** 이고, 이번 사이클에 PP1·PP2 가 새로 GET 하는 전극은 **다음 사이클에 적층될 것** — 즉 **2-단 파이프라인**.

### 3-3. VR03 각도별 동작 (수정판)

| VR03 각도 | 비전 트리거 | LC 측 | RA 측 | Stack Table |
|---|---|---|---|---|
| **0°** | — (StandStill 확인 후 진입) | PP1 = LC 매거진 위 Z 하강 시작 (GET) ／ PP2 = LC Reverse 위 Z 하강 시작 (반전된 전극 GET) | PP1 = RA Reverse 위 Z 하강 시작 (반전된 전극 GET) ／ PP2 = RA 매거진 위 Z 하강 시작 (GET) | Z 상승, 분리막 안착 자세 |
| **0° ~ 80°** | — | LC PP1 흡착 후 Z 상승, X 이동 → Reverse 로 향함 ／ LC PP2 흡착 후 Z 상승, X 이동 → Stack 로 향함 | RA PP1 흡착 후 Z 상승 → Stack 로 향함 ／ RA PP2 흡착 후 Z 상승 → Reverse 로 향함 | Z01/Z02 미세 승강 |
| **80°** | `1st_Surface_Vision_LC.Trg[0]` | **LC PP1 1차 면 검사** (매거진 GET 직후) | — | — |
| **80° ~ 120°** | — | LC PP1 → LC Reverse 위 Z 하강, 전극 PUT → Reverse 가 R 축으로 뒤집기 시작 | RA PP2 → RA Reverse 위 Z 하강, 전극 PUT → Reverse 가 R 축으로 뒤집기 시작 | — |
| **120°** | `1st_Surface_Vision_RA.Trg[0]` | — | **RA PP2 1차 면 검사** (매거진 GET 직후) | — |
| **120° ~ 180°** | — | LC PP2 가 운반 중인 (이전 사이클 반전된) 전극이 Stack Align 위치 도달 | RA PP1 이 운반 중인 (이전 사이클 반전된) 전극이 Stack Align 위치 도달 | Swing Roller R01/R02 회전 → 분리막 위치 정렬 |
| **180°** | `2nd_Surface_Vision_LC` / `2nd_Surface_Vision_RA` | **LC PP2 2차 면 검사** (반전된 전극, PUT 직전) | **RA PP1 2차 면 검사** (반전된 전극, PUT 직전) | — |
| **180° ~ 230°** | — | LC PP2 가 Stack Table 정확 위치로 X 정렬 | RA PP1 가 Stack Table 정확 위치로 X 정렬 | Swing Roller Z 상승 — 분리막 들어올림 |
| **230°** | `Align_Vision.Trg[18]` | — | — | **적층 직전 Align 비전 검사** |
| **230° ~ 320°** | — | **LC PP2 Z 하강 → Cathode PUT** → 흡착 해제 → Z 상승 | **RA PP1 Z 하강 → Anode PUT** → 흡착 해제 → Z 상승 | Swing Roller 회전·하강 → 분리막으로 전극 덮음 |
| **320° ~ 360°** | — | LC PP1/PP2 X 복귀 (PP1 → 다음 사이클 매거진 위치, PP2 → 다음 사이클 Reverse 위치) | RA PP1/PP2 X 복귀 (PP1 → 다음 사이클 Reverse 위치, PP2 → 다음 사이클 매거진 위치) | Z 원위치 복귀 |
| **360° (= 0°)** | (`MC_MOVERELATIVE.Done`) | 1 cell 적층 완료 → sub-step 240 진입 | — | — |

> 정확한 위치/속도 프로파일은 `DB_GdbCam` + `DB_Global_Cam_Pos` 의 캠 데이터로 정의된다. 위 표는 **비전 트리거 시점과 CAMIN 이름 규약(GET/PUT)** 을 기준으로 한 개념적 타임라인이다.

---

## 4) 한 사이클 안의 두 흐름 — Reverse P&P 까지 포함한 서술

### 4-1. LC (Cathode) 흐름 — `LC PP1 GET` → `Reverse 반전` → `LC PP2 PUT`

VR03 한 바퀴 안에서 Cathode 1장이 거치는 경로:

1. **0° ~ 80°  · GET 단계** : `LC PP1` (Axis 13 X / 14 Z) 가 LC 매거진 위로 X 이동 → Z 하강 → 흡착 → Z 상승.
2. **80°  · 1차 면 비전** : 흡착된 면을 위에서 촬영해 표면 결함을 확인.
3. **80° ~ 180°  · Reverse 로 전달** : `LC PP1` 이 LC Reverse P&P 위로 X 이동 → Z 하강 → **`LC ReverseZ_PUT` (Axis 11) 위에 놓음** → `LC ReverseR_PUT` (Axis 12) 가 R 축으로 회전해 **2차 면을 위로 향하게 반전**.
4. **180°  · 2차 면 비전** : 반전 후, `LC PP2` (Axis 15 X / 16 Z) 가 Reverse 위로 와서 흡착할 준비를 하면서 2차 면을 비전이 촬영.
5. **180° ~ 230°  · PUT 위치 이동** : `LC PP2` 가 Reverse 에서 흡착(이번 사이클의 Reverse 결과물이 아니라 **이전 사이클에 PP1 이 넘겨놓고 이번 사이클 전반부에 반전된 것**) → Stack Table 위로 X 이동.
6. **230°  · Align 비전** : 적층 정렬 검사.
7. **230° ~ 320°  · PUT 단계** : `LC PP2` Z 하강 → Stack Table 분리막 위에 Cathode 안착 → 흡착 해제 → Z 상승.
8. **320° ~ 360°  · 복귀** : `LC PP1` 은 다음 사이클 매거진 위로, `LC PP2` 는 다음 사이클 Reverse 위로 X 복귀.

### 4-2. RA (Anode) 흐름 — `RA PP2 GET` → `Reverse 반전` → `RA PP1 PUT`

LC 와 거울 대칭. **PP1/PP2 의 GET/PUT 역할이 반대** 임에 주의.

1. **0° ~ 120°  · GET 단계** : `RA PP2` (Axis 30 X / 31 Z) 가 RA 매거진에서 Anode 흡착.
2. **120°  · 1차 면 비전** : `RA PP2` 흡착 직후 1차 면 비전.
3. **120° ~ 180°  · Reverse 로 전달** : `RA PP2` → RA Reverse 위 Z 하강 → 전극을 놓음 → `RA ReverseZ_GET` (Axis 26) / `RA ReverseR_GET` (Axis 27) 가 R 축으로 반전.
   - 이름이 `_GET` 인 이유: Reverse 의 **출력측이 PP1** 이라, "Reverse → PP1 으로 GET 시킨다" 는 의미로 명명.
4. **180°  · 2차 면 비전** : `RA PP1` (Axis 28 X / 29 Z) 이 Reverse 위로 와서 (이번 사이클 전반부에 반전된 전극을) 흡착할 준비. 2차 면 비전 촬영.
5. **180° ~ 230°  · PUT 위치 이동** : `RA PP1` 흡착 후 Stack Table 위로 X 이동.
6. **230° ~ 320°  · PUT 단계** : `RA PP1` Z 하강 → Anode 안착 → 흡착 해제 → Z 상승.
7. **320° ~ 360°  · 복귀** : `RA PP1` 은 다음 사이클 Reverse 위로, `RA PP2` 는 다음 사이클 매거진 위로 X 복귀.

### 4-3. Stack Table Swing Roller — 분리막 덮기 동작

`Axis 37/38 Z` + `Axis 39/40 R` 4축은 VR03 한 바퀴 동안 **분리막을 전극 위로 덮어 셀 한 단을 완성** 한다.

1. **0° ~ 180°  · 대기/세팅** : Z 축 미세 승강으로 분리막 텐션 유지, R 축은 다음 덮기 자세로 회전 정렬.
2. **180° ~ 230°  · 분리막 들어올림** : Swing Roller Z 상승 → 분리막을 위로 들어 올려 **PP 헤드가 전극을 안착할 공간 확보**.
3. **230°** : Align 비전 통과 → PP 헤드 PUT 동작 시작과 동기.
4. **230° ~ 320°  · 덮기** : PP 헤드가 전극을 놓는 동안 **Swing Roller 가 R 축으로 회전·Z 축으로 하강** 하며 분리막을 전극 위로 덮음. → 한 단(=Cathode + 분리막 + Anode + 분리막) 완성.
5. **320° ~ 360°  · 복귀** : Z 원위치, R 다음 사이클 시작 자세로 복귀.

> Swing Roller 1번(Axis 37 Z + 39 R) 과 2번(Axis 38 Z + 40 R) 은 좌·우(또는 전·후) 분리막을 각각 담당해 **두 장의 분리막을 동시에 덮을 수 있게** 구성되어 있다.

### 4-4. 한 사이클이 만드는 결과물

VR03 1회전(0°→360°) = **Cathode 1장 + 분리막 1장 + Anode 1장 + 분리막 1장 = 셀 1단**
- LC 측은 PP1 이 GET, PP2 가 PUT 을 동시에 진행 (2-단 파이프라인)
- RA 측은 PP2 가 GET, PP1 이 PUT 을 동시에 진행 (역시 2-단 파이프라인)
- 따라서 **이번 사이클에 적층되는 전극은 이전 사이클 전반부에 PP1·PP2 가 Reverse 로 넘겨놓은 것** 이고, 이번 사이클에 새로 GET 한 전극은 **다음 사이클에 적층** 된다.

---

## 5) 핵심 포인트 정리

1. **VR03은 한 바퀴 = 한 셀** — 정확히 360° 회전이 1 사이클 단위.
2. **P&P 12축 + Stack Table 4축 모두 VR03 슬레이브** — 12개의 P&P 축(LC/RA × Main 2헤드 × X/Z + Reverse Z/R)과 4개의 Stack Table Swing Roller 축(Z01/Z02/R01/R02)이 모두 `MC_CAMIN` 으로 VR03에 결합되어 있어 **소프트웨어 PLC 차원에서 기계적 캠축처럼 동기**된다.
3. **CAMIN은 `Execute` 한 번만 떨어뜨리면 유지** — 사이클마다 다시 결합하지 않는다. `STACK_LC_RUN_CAMIN` 비트가 한번 Set 되어 25축이 InSync 되면, 그 이후 `MC_MOVERELATIVE` 가 VR03을 돌릴 때마다 슬레이브들이 자동으로 캠을 따라 같이 돈다.
4. **위치 보장 인터록** — sub-step 210에서 `VR03.ActualPosition == 0.0` & StandStill 을 확인해야만 다음 사이클에 진입한다 (캠 결합 시 마스터/슬레이브 위치 어긋남 방지).
5. **두 헤드 교대 동작** — LC PP1=GET / PP2=PUT, RA PP1=PUT / PP2=GET 으로 **두 헤드가 한 사이클 안에서 교대로 일하기 때문에** VR03 한 바퀴 동안 GET 동작과 PUT 동작이 동시에 진행될 수 있다.

---

## 6) 참고 자료

- 상위 구조: [`LC_RUN_CAM_구조.md`](LC_RUN_CAM_구조.md) §3 (CAM coupling 25축 전체 표)
- CAMIN 비트 조건: [`STACK_LC_RUN_CAMIN_비트조건.md`](STACK_LC_RUN_CAMIN_비트조건.md)
- 시퀀서 구조: [`FB_auto_Sequence_stack_구조.md`](FB_auto_Sequence_stack_구조.md)
- XML 추출:
  - `exports\FB_Camin_STACK_LC_RUN.xml` — VR03 마스터 + 25개 슬레이브 결합 정의
  - `exports\FB_Auto_Sub1_Stack_200.xml` — VR03 회전 명령 (`MC_MOVERELATIVE`) + 비전 트리거
