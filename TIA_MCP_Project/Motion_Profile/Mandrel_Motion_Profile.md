# Mandrel Motion Profile — Stack Table Mandrel Y/Z

> 근거: TIA Portal Openness 직접 export (2026-05-19)  
> 대상: `Cam_STACK_LC/RA_Mandrel1/2_Y/Z_GET/PUT` × 16 TO  
> 마스터: **VR04_StackLeadingAxis** (STACK Phase 전용, VR03과 별개)

---

## 1) 하드웨어 구성

### 1-1. 축 목록

| Axis | 명칭 | 역할 | TB | Phase |
|------|------|------|-----|-------|
| **Axis41** | Cathode Stack Table Mandrel01 Z | LC Mandrel1 Z 승강 | TB102 | LC_STACK 능동 |
| **Axis42** | Cathode Stack Table Mandrel02 Z | LC Mandrel2 Z 승강 | TB105 | LC_STACK 능동 |
| **Axis43** | Cathode Stack Table Mandrel01 Y | LC Mandrel1 Y 전후진 | TB123 | LC_STACK 능동 |
| **Axis44** | Cathode Stack Table Mandrel02 Y | LC Mandrel2 Y 전후진 | TB124 | LC_STACK 능동 |
| **Axis45** | Anode Stack Table Mandrel01 Z | RA Mandrel1 Z 승강 | TB132 | RA_STACK 능동 |
| **Axis46** | Anode Stack Table Mandrel02 Z | RA Mandrel2 Z 승강 | TB135 | RA_STACK 능동 |
| **Axis47** | Anode Stack Table Mandrel01 Y | RA Mandrel1 Y 전후진 | TB147 | RA_STACK 능동 |
| **Axis48** | Anode Stack Table Mandrel02 Y | RA Mandrel2 Y 전후진 | TB148 | RA_STACK 능동 |

### 1-2. 물리 배치

```
Stack Table (상면 뷰)
┌────────────────────────────────────────┐
│                                        │
│  [LC Mandrel1]    전극 적층 영역    [LC Mandrel2]  │
│  Axis43(Y)/41(Z)                 Axis44(Y)/42(Z)  │
│                                        │
│  [RA Mandrel1]                  [RA Mandrel2]      │
│  Axis47(Y)/45(Z)                Axis48(Y)/46(Z)  │
│                                        │
└────────────────────────────────────────┘
```

> Mandrel 1/2는 전극 스택 양측에 대칭 배치. 동일한 CAM 프로파일로 동시 동작.

---

## 2) CAMIN 구조

### 2-1. LC_STACK Phase (`FB_Camin_STACK_LC_STACK`, 마스터: VR04)

| CAMIN 인스턴스 | 슬레이브 축 | CAM TO | 동작 |
|---|---|---|---|
| `CAMIN_Cam_STACK_LC_Mandrel1Y_GET` | Axis43 | `Cam_STACK_LC_Mandrel1Y_GET` | LC Mandrel1 Y **능동** |
| `CAMIN_Cam_STACK_LC_Mandrel1Z_GET` | Axis41 | `Cam_STACK_LC_Mandrel1Z_GET` | LC Mandrel1 Z **능동** |
| `CAMIN_Cam_STACK_LC_Mandrel2Y_GET` | Axis44 | `Cam_STACK_LC_Mandrel2Y_GET` | LC Mandrel2 Y **능동** |
| `CAMIN_Cam_STACK_LC_Mandrel2Z_GET` | Axis42 | `Cam_STACK_LC_Mandrel2Z_GET` | LC Mandrel2 Z **능동** |
| `CAMIN_Cam_STACK_RA_Mandrel1Y_PUT` | Axis47 | `Cam_STACK_RA_Mandrel1Y_PUT` | RA Mandrel1 Y **정지** (홈) |
| `CAMIN_Cam_STACK_RA_Mandrel1Z_PUT` | Axis45 | `Cam_STACK_RA_Mandrel1Z_PUT` | RA Mandrel1 Z **정지** (홈) |
| `CAMIN_Cam_STACK_RA_Mandrel2Y_PUT` | Axis48 | `Cam_STACK_RA_Mandrel2Y_PUT` | RA Mandrel2 Y **정지** (홈) |
| `CAMIN_Cam_STACK_RA_Mandrel2Z_PUT` | Axis46 | `Cam_STACK_RA_Mandrel2Z_PUT` | RA Mandrel2 Z **정지** (홈) |

### 2-2. RA_STACK Phase (`FB_Camin_STACK_RA_STACK`, 마스터: VR04)

| CAMIN 인스턴스 | 슬레이브 축 | CAM TO | 동작 |
|---|---|---|---|
| `CAMIN_Cam_STACK_RA_Mandrel1Y_GET` | Axis47 | `Cam_STACK_RA_Mandrel1Y_GET` | RA Mandrel1 Y **능동** |
| `CAMIN_Cam_STACK_RA_Mandrel1Z_GET` | Axis45 | `Cam_STACK_RA_Mandrel1Z_GET` | RA Mandrel1 Z **능동** |
| `CAMIN_Cam_STACK_RA_Mandrel2Y_GET` | Axis48 | `Cam_STACK_RA_Mandrel2Y_GET` | RA Mandrel2 Y **능동** |
| `CAMIN_Cam_STACK_RA_Mandrel2Z_GET` | Axis46 | `Cam_STACK_RA_Mandrel2Z_GET` | RA Mandrel2 Z **능동** |
| `CAMIN_Cam_STACK_LC_Mandrel1Y_PUT` | Axis43 | `Cam_STACK_LC_Mandrel1Y_PUT` | LC Mandrel1 Y **정지** (홈) |
| `CAMIN_Cam_STACK_LC_Mandrel1Z_PUT` | Axis41 | `Cam_STACK_LC_Mandrel1Z_PUT` | LC Mandrel1 Z **정지** (홈) |
| `CAMIN_Cam_STACK_LC_Mandrel2Y_PUT` | Axis44 | `Cam_STACK_LC_Mandrel2Y_PUT` | LC Mandrel2 Y **정지** (홈) |
| `CAMIN_Cam_STACK_LC_Mandrel2Z_PUT` | Axis42 | `Cam_STACK_LC_Mandrel2Z_PUT` | LC Mandrel2 Z **정지** (홈) |

> **핵심**: 한 Phase에서는 해당 측(LC or RA) Mandrel만 움직인다. 반대 측은 PUT 프로파일(=0)로 홈 정지.

---

## 3) CAM 프로파일 데이터 (실측)

16개 TO를 분석한 결과 **실질적으로 3가지 형태**만 존재한다.

### 3-1. 고유 곡선 수

| 프로파일 | 해당 TO 수 | 비고 |
|---|---|---|
| **Y_GET** | 8개 | LC/RA, Mandrel1/2 모두 동일 |
| **Z_GET** | 8개 | LC/RA, Mandrel1/2 모두 동일 |
| **PUT (Y·Z 공통)** | 16개 → 사실상 1개 | 전 구간 Y=0·Z=0 정지 |

→ 실질 곡선: **2개** (Y_GET · Z_GET)

---

## 4) Y축 — 전후진 (GET 프로파일)

**형태: 대칭 벨 커브, VR04=180°에서 최대 전진**

| VR04 각도 | Y 값 | 설명 |
|---|---|---|
| 0° | 0.000 | 홈 위치 |
| 0°~30° | 0.000 | 홈 유지 (Flat) |
| 30° | 0.000 | 이동 시작 |
| 50° | 0.050 | 완만한 전진 시작 |
| 160° | 0.950 | 거의 최대 전진 |
| **180°** | **1.000** | **최대 전진 (전극 위치 정렬 완료)** |
| 200° | 0.950 | 복귀 시작 |
| 300° | 0.050 | 대부분 복귀 |
| 322° | 0.000 | 홈 복귀 완료 |
| 322°~360° | 0.000 | 홈 유지 (Flat) |

```
Y
1.0 |         ●180°
    |       /   \
0.9 |     /       \
    |   /           \
    |  /             \
0.0 |●─────●─────────────────────●─────●
    0°  30° 50°               300° 322° 360°
                    VR04 →
```

**특징**:
- 대칭 S자 곡선 (CubicSpline)
- 30°-322° 구간에서 전진·복귀 (양단 38° 씩 홈 유지)
- 전극 압착 시점(VR04=180°)에 완전 전진 완료

---

## 5) Z축 — 승강 (GET 프로파일)

**형태: 비대칭 다단 접근, VR04=220°에서 최대 압착**

| VR04 각도 | Z 값 | 설명 |
|---|---|---|
| 0° | 0.000 | 홈 위치 (상단) |
| 10° | 0.025 | 완속 하강 시작 |
| 38° | 0.185 | 접촉 대기 구간 |
| 43° | 0.200 | 속도 감소 제어점 |
| 100° | 0.250 | 극저속 유지 |
| 140° | 0.300 | 극저속 유지 |
| 150° | 0.350 | 급속 압착 전 준비 완료 |
| 180° | 0.850 | Y 최대 전진 시점 — Z 급속 하강 중 |
| 195° | 0.950 | 거의 최대 압착 |
| **220°** | **1.000** | **최대 압착 (Y 피크 후 40°)** |
| 240° | 0.970 | 압착 해제 시작 |
| 320° | 0.100 | 대부분 복귀 |
| 360° | 0.000 | 홈 복귀 완료 |

```
Z
1.0 |                          ●220°
    |                        /   \
0.9 |                      /      \
    |     접촉 완속구간    / 급속압착 \
0.5 |                    /            \
    |                   /               \
    |●─●───────────────●                 \
0.0 |  10°  43°  100° 150°  180°        320° 360°
                          VR04 →
```

**특징 — 3단 속도 구조**:

| 구간 | VR04 범위 | Z 변화 | 설계 의도 |
|---|---|---|---|
| **완속 접근** | 0°~150° | 0.000→0.350 | 분리막/전극 손상 방지, 최소속도 |
| **급속 압착** | 150°~220° | 0.350→1.000 | Y 전진 완료 후 짧은 시간에 전 압착력 인가 |
| **복귀** | 220°~360° | 1.000→0.000 | 압착 해제 후 홈 복귀 |

---

## 6) PUT 프로파일 — 정지

**Y_PUT 및 Z_PUT 전 변종 (8개 × 2 = 16개)**:

```
Point X=0  Y=0
Point X=360 Y=0
```

→ VR04 0°~360° 전 구간 **완전 정지**. 해당 Phase에서 반대 측 Mandrel은 CAMIN이 연결되지만 실제로는 홈에서 움직이지 않음.

---

## 7) Y/Z 타이밍 비교

```
Y  | 홈──────전진─────────────────────복귀──홈
   |          50°        180°(최대)  300°
   
Z  | 홈·완속접근·극저속──────급속압착──복귀──홈
   |    10°          150°  220°(최대)    360°

VR04: 0°      50°    150°   180°  220°       360°
                       │      │    │
                       │      │    └── Z 최대 압착
                       │      └─────── Y 최대 전진
                       └────────────── Z 급속 압착 시작
```

**핵심 시퀀스**:
1. **VR04 0°-30°**: Y 홈 유지, Z 완속 하강 시작 (전극에 천천히 접근)
2. **VR04 30°-150°**: Y 전진 시작, Z 극저속 접촉 유지 (전극·분리막 보호)
3. **VR04 150°-180°**: Y 거의 전진 완료, **Z 급속 하강** (본격 압착 시작)
4. **VR04 180°**: Y 최대 전진 (전극 위치 정렬 완료), Z=0.85 (아직 최대 미도달)
5. **VR04 180°-220°**: Y 복귀 시작, Z **최대 압착 도달** (220°)
6. **VR04 220°-322°**: Y/Z 동시 복귀
7. **VR04 322°-360°**: Y 홈 유지, Z 복귀 완료

---

## 8) Phase별 동작 요약

| Phase | 마스터 | LC Mandrel (Axis41~44) | RA Mandrel (Axis45~48) |
|---|---|---|---|
| **LC_STACK** | VR04 | **능동** — GET 프로파일 (Y·Z 이동) | **정지** — PUT 프로파일 (Y·Z = 0) |
| **RA_STACK** | VR04 | **정지** — PUT 프로파일 (Y·Z = 0) | **능동** — GET 프로파일 (Y·Z 이동) |
| **LC_RUN / RA_RUN** | VR03 | CAMIN 비활성 | CAMIN 비활성 |

---

## 9) 다른 기구와 비교

| 기구 | 마스터 | 고유 곡선 수 | 최대 위치 각도 | 설계 특징 |
|---|---|---|---|---|
| **Mandrel Y** | VR04 | 1 | 180° | 대칭 벨 커브 |
| **Mandrel Z** | VR04 | 1 | 220° | 3단 속도 (완속→급속→복귀) |
| PP Z | VR03 | 1 | 180° | 부드러운 단일 곡선 |
| PP X | VR03 | 1 | 340° | 단방향 전진 |
| Reverse Z_GET | VR03 | 1 | 22°~360° | 급속 하강 후 유지 |
| Swing Z | VR03 | 1 | 72°~288° | 압착 후 장시간 유지 |

**Mandrel Z가 다른 기구와 다른 점**:
- VR04=150° 이전의 **극저속 구간** (많은 제어점으로 속도 상한 설정) — 전극 파손 방지
- Y 피크(180°)보다 40° 뒤에 Z 피크(220°) — 수평 정렬 후 수직 압착 순서 보장

---

## 10) 참고 자료

- export 파일: `exports/PowerCo_Stack_20260430_R150_Backup/cam_exports/Cam_STACK_*Mandrel*.xml`
- CAMIN FB: `exports/PowerCo_Stack/_root/200_MotionControl/210_CAM/Stack/FB_Camin_STACK_LC_STACK.xml`
- CAMIN FB: `exports/PowerCo_Stack/_root/200_MotionControl/210_CAM/Stack/FB_Camin_STACK_RA_STACK.xml`
- 전체 동작 맥락: [`VR축_0to360_전체동작.md`](VR축_0to360_전체동작.md) (RUN Phase)
- Swing Roller 비교: [`SwingRoller_Motion_Profile.md`](SwingRoller_Motion_Profile.md)
