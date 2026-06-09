# S7TestProject PLC 온보딩

> 생성: 2026-06-09 by /analyze-plc (라이브 세션 분석)
> 소스: `C:\Users\Seokyoung\Desktop\Siemens\Program Developer\S7TestProject\S7TestProject.ap20` → `exports/S7TestProject/` (11 블록 직접 export·열람)
> TIA Portal V20 Update 4 / STEP 7 Professional / SINAMICS Startdrive / WinCC Unified
> 다음 단계: §8 "어디서부터" 의 진입점을 `/analyze-plc` 에 `explain <블록>` 으로 깊이 분석

---

## 1. 한눈에 보기

- **이 PLC 는 배터리 셀 스태킹 공정의 "GAP Vision 측정 데이터 시뮬레이터 / 통신 헤더 생성기" 테스트 프로젝트다.** 실제 비전 카메라 대신 가짜(triangle-wave) 측정값을 만들어 상위 시스템(`mEDAS_DA`)으로 넘기는 데이터 계약(DB_GapPV)을 검증한다.
- 블록은 **11개**뿐인 소형 프로젝트: 코드 블록 5개(OB 1, FC 1, FB 3) + DB 6개.
- 언어는 진입점 OB만 LAD, 나머지 로직은 전부 **SCL**.
- 핵심 데이터 구조 **`DB_GapPV`** 가 PLC ↔ 호스트(비전 데이터 수집/MES) 간의 통신 레이아웃을 정의한다 (Magic / Version / Length 헤더 + 핸드셰이크 + 측정 데이터).
- 상태머신(`S7Test`)은 **IDLE → STACK → OUT** 3-state CASE 구조로 스택 1사이클을 모사한다.
- 명명 규칙이 일관적: 상수 `CST_*`, 인스턴스 정적변수 `st*`, DB는 `DB_*`, 사용자 타입은 `type*`.

---

## 2. 도메인 — 무엇을 제어하는가

**산업 분야: 리튬이온 배터리 셀 스태킹(Stacking) 공정의 GAP 비전 검사** (블록·필드 이름에서 강한 근거, 도메인 자체는 추정).

근거가 되는 용어:
- `Etr*` = **Electrode(전극)**, `Sepa*` = **Separator(분리막)**. 둘 사이의 단차/겹침(overhang gap)을 측정.
- `GapSpecAn` / `GapSpecCa` = **Anode(음극) / Cathode(양극)** 갭 사양.
- `Left` / `Right`, `*TopX/Y` / `*BottomX/Y` = 셀의 좌/우, 상/하 모서리 좌표(비전 픽셀/㎛ 단위 DInt).
- `StackIndex` / `TargetStackCount` / `ProductIndex` = 한 제품(셀)을 목표 장수만큼 적층하는 스택 카운터.
- `mEDAS_DA` (FB_makeHeader 주석) = 측정 데이터를 주기적으로 수집하는 상위 데이터 수집(Edge/MES) 시스템.

**이 프로젝트의 성격은 "테스트/시뮬레이터"** — `FB_makeGapData` 헤더 주석에 *"GAP Vision data update simulator"*, `FC_ScanTimeLoad` 는 *"부하를 주기 위한 더미 연산"* 이라고 명시되어 있다. 즉 실 생산 로직이 아니라 **데이터 포맷·스캔타임·핸드셰이크를 벤치에서 검증**하기 위한 프로젝트다.

---

## 3. 프로젝트 구조 — 어디에 무엇이 있나

```
S7TestProject (PLC)
├─ _root
│   ├─ Main              OB1  (LAD)  ← 진입점 (Program Cycle)
│   ├─ FC_ScanTimeLoad   FC1  (SCL)  스캔타임 부하 더미 연산
│   ├─ S7Test            FB3  (SCL)  메인 상태머신 (IDLE/STACK/OUT)
│   ├─ S7Test_DB         iDB2        S7Test 인스턴스 DB
│   └─ DB_Test           gDB1        설정/시운전 파라미터 (HMI 입력)
│
└─ _root/GAP                          ← GAP 비전 데이터 서브시스템
    ├─ FB_makeHeader     FB1  (SCL)  통신 헤더(Heartbeat·시각·사이클타임) 생성
    ├─ FB_makeGapData    FB2  (SCL)  GAP 측정 데이터 시뮬레이터
    ├─ DB_GapPV          gDB8000     ★ PLC↔호스트 데이터 계약 (PV: Process Value)
    ├─ DB_Handshake      gDB8001     핸드셰이크 비트
    ├─ DB_CompSV         gDB8010     보정 설정값 (SV: Set Value)
    └─ DB_CompSV_AN      gDB8011     보정 설정값 (Anode)
```

구조 철학: **기능 분해(functional decomposition)**. 루트에는 진입점/상태머신/부하테스트, `GAP` 그룹에는 비전 데이터 파이프라인과 그 통신 DB(8000번대 번호 블록)를 모았다. DB 번호 대역이 의미를 가진다: `8000`=PV, `8001`=Handshake, `8010/8011`=보정 SV.

---

## 4. 명명 규칙

| 구분 | 규칙 | 예시 |
|---|---|---|
| 상수 | `CST_<영역>_<값>` (대문자 snake) | `CST_STATE_IDLE`, `CST_STACK_START_ON`, `CST_PLC_STATE_WET_RUN` |
| 인스턴스 정적변수 | `st<Name>` (camel, st 접두) | `stProductionState`, `stHeartbeat`, `stRising1Hz` |
| 입력 파라미터 | `i<Name>` 또는 소문자 | `iEnable`, `iLoopCount`, `enable` |
| 전역 DB | `DB_<Name>` (Pascal) | `DB_GapPV`, `DB_Handshake`, `DB_CompSV` |
| 사용자 데이터타입(UDT) | `type<Name>` | `typeGapPvHeader`, `typeGapSpec`, `typeGapPV`, `typeGapData` |
| 호스트 공유 필드 | `PLC_<Name>` (PLC→호스트 방향 명시) | `PLC_Heartbeat`, `PLC_RunningState`, `PLC_CaptureSeq` |

케이스 스타일은 혼용이지만 일관적: 상수는 UPPER_SNAKE, 변수는 camelCase(st 접두), 타입/DB는 Pascal.

---

## 5. 라이브러리 / 시스템 함수 의존성

인하우스 라이브러리(LAF/LUC/MC_ 등)는 **사용하지 않는다**. 표준 IEC + S7 시스템 함수만 쓴다:

| 함수 | 용도 | 사용처 |
|---|---|---|
| `R_TRIG` / `F_TRIG` | 클록 상승/하강 엣지 검출 | 전 FB (Clock_1Hz/2Hz 기반) |
| `RD_SYS_T` / `RD_LOC_T` | UTC / 로컬 시각 읽기 | FB_makeHeader |
| `RT_INFO` (MODE 25) | 현재 사이클 타임(µs) | FB_makeHeader |
| `SQRT`, `DINT_TO_REAL`, `**` | 더미 부동소수점 부하 | FC_ScanTimeLoad |
| `LTIME_TO_UINT` | 사이클타임 단위 환산(/1000) | FB_makeHeader |

시스템 클록 메모리(`Clock_1Hz`, `Clock_2Hz`)와 `FirstScan` 시스템 비트를 전제로 한다 → CPU 속성에서 **Clock memory byte / System memory byte 활성화**가 필요.

---

## 6. 프로그램 흐름 — OB로 본 골격

OB는 `Main` (OB1, Program Cycle) 하나. 매 스캔:

```
Main (OB1)
 ├─ "S7Test_DB"(S7Test());        ← 메인 상태머신 1회 실행
 └─ FC_ScanTimeLoad(iEnable := "DB_Test".loadTestEnable,
                    iLoopCount := "DB_Test".loadLoopCount);  ← 스캔 부하 테스트
```

S7Test(FB) 내부 흐름:
1. **INITIAL** (`FirstScan`): DB_GapPV.Header 초기화(Magic=0, PLC_Alive, StackStart/Done=OFF…), 그 외엔 Magic=`16#A55A`, Version=100, Length=640, RecipeId=1, TargetStackCount←DB_Test.
2. **SETTING_TIMER**: `stRising1Hz`(R_TRIG, Clock_1Hz).
3. **SETTING_RUNNING_STATE**: `DB_GapPV.Header.PLC_RunningState ← DB_Test.runningState` (0:Stop / 1:Wet Run / 2:Dry Run / 3:Manual).
4. **STATE_MACHINE** (CASE stProductionState):
   - `IDLE(1)`: StackIndex/Start/Done 리셋 → RunningState>Stop 이면 `STACK` 으로.
   - `STACK(10)`: `Inst_makeGapData(enable:=TRUE)` 호출(측정 데이터 생성) → StackDone 이면 `OUT` 으로.
   - `OUT(20)`: 1Hz 마다 stOutDelay 증가, ≥5 이면 StackDone 해제 후 `STACK` 복귀(연속 사이클).
5. 마지막에 항상 `Inst_makeHeader(enable:=TRUE)` 호출 → 헤더(Heartbeat/시각/사이클타임) 갱신.

> 참고: 구버전 "Clock_500mHz 상승엣지마다 Stack 조건 검사" 로직은 주석 처리되어 있고, 현재는 CASE 상태머신으로 대체됨.

---

## 7. 데이터 계약 — DB_GapPV (가장 중요)

PLC가 호스트로 내보내는 메모리 레이아웃. 3계층 UDT 구성:

- **Header** (`typeGapPvHeader`): 프로토콜·핸드셰이크
  - 식별: `Magic(16#A55A)`, `Version(100)`, `Length(640)`
  - 생존/시간: `PLC_Alive`, `PLC_Heartbeat`, `PLC_TimeUTC/LOCAL`, `PLC_CycleTimeMs`
  - 시퀀스: `PLC_CaptureSeq`, `PLC_CompRsltSeqAck`
  - 공정: `PLC_RunningState`, `ProductIndex`, `RecipeId`, `StackIndex`, `TargetStackCount`, `StackStart`, `StackDone`, `StackType`, `CompensationEnable`
  - 오류: `PLC_ErrCode`, `VisionErrCodeAn`, `VisionErrCodeCa`
- **GapSpecAn / GapSpecCa** (`typeGapSpec`): 양극/음극 갭 **사양(기준)**. 각각 `Left`/`Right`(`typeGapPV`) 안에 `EtrTopX/Y`, `EtrBottomX/Y`, `EtrT`, `SepaTopX/Y`, `SepaBottomX/Y`, `SepaT` (모두 DInt).
- **GapDataAn / GapDataCa** (`typeGapData`): 양극/음극 갭 **실측값** + `GapJudgeResult`(판정).

`typeGapPV` = 한 코너 단위 측정 묶음(전극 Top/Bottom + 분리막 Top/Bottom + 두께 T). `An`/`Ca` × `Left`/`Right` 로 4개 영역을 측정/판정하는 구조.

---

## 8. 어디서부터 읽을지

1. **`Main`** — `exports/S7TestProject/_root/Main.xml`
   진입점. 전체가 단 2줄 호출이라 호출 구조를 5초에 파악. → *읽고 나면 S7Test와 FC_ScanTimeLoad의 관계를 안다.*
2. **`S7Test`** — `exports/S7TestProject/_root/S7Test.xml`
   메인 상태머신. IDLE/STACK/OUT 전이와 DB_GapPV.Header 초기화 로직. → *읽고 나면 스택 1사이클이 어떻게 흐르는지 안다.*
3. **`DB_GapPV`** — `exports/S7TestProject/_root/GAP/DB_GapPV.xml`
   호스트와의 통신 계약. → *읽고 나면 이 PLC가 외부로 무엇을 내보내는지 안다.*
4. **`FB_makeGapData`** — `exports/S7TestProject/_root/GAP/FB_makeGapData.xml`
   측정값 시뮬레이션(삼각파 ±30 → ×1000)과 An/Ca·Left/Right 필드 채우기. → *읽고 나면 가짜 데이터 생성 규칙을 안다.*
5. **`FB_makeHeader`** — `exports/S7TestProject/_root/GAP/FB_makeHeader.xml`
   Heartbeat·시각·사이클타임 헤더 생성. → *읽고 나면 호스트가 PLC 생존을 어떻게 확인하는지 안다.*

---

## 9. 치트시트

**약어**
- `Etr` = Electrode(전극), `Sepa` = Separator(분리막), `T` = Thickness/두께
- `An` = Anode(음극), `Ca` = Cathode(양극)
- `PV` = Process Value(실측), `SV` = Set Value(설정값), `Comp` = Compensation(보정)
- `Spec` = 기준 사양 / `Data` = 실측+판정
- `OB`=조직블록, `FB`=함수블록(인스턴스DB 보유), `FC`=함수(무상태), `gDB`=전역DB, `iDB/DI`=인스턴스DB, `UDT(type*)`=사용자 데이터타입
- `mEDAS_DA` = 상위 측정 데이터 수집(Data Acquisition) 시스템

**상태 코드**
- ProductionState: `1`=IDLE, `10`=STACK, `20`=OUT
- RunningState: `0`=Stop, `1`=Wet Run, `2`=Dry Run, `3`=Manual
- StackStart/StackDone: `16#0`=OFF, `16#1`=ON

**DB 번호 대역**
- `8000`=DB_GapPV(PV), `8001`=DB_Handshake, `8010`=DB_CompSV, `8011`=DB_CompSV_AN

**시뮬레이션 규칙 (FB_makeGapData)**
- 2Hz 하강엣지(=500ms)마다 1캡처 → StackIndex/CaptureSeq +1
- StackIndex ≥ TargetStackCount → ProductIndex +1, StackIndex 0, StackDone ON
- 측정값 stValue = stCount × 1000, stCount는 -30↔+30 삼각파(방향 반전)

---

## 10. 알아둘 점 / 주의

- **테스트 프로젝트**다. 실 비전 데이터가 아닌 시뮬레이션 값이며, `FC_ScanTimeLoad` 는 의도적으로 CPU 부하를 거는 더미 루프다(스캔타임 영향 검증용).
- 시스템 클록/메모리 비트(`Clock_1Hz`, `Clock_2Hz`, `FirstScan`)에 의존 → 다른 CPU로 옮길 때 클록·시스템 메모리 바이트 설정 확인 필요.
- `DB_Test` 가 사실상 HMI/시운전 입력 역할(runningState, TargetStackCount, loadTestEnable, loadLoopCount).
- `GapSpecCa`/`GapDataCa`(양극)는 구조는 정의돼 있으나 시뮬레이터가 어디까지 채우는지는 FB_makeGapData 후반부(본 분석에서 미열람 구간)에서 확인 필요.
