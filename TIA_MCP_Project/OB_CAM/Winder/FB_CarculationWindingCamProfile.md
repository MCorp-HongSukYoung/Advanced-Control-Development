````md
# FB_CarculationWindingCamProfile

## 블록 기본 정보

| 항목 | 내용 |
|---|---|
| 타입 | Functional Block (FB) |
| 이름 | FB_CarculationWindingCamProfile |
| Unit | `_root (200_MotionControl/210_CAM/Winding/)` |
| 언어 | SCL |
| 번호 | FB37 |
| 작성자 | Precision Motion Control Dept. / Lee Jin Sun |
| 이력 | 초판 2025.12.17 / 2차 수정 2025.12.23 |

---

# 한 줄 요약

JR(Jelly Roll) 단면의 높이, 폭, 회전 방향을 입력받아  
와인딩 1사이클(0°~360°) 동안 X축 2개(X1/X2)와 Z축 2개(Z1/Z2)의 CAM 포인트 배열을 삼각함수 기반으로 계산하는 CAM Profile 생성 블록이다.

---

# 주요 인터페이스

## Input

| 이름 | 타입 | 설명 |
|---|---|---|
| `in_Height` | Real | JR 단면 높이 (전극 두께 방향) |
| `in_Width` | Real | JR 단면 폭 (전극 길이 방향) |
| `in_windingDirection` | Bool | `0 = CW`, `1 = CCW` |
| `in_windingRevolution` | DInt | 와인딩 회전 수 (현재 로직 내 미사용) |
| `in_offset1` | Real | 1회전 오프셋 |
| `in_offset2` | Real | 2회전 오프셋 |
| `in_magnification` | Int | CAM 계산 배율 |

---

## InOut (CAM Point Array)

각 포인트 타입:

```scl
{x : LReal, y : LReal}
````

* `x` : Master Angle (deg)
* `y` : Slave Position

| 이름                   | 타입                                   | 설명            |
| -------------------- | ------------------------------------ | ------------- |
| `inout_camProfileX1` | Array[0..360] of LCamHdl_typeXYPoint | X축 1번 클램프 CAM |
| `inout_camProfileX2` | Array[0..360] of LCamHdl_typeXYPoint | X축 2번 클램프 CAM |
| `inout_camProfileZ1` | Array[0..360] of LCamHdl_typeXYPoint | Z축 1번 클램프 CAM |
| `inout_camProfileZ2` | Array[0..360] of LCamHdl_typeXYPoint | Z축 2번 클램프 CAM |

---

# Static 변수

| 이름                   | 타입   | 설명         |
| -------------------- | ---- | ---------- |
| `stat_Rad2Deg`       | Real | `180 / π`  |
| `stat_Deg2Rad`       | Real | `π / 180`  |
| `stat_Radius`        | Real | JR 외접원 반경  |
| `stat_Theta`         | Real | 대각선 기울기 각도 |
| `stat_magnification` | Int  | 유효 배율      |

---

# Temp 변수

| 이름       | 설명             |
| -------- | -------------- |
| `tempi`  | FOR Loop Index |
| `tempXi` | 실제 계산용 각도      |

---

# Pre Sequence

## 계산식

R=\sqrt{\left(\frac{H}{2}\right)^2+\left(\frac{W}{2}\right)^2}

\Theta=\tan^{-1}\left(\frac{H/2}{W/2}\right)\times\frac{180}{\pi}

## SCL Logic

```scl
stat_Rad2Deg := 180 / PI;
stat_Deg2Rad := PI / 180;

stat_Radius :=
SQRT(
    SQR(in_Height / 2) +
    SQR(in_Width / 2)
);

stat_Theta :=
ATAN((in_Height / 2) / (in_Width / 2))
* stat_Rad2Deg;
```

---

# Main Sequence — CW

## 1st Rotation (X1 / Z1)

### 구간 1 : 0° ~ 180°

X1:

y=-R\cos((\Theta-x)\times D2R)+\frac{W}{2}

Z1:

y=R\sin((\Theta-x)\times D2R)-\frac{H}{2}

---

### 구간 2 : 181° ~ 270°

X1:

y=R\cos((\Theta+x)\times D2R)+W+\frac{W}{2}

Z1:

y=R\sin((\Theta+x)\times D2R)-\frac{H}{2}

추가로 `offset1` 이 선형 증가 방식으로 가산된다.

---

### 구간 3 : 271° ~ 360°

X1:

y=R\cos((x-\Theta)\times D2R)+W+H

Z1:

y=R\sin((x-\Theta)\times D2R)-\frac{H}{2}

---

# Main Sequence — CCW

CW와 대칭 구조를 가진다.

* COS/SIN 부호 방향 반전
* 역방향 타원 궤적 생성
* X1/Z1 및 X2/Z2 계산 구조 동일

---

# 물리적 의미

배터리 와인딩 공정에서 맨드럴 회전에 따라 JR 단면은 타원형에 가까운 사각 궤적을 형성한다.

본 블록은:

* X축 클램프
* Z축 클램프
* 세퍼레이터 추종축

이 해당 궤적을 따라 움직일 수 있도록 CAM Table을 생성한다.

---

# 축 역할

| 축     | 설명           |
| ----- | ------------ |
| X1/Z1 | 1번 세퍼레이터 클램프 |
| X2/Z2 | 2번 세퍼레이터 클램프 |

---

# Offset 역할

| 변수        | 설명           |
| --------- | ------------ |
| `offset1` | 1회전 위치 누적 보상 |
| `offset2` | 2회전 위치 누적 보상 |

---

# 특이점 및 주의사항

## 1. magnification 동작 방식

```scl
tempXi := tempi * magnification;
```

배율이 증가해도 루프 자체는 `0..360` 그대로 수행된다.

즉:

* 포인트 수는 동일
* 실제 계산 각도만 확대

되는 구조이다.

구간 조건 또한:

```scl
tempi <= 180 / magnification
```

처럼 축소되므로 설계 의도를 확인할 필요가 있다.

---

## 2. in_windingRevolution 미사용

인터페이스에는 존재하지만 현재 로직에서는 참조되지 않는다.

가능성:

* 향후 확장 예정
* 외부 참조용 변수

---

## 3. 블록 이름 오타

```text
Carculation
```

은:

```text
Calculation
```

의 오타로 보인다.

---

## 4. Real / LReal 혼용

입력 변수는 `Real` 타입이지만 CAM Point는 `LReal` 타입이다.

따라서 계산 중 암묵적 형변환이 발생한다.

```
```