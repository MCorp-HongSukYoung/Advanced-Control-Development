# S7TestProject — 블록 상세 분석

> 생성: 2026-06-09 by /analyze-plc (라이브 세션 + export XML 정독)
> 소스: `exports/S7TestProject/` (TIA Portal V20 Update 4 export)
> 범위: 11개 블록 전수 (OB 1 / FC 1 / FB 3 / DB 6). 코드 블록은 NetworkSource(StructuredText) 토큰을 SCL로 복원, DB는 인터페이스 정독.
> 함께 보기: [S7TestProject.md](S7TestProject.md) (온보딩 개요)

---

## 0. 전체 데이터 흐름 (요약)

```
        ┌───────────────────────── PLC (S7TestProject) ─────────────────────────┐
        │  Main(OB1)                                                             │
        │    ├─ S7Test(FB)  ── 상태머신 IDLE/STACK/OUT                            │
        │    │     ├─ Inst_makeGapData(FB) ── 측정 시뮬레이터                     │
        │    │     └─ Inst_makeHeader(FB)  ── 헤더(Heartbeat/시각/사이클)         │
        │    └─ FC_ScanTimeLoad ── 스캔타임 부하 더미                             │
        └────────────────────────────────────────────────────────────────────────┘
              │ writes                              ▲ reads
              ▼                                     │
        DB_GapPV(gDB8000)  ───────────▶  상위 호스트(mEDAS_DA / PC / Vision)
          · Header.PLC_*  (생존/시퀀스/공정상태)        │ writes
          · GapSpec/GapData/AlignPv (An·Ca)             ▼
                                                  DB_Handshake(gDB8001)  PC_* (호스트→PLC)
                                                  DB_CompSV(gDB8010)     스택별 X/Y/T 보정값
                                                  DB_CompSV_AN(gDB8011)  (Anode)
```

핵심: PLC는 `DB_GapPV` 에 자기 상태와 (시뮬레이션) 측정값을 쓰고, 호스트는 `DB_Handshake`(생존/ACK/에러)와 `DB_CompSV*`(보정 오프셋)를 써서 응답하는 **양방향 핸드셰이크 데이터 계약**.

---

## ① Main — OB1 (LAD/SCL, Program Cycle, No.1)

**역할**: 사이클 진입점. 본체는 두 호출뿐인 얇은 디스패처.

**인터페이스**: 시스템 제공 입력 `Initial_Call`, `Remanence` (미사용). Temp: plcTime/plcLocalTime/tempStatus/infoData (선언만, 미사용 — 잔재).

**복원 코드**
```scl
// Network 1 (LAD): 비어 있음
// Network 2 (SCL):
"S7Test_DB"();                                          // 상태머신 FB 1회 실행
FC_ScanTimeLoad(iEnable    := "DB_Test".loadTestEnable,
                iLoopCount := "DB_Test".loadLoopCount); // 스캔타임 부하 테스트
```

**해설**
- `"S7Test_DB"()` — FB `S7Test`를 인스턴스DB `S7Test_DB`로 호출. 파라미터가 없어 실로직은 전부 내부.
- `FC_ScanTimeLoad(...)` — `DB_Test.loadTestEnable`이 ON일 때만 부하 연산 수행(진단용).

> **요약**: "상태머신 1회 + 부하테스트 1회"를 부르는 진입점.

---

## ② S7Test — FB3 (SCL, No.3) · 메인 상태머신

**역할**: 스택 1사이클을 모사하는 3-state CASE 머신 + `DB_GapPV.Header` 초기화/갱신. 인스턴스DB = `S7Test_DB`.

**인터페이스 (Static)**
| 변수 | 타입 | 의미 |
|---|---|---|
| `stProductionState` | UInt | 현재 상태 (시작값 `CST_STATE_IDLE`) |
| `stOutDelay` | Int | OUT 지연 카운터 |
| `Inst_makeGapData` | `FB_makeGapData` | 측정 시뮬레이터 인스턴스 |
| `Inst_makeHeader` | `FB_makeHeader` | 헤더 생성기 인스턴스 |
| `stRising1Hz` | R_TRIG | 1Hz 상승엣지 |

**상수**: 상태 `IDLE=1 / STACK=10 / OUT=20`, PLC상태 `STOP=0 / WET_RUN=1 / DRY_RUN=2 / MANUAL=3`, `STACK_START/DONE_OFF=16#0 / _ON=16#1`, `CST_PLC_ALIVE=1`.

**복원 코드**
```scl
REGION INITIAL
    IF "FirstScan" = TRUE THEN
        #stProductionState := CST_STATE_IDLE;
        "DB_GapPV".Header.Magic              := 0;            // 무효 (초기화 중)
        "DB_GapPV".Header.PLC_Alive          := CST_PLC_ALIVE;
        "DB_GapPV".Header.PLC_CaptureSeq     := 0;
        "DB_GapPV".Header.PLC_CompRsltSeqAck := 0;
        "DB_GapPV".Header.PLC_RunningState   := CST_PLC_STATE_STOP;
        "DB_GapPV".Header.ProductIndex       := 0;
        "DB_GapPV".Header.StackIndex         := 0;
        "DB_GapPV".Header.StackStart         := CST_STACK_START_OFF;
        "DB_GapPV".Header.StackDone          := CST_STACK_DONE_OFF;
    ELSE
        "DB_GapPV".Header.Magic            := 16#A55A;        // 유효 패킷 표식
        "DB_GapPV".Header.Version          := 100;
        "DB_GapPV".Header.Length           := 640;
        "DB_GapPV".Header.RecipeId         := 1;
        "DB_GapPV".Header.TargetStackCount := "DB_Test".TargetStackCount;  // Stack 갯수 지정
    END_IF;
END_REGION

REGION SETTING_TIMER
    #stRising1Hz(CLK := "Clock_1Hz");
END_REGION

REGION SETTING_RUNNING_STATE                  // 0:Stop 1:WetRun 2:DryRun 3:Manual
    "DB_GapPV".Header.PLC_RunningState := "DB_Test".runningState;
END_REGION

// [주석 처리됨] 구버전 Clock_500mHz 상승엣지 기반 Stack 시작/완료 검사 로직

REGION STATE_MACHINE
    CASE #stProductionState OF
        CST_STATE_IDLE:                                       // 1
            "DB_GapPV".Header.StackIndex := 0;
            "DB_GapPV".Header.StackStart := CST_STACK_START_OFF;
            "DB_GapPV".Header.StackDone  := CST_STACK_DONE_OFF;
            IF ("DB_GapPV".Header.PLC_RunningState = CST_PLC_STATE_STOP) THEN
                #stProductionState := CST_STATE_IDLE;
            ELSE
                #stProductionState := CST_STATE_STACK;
            END_IF;

        CST_STATE_STACK:                                      // 10
            IF ("DB_GapPV".Header.StackStart = CST_STACK_START_OFF) THEN
                "DB_GapPV".Header.StackStart := CST_STACK_START_ON;
                "DB_GapPV".Header.StackIndex := 0;
            END_IF;
            #Inst_makeGapData(enable := TRUE);                // ★ 측정 데이터 생성
            IF ("DB_GapPV".Header.PLC_RunningState = CST_PLC_STATE_STOP) THEN
                #stProductionState := CST_STATE_IDLE;
            ELSIF ("DB_GapPV".Header.StackDone = CST_STACK_DONE_ON) THEN
                #stOutDelay := 0;
                #stProductionState := CST_STATE_OUT;
            END_IF;

        CST_STATE_OUT:                                        // 20
            IF (#stRising1Hz.Q = TRUE) THEN
                #stOutDelay := #stOutDelay + 1;               // 1Hz 카운트
            END_IF;
            IF (#stOutDelay >= 5) THEN                        // 5초 후 리셋
                "DB_GapPV".Header.StackDone  := CST_STACK_DONE_OFF;
                "DB_GapPV".Header.StackStart := CST_STACK_START_OFF;
            END_IF;
            IF ("DB_GapPV".Header.PLC_RunningState = CST_PLC_STATE_STOP) THEN
                #stProductionState := CST_STATE_IDLE;
            ELSE
                IF ("DB_GapPV".Header.StackDone = CST_STACK_DONE_OFF) THEN
                    #stProductionState := CST_STATE_STACK;    // 다음 제품 순환
                END_IF;
            END_IF;
    END_CASE;
END_REGION

#Inst_makeHeader(enable := TRUE);             // 매 스캔 헤더 갱신
```

**상태 전이도**
```
       RunningState<>Stop           StackDone=ON
 IDLE ───────────────────▶ STACK ───────────────▶ OUT
  ▲                           ▲                      │ 5초(1Hz×5) 후
  └──── RunningState=Stop ────┴──────◀──────────────┘  StackDone 해제→STACK
        (어느 상태든 Stop이면 IDLE 복귀)
```

**관찰**
- `Magic`: 첫 스캔엔 0, 두 번째 스캔부터 `16#A55A`. 호스트는 이 값으로 PLC 초기화 완료를 판별.
- 측정의 "언제"는 S7Test가, "무엇을"은 `Inst_makeGapData`가 담당(관심사 분리).
- 모든 입력은 `DB_Test`, 모든 출력은 `DB_GapPV.Header` (전역 DB 결합).

> **요약**: 측정·헤더를 하위 FB에 위임하는 오케스트레이터, 안전상 Stop→IDLE 항상 복귀.

---

## ③ FB_makeGapData — FB2 (SCL, No.2) · 측정 데이터 시뮬레이터

**역할(주석 그대로)**: *"GAP Vision data update simulator — 주기적으로 GAP Vision 측정 데이터를 생성"*. 실 카메라 없이 삼각파 값으로 모든 측정 필드를 채운다.

**인터페이스**: Input `enable`(미사용; 호출부에서 TRUE 고정). Static: `stFallingEdge2Hz`(F_TRIG), `stDirection`(Int,초기 1), `stCount`(Int), `stValue`(Int), `stGapVisionOK`(Bool). 상수 `CST_STACK_START/DONE_*`.

**REGION 구성 (실행 순서)**
| # | REGION | 동작 |
|---|---|---|
| 1 | `SETTING_TIMER` | `stFallingEdge2Hz(CLK := "Clock_2Hz")` → 500ms 주기 |
| 2 | `MAKE_STACK_STATE` | 하강엣지 시 `stGapVisionOK := TRUE`, 아니면 FALSE (1스캔 펄스 - 500ms) |
| 3 | `MAKE_STACK_INFO` | OK일 때 `PLC_CaptureSeq++`(비전데이터 캡처 완료 시 증가 변수), `StackIndex++`(제품 현재 적층 위치); `StackIndex >= TargetStackCount`(제품 완성 목표 적층 개수) 면 `ProductIndex++`, `StackIndex:=0`, `StackDone:=ON` |
| 4 | `CREATE_COUNT` | OK일 때 `stCount += stDirection`; ±30 도달 시 방향 반전(삼각파) |
| 5 | `MAKE_DATA` | `stValue := stCount * 1000` |
| 6 | `GAP_SPEC_AN` | `DB_GapPV.GapSpecAn.Left/Right.*`(음극 전극의 GAP 기준 값) ← stValue |
| 7 | `GAP_SPEC_CA` | `DB_GapPV.GapSpecCa.Left/Right.*`(양극 전극의 GAP 기준 값) ← stValue |
| 8 | `GAP_SPEC_AN` (중복 라벨) | 다시 `GapSpecAn.*`(음극 전극의 GAP 기준 값) ← stValue **(아래 주의)** |
| 9 | `GAP_DATA_AN` | `DB_GapPV.GapDataAn.Left/Right.*`(음극 전극의 GAP 측정 값) ← stValue (실측값 슬롯) |
| 10 | `GAP_DATA_CA` | `DB_GapPV.GapDataCa.Left/Right.*`(양극 전극의 GAP 기준 값) ← stValue |
| 11 | `ALIGN_PV_AN` | `DB_GapPV.AlignPvAn.*`(음극 전극의 Align 측정값) ← stValue (정렬/픽앤플레이스 PV) |
| 12 | `ALIGN_PV_CA` | `DB_GapPV.AlignPvCa.*`(양극 전극의 Align 측정값) ← stValue |

**복원 코드 (핵심부)**
```scl
REGION SETTING_TIMER
    #stFallingEdge2Hz(CLK := "Clock_2Hz");
END_REGION

REGION MAKE_STACK_STATE       // 500ms마다 Stack 1장 + GAP Vision 갱신으로 정의
    IF (#stFallingEdge2Hz.Q = TRUE) THEN  #stGapVisionOK := TRUE;
    ELSE                                  #stGapVisionOK := FALSE;  END_IF;
END_REGION

REGION MAKE_STACK_INFO
    IF (#stGapVisionOK = TRUE) THEN
        "DB_GapPV".Header.PLC_CaptureSeq := "DB_GapPV".Header.PLC_CaptureSeq + 1;
        "DB_GapPV".Header.StackIndex     := "DB_GapPV".Header.StackIndex + 1;
        IF ("DB_GapPV".Header.StackIndex >= "DB_GapPV".Header.TargetStackCount) THEN
            "DB_GapPV".Header.ProductIndex := "DB_GapPV".Header.ProductIndex + 1;
            "DB_GapPV".Header.StackIndex   := 0;
            "DB_GapPV".Header.StackDone    := CST_STACK_DONE_ON;   // 1제품 완료
        END_IF;
    END_IF;
END_REGION

REGION CREATE_COUNT
    IF (#stGapVisionOK = TRUE) THEN
        #stCount := #stCount + #stDirection;        // +1 증가 / -1 감소
        IF (#stCount >= 30)  THEN #stCount := 30;  #stDirection := -1; END_IF;
        IF (#stCount <= -30) THEN #stCount := -30; #stDirection := 1;  END_IF;
    END_IF;
END_REGION

REGION MAKE_DATA
    #stValue := #stCount * 1000;                    // -30000 ~ +30000 삼각파
END_REGION

REGION GAP_SPEC_AN   // (CA / GAP_DATA_* / ALIGN_PV_* 모두 동일 패턴)
    "DB_GapPV".GapSpecAn.Left.EtrTopX    := #stValue;
    "DB_GapPV".GapSpecAn.Left.EtrTopY    := #stValue;
    "DB_GapPV".GapSpecAn.Left.EtrBottomX := #stValue;
    // ... EtrBottomY, EtrT(Theta), SepaTopX/Y, SepaBottomX/Y, SepaT(Theta) (Left)
    "DB_GapPV".GapSpecAn.Right.EtrTopX   := #stValue;
    // ... Right 동일 10개 필드
END_REGION
```

**관찰 / 주의**
- 모든 측정 필드(Spec/Data/Align × An/Ca × Left/Right)에 **동일한 `stValue` 한 값**을 넣는 단순 시뮬레이터다. 실제 검사 의미는 없고 데이터 파이프라인·바이트 레이아웃 검증용.
- ⚠️ **REGION #8 `GAP_SPEC_AN` 중복**: `GAP_SPEC_AN`이 #6과 #8 두 번 나타나며 둘 다 `GapSpecAn`을 같은 값으로 덮어쓴다. 복사-붙여넣기 잔재로 보이며 기능상 무해하지만, 의도가 `GapDataAn` 등 다른 타겟이었다면 **버그**일 수 있다 → 원작자 확인 권장.
- `GapJudgeResult`, `EtrWidth`, `VisionErrCode*` 필드는 이 FB에서 **쓰지 않음**(구조에는 존재).
- `enable` 입력은 받지만 본문에서 게이팅에 쓰지 않음(항상 실행). 호출부(S7Test STACK 상태)에서만 호출되므로 실질 게이팅은 상위에서 함.

> **요약**: 500ms마다 삼각파(±30000) 한 값으로 전 측정 필드를 채우는 데이터 포맷 시뮬레이터. 중복 REGION 1건 점검 필요.

---

## ④ FB_makeHeader — FB1 (SCL, No.1) · 통신 헤더 생성

**역할(주석)**: *"mEDAS_DA에서 주기적으로 수집하는 GAP Vision data의 header를 생성"*.

**인터페이스**: Input `enable`(미사용). Static: `stUtcTime`/`stLocalTime`(DATE_AND_TIME), `stCycleData`(LTime), `stHeartbeat`(UDInt), `stRising500ms`(R_TRIG). Temp `tempStatus`(Int, 시스템함수 리턴값).

**복원 코드**
```scl
REGION MAKE_Heartbeat
    #stRising500ms(CLK := "Clock_2Hz");             // 500ms 상승엣지
    IF (#stRising500ms.Q = TRUE) THEN
        #stHeartbeat := #stHeartbeat + 1;           // 500ms마다 +1
    END_IF;
END_REGION

REGION GET_TIME                                     // DATE_AND_TIME = 8byte BCD
    #tempStatus := RD_SYS_T(OUT => #stUtcTime);     // UTC
    #tempStatus := RD_LOC_T(OUT => #stLocalTime);   // Local
END_REGION

REGION GET_CYCLE_TIME                               // MODE 25 = 현재 사이클타임(µs)
    #tempStatus := RT_INFO(MODE := 25, OB := 1, INFO := #stCycleData);
END_REGION

REGION WRITE_DB
    "DB_GapPV".Header.PLC_Heartbeat  := #stHeartbeat;
    "DB_GapPV".Header.PLC_TimeUTC    := #stUtcTime;
    "DB_GapPV".Header.PLC_TimeLOCAL  := #stLocalTime;
    "DB_GapPV".Header.PLC_CycleTimeMs := LTIME_TO_UINT(#stCycleData / 1000);  // µs→ms
END_REGION
```

**관찰**
- `PLC_Heartbeat`는 500ms마다 증가하는 카운터 → 호스트가 PLC 생존(통신 끊김) 감시에 사용.
- 사이클타임: `RT_INFO MODE 25`는 µs(LTime) → `/1000` 후 UInt(ms)로 환산해 기록.
- `tempStatus`는 시스템함수 에러코드를 받지만 **검사하지 않음**(에러 무시).

> **요약**: 생존(Heartbeat)·시각(UTC/Local)·성능(사이클타임)을 헤더에 매 스캔 기록하는 텔레메트리 블록.

---

## ⑤ FC_ScanTimeLoad — FC1 (SCL, No.1) · 스캔타임 부하 더미

**역할(주석)**: *"부하를 주기 위한 더미 연산"* — CPU 스캔타임을 인위적으로 늘려 영향 검증.

**인터페이스**: Input `iEnable`(Bool), `iLoopCount`(DInt). Temp `tempReal`(Real), `tempDInt`(DInt). Return Void.

**복원 코드**
```scl
IF NOT #iEnable THEN
    RETURN;                          // 비활성 시 즉시 종료
END_IF;

// 부하를 주기 위한 더미 연산
FOR #tempDInt := 1 TO #iLoopCount DO
    // CPU에 연산 부하를 주기 위한 부동소수점 계산 (Dummy)
    #tempReal := SQRT(DINT_TO_REAL(#tempDInt)) * 3.141592;
    #tempReal := #tempReal ** 2.0;
END_FOR;
```

**관찰**
- 결과(`tempReal`)는 어디에도 저장하지 않음 → 순수하게 CPU 시간을 소모하는 것이 목적.
- `iLoopCount`로 부하량 조절(`DB_Test.loadLoopCount`로 HMI에서 설정).

> **요약**: 운영 무관, 스캔타임 스트레스 테스트용 의도적 더미.

---

## ⑥ 데이터 블록 (DB) 6종

> **정본 교차검증**: 아래 의미·단위·오프셋은 인터페이스 설계 정본
> `산출물_V0.8.2_PowerCo_STC_260528_R0_민훈기_Stack보상기능_데이터구조.xlsx`
> (PLC↔PC 데이터 구조, 2026-05-28)와 대조해 확정. PLC export(S7TestProject)와
> 정본이 어긋나는 항목은 §7-A "정본 대비 불일치"에 정리.
> 측정값은 전부 정수(raw, DecimalPlace=0, 단위 미지정).

### DB_GapPV — gDB8000 · ★ PLC→호스트 데이터 계약 (PV), 프레임 640 byte
3계층 UDT.
- **Header** (`typeGapPvHeader`, offset 0~): `Magic(0xA55A 시그니처) / Version(=100) / Length(=640, 전체 프레임 byte) / PLC_TimeUTC·PLC_TimeLOCAL(DATE_AND_TIME, 8byte BCD) / PLC_Alive / PLC_Heartbeat / PLC_CaptureSeq(캡처 완료마다 +1) / PLC_CompRsltSeqAck(PC 보상 적용 완료 ACK) / PLC_RunningState(0:Stop 1:WetRun 2:DryRun 3:Manual 4:Error) / PLC_CycleTimeMs / ProductIndex(제품 순번) / RecipeId / StackIndex(1~Target) / TargetStackCount / CompensationEnable / StackStart / StackDone / StackType(0:Cathode 1:Anode) / ManualCompCount / AuotCompCount(⚠️오타) / PLC_ErrCode / VisionErrCodeAn(음극) / VisionErrCodeCa(양극)` (+ Reserved 다수)
- **GapSpecAn / GapSpecCa** (`typeGapSpec`): 음극(An)/양극(Ca) 전극 갭 **기준값**. `EtrWidth`(전극 폭 기준) + `Left`/`Right`(`typeGapPV`) + Spare.
- **GapDataAn / GapDataCa** (`typeGapData`): 음극/양극 **실측값** + `GapJudgeResult`(적층 전극 GAP 판정 결과) + `EtrWidth`(폭 측정).
- **AlignPvAn / AlignPvCa** (`typeAlignPV`): 얼라인 테이블 정렬 PV — `AlignX/Y/TReadyPos`(준비완료 위치), `AlignX/Y/TActualPos`(보정 후 위치), `MeasResultX/Y/T`(비전 측정 결과).
- `typeGapPV` (한 코너 단위, 모두 DInt): `EtrTopX/Y`·`EtrBottomX/Y`(전극 상/하단 X·Y Gap), `EtrT`(**전극 Theta=회전각 Gap**), `SepaTopX/Y`·`SepaBottomX/Y`(분리막 상/하단), `SepaT`(**분리막 Theta Gap**) + spare1~4.
  - ⚠️ **정정**: `EtrT`/`SepaT`의 `T`는 두께(Thickness)가 아니라 **Theta(회전각)**. 즉 X·Y 위치 Gap + Theta 각도 Gap을 측정하는 구조.

### DB_Handshake — gDB8001 · 호스트(PC)→PLC 핸드셰이크
| 필드 | 타입 | offset | 의미 |
|---|---|---|---|
| `PC_Alive` | UDInt | 0 | 호스트 생존 (정본 표에는 미기재, offset 0 슬롯) |
| `PC_Heartbeat` | UDInt | 4 | 호스트가 주기적으로 +1 |
| `PC_CompRsltSeq` | UDInt | 8 | 새 보상 데이터를 PLC에 쓸 때 PC가 +1 (PLC의 `PLC_CompRsltSeqAck`가 ACK) |
| `PC_CaptureSeqAck` | UDInt | 12 | 특정 CaptureSeq 수신확인 (PLC의 `PLC_CaptureSeq`에 응답) |
| `PC_ErrString` | String | 16 | PC 오류 문자열 (분석/보상 실패). **정본 비고=삭제 예정** |
| `PC_ErrCode` | Int | 272 | PC 오류 코드 |

→ `DB_GapPV.Header`의 `PLC_*`와 **대칭 쌍**. Seq↔SeqAck로 캡처/보상 핸드셰이크 완성.

### DB_CompSV — gDB8010 · 보정 설정값 (호스트→PLC)
- `CompSeq` (UDInt) + `CompSV` : **`Array[1..200] of typeCompSV`** (스택 최대 200장)
- `typeCompSV` (PLC export) = `StackCompX`, `StackCompY`, `StackCompT`(Int) + `Reserved`(Int) — 장별 **X/Y/Theta 정렬 보정 오프셋**.
  - ⚠️ 정본 V0.8에서는 4번째 멤버가 `Reserved` → **`SepaX`(Sepa 보정값)** 로 변경됨. PLC 미반영.

### DB_CompSV_AN — gDB8011 · 보정 설정값 (Anode)
- DB_CompSV와 동일 구조의 음극(Anode)용. (정본상 보정 DB의 An/Ca 분화 방식은 §7-A 참조)

### DB_Test — gDB1 · 시운전/HMI 입력
| 필드 | 타입 | 용도 |
|---|---|---|
| `runningState` | UInt | S7Test가 `PLC_RunningState`로 복사 (0~3) |
| `TargetStackCount` | UInt | 제품당 목표 스택 장수 |
| `loadLoopCount` | DInt | FC_ScanTimeLoad 부하량 |
| `loadTestEnable` | Bool | 부하 테스트 ON/OFF |

### S7Test_DB — iDB2 · S7Test 인스턴스 DB
- FB `S7Test`의 인스턴스(상태·엣지·하위 FB 인스턴스 보관). 사용자가 직접 편집하지 않음.

---

## 7-A. 정본(엑셀 V0.8.2) 대비 불일치

> 출처: `산출물_V0.8.2_PowerCo_STC_260528_R0_민훈기_Stack보상기능_데이터구조.xlsx`.
> 정본 이력: V0.5.0(초도, 유덕재) → V0.6.0 PLC_Time 추가 → V0.7.0 CompCount→CompSeq → V0.8.0 Sepa 보정 추가(민훈기) → V0.8.1 PnP Pick/Place 위치 추가.
> PLC export(S7TestProject)는 이보다 앞선 테스트 구현본으로 보이며 다음이 어긋남:

| # | 항목 | PLC export | 정본 V0.8.2 | 성격 |
|---|---|---|---|---|
| D1 | 카운터 오타 | `AuotCompCount` | `AutoCompCount` | **PLC 오타 수정 필요** |
| D2 | 보상 enable | `CompensationEnable` | `EtrCompensationEnable` (+ `SepaCompensatonEnable` 신규) | 이름/분화 |
| D3 | Align X 실위치 | `PnpXActualPos` | `AlignXActualPos` (+ `PnP_PickPos`/`PnP_PlacePos` 별도 신규) | 이름/구조 |
| D4 | RunningState | 상수 0~3만 정의 | 0~3 **+ 4=Error** | PLC 상수 누락 |
| D5 | `typeCompSV` 4번째 | `Reserved`(Int) | `SepaX`(Int, Sepa 보정) | PLC 미반영 |
| D6 | 신규 필드 | 없음 | `PLC_PPM`·`UserLevel`·`EtrModel`·`StackedCellId`·`SepaWidth/Height`·`EtrHeight`·`SepaPv`(`SepaReadyPos`/`SepaActualPos`) | 설계중(오프셋 미정, "협의 필요") |

### 정본 엑셀 자체의 오류 (스펙 측 점검)
- **CompSignal 시트**: `StackCompT` 오프셋이 200개 배열 전 요소에서 **`12`로 고정**(복붙 실수). 실제론 12, 20, 28…로 증가해야 함.
- **DB_GapPV AlignPv**: `AlignXActualPos`만 오프셋 공란, `MeasResultX/Y/T`(580~588)가 `Align*ActualPos`(596~600)보다 오프셋이 앞서는데 표기 순서는 뒤 → 레이아웃 미확정.

## 7-B. 종합 발견 & 점검 포인트

1. **FB_makeGapData의 중복 `GAP_SPEC_AN` REGION**(#6, #8) — 복붙 잔재 의심. 한 영역이 다른 타겟(예: `GapSpecCa` 2차 또는 `GapDataAn`)이어야 했는지 점검.
2. **에러 핸들링 부재**: `RD_SYS_T`/`RD_LOC_T`/`RT_INFO`의 status를 `tempStatus`로 받지만 검사하지 않음. `PLC_ErrCode`/`VisionErrCode*`는 구조만 있고 쓰는 코드가 없음.
3. **시스템 자원 의존**: `Clock_1Hz`/`Clock_2Hz`/`FirstScan` 전제 → CPU의 클록·시스템 메모리 바이트 설정 필수.
4. **테스트 프로젝트**: 측정값은 전부 시뮬레이션 단일 값, `FC_ScanTimeLoad`는 의도적 부하. 실 생산 로직이 아니라 **데이터 계약/스캔타임/핸드셰이크 벤치 검증용**.
5. **보정 DB An/Ca 구조**: PLC는 `DB_CompSV` + `DB_CompSV_AN` 2개. 정본 CompSignal과의 An/Ca 분화·Sepa 확장(D5) 정합성 확인 필요.
