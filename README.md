# 🍓 Raspberry Pi 30FPS AI Face Greeter & Robot Controller

라즈베리파이 3의 카메라(CSI)와 L298N 모터 드라이버 및 DC 모터 2개를 결합한 **30FPS 실시간 영상 스트리밍 + 딥러닝 얼굴 감지 인사 + 2륜 로봇 모터 주행 제어 시스템**입니다.

---

## 🔌 L298N 모터 드라이버 및 라즈베리파이 회로 결선도

### 1. 전원 결선 (주의: 모터 전원은 반드시 외장 배터리 사용!)
> [!CAUTION]
> 라즈베리파이 5V 핀으로 모터를 구동하면 전압 급강하로 라즈베리파이가 재부팅되거나 파손될 수 있습니다. 모터 구동 전원(12V 터미널)은 **외부 배터리(6V~12V, 예: AA 배터리 4~6개 또는 리튬이온 배터리팩)**를 사용하세요.

- **외부 배터리 (+) (6~12V)** ➔ L298N **`12V` (VMS)** 단자
- **외부 배터리 (-) (GND)** ➔ L298N **`GND`** 단자
- **공통 접지 (Common Ground, 필수!)**: 라즈베리파이 **`GND` (Pin 6)** ➔ L298N **`GND`** 단자
- **5V 레귤레이터 점퍼**: 배터리가 7V~12V인 경우 L298N의 5V 레귤레이터 점퍼 캡을 그대로 꽂아둡니다. (L298N 5V 단자는 비워둠)

---

### 2. 모터 결선 (Motor A / Motor B)
- **모터 A (왼쪽 모터)**: L298N **`OUT1`**, **`OUT2`** 단자에 2개 선 연결
- **모터 B (오른쪽 모터)**: L298N **`OUT3`**, **`OUT4`** 단자에 2개 선 연결

---

### 3. 라즈베리파이 GPIO 신호 결선표 (BCM 핀 번호 기준)

| L298N 핀 | 라즈베리파이 3 연결 (BCM / 물리핀) | 설명 |
| :--- | :--- | :--- |
| **`ENA`** | **GPIO 12** (물리 Pin 32, PWM0) | 왼쪽 모터 PWM 속도 제어 (점퍼캡 제거 후 연결) |
| **`IN1`** | **GPIO 17** (물리 Pin 11) | 왼쪽 모터 정회전 신호 |
| **`IN2`** | **GPIO 27** (물리 Pin 13) | 왼쪽 모터 역회전 신호 |
| **`IN3`** | **GPIO 22** (물리 Pin 15) | 오른쪽 모터 정회전 신호 |
| **`IN4`** | **GPIO 23** (물리 Pin 16) | 오른쪽 모터 역회전 신호 |
| **`ENB`** | **GPIO 13** (물리 Pin 33, PWM1) | 오른쪽 모터 PWM 속도 제어 (점퍼캡 제거 후 연결) |
| **`GND`** | **GND** (물리 Pin 6) | **공통 접지 (반드시 연결)** |

---

## 🕹️ 모터 제어 방법

### 1) PC 애플리케이션 창에서 실시간 주행 (추천)
- 바탕화면의 **`라즈베리파이_얼굴인식_실행.bat`**을 실행하면 화면을 보며 키보드로 바로 주행할 수 있습니다.
  - `W`: 전진 (Forward)
  - `S`: 후진 (Backward)
  - `A`: 좌회전 (Turn Left)
  - `D`: 우회전 (Turn Right)
  - `1 / 2 / 3`: 모터 A (왼쪽) 전진 / 후진 / 정지
  - `4 / 5 / 6`: 모터 B (오른쪽) 전진 / 후진 / 정지
  - `Space`: 전체 정지 (Stop)
  - `+` / `-`: 속도 10% 증가 / 감소
  - `H`: HUD 오버레이 켜기/끄기
  - `Q`: 종료

### 2) 웹 브라우저 조종 패드 (모바일 / PC 브라우저)
- 브라우저에서 `http://<YOUR_RPI_IP>:8080/` (또는 `http://raspberrypi.local:8080/`)로 접속하면 30FPS 카메라 화면과 함께 화면에 **상하좌우 D-Pad 터치 버튼, 개별 모터 조종 탭, 속도 조절 슬라이더**가 나타납니다.

### 3) 라즈베리파이 터미널 직접 테스트
- 라즈베리파이 SSH 터미널에서 모터 동작을 독립적으로 테스트할 수 있습니다:
  ```bash
  python3 /home/pi/motor_controller.py
  ```

### 4) REST API 원격 호출
- 브라우저나 HTTP 클라이언트로 모터를 직접 제어할 수 있습니다:
  - `http://<YOUR_RPI_IP>:8080/api/motor?action=forward&speed=80`
  - `http://<YOUR_RPI_IP>:8080/api/motor?action=backward&speed=70`
  - `http://<YOUR_RPI_IP>:8080/api/motor?action=left&speed=60`
  - `http://<YOUR_RPI_IP>:8080/api/motor?action=right&speed=60`
  - `http://<YOUR_RPI_IP>:8080/api/motor?action=stop`
  - `http://<YOUR_RPI_IP>:8080/api/motor?action=mot_a_fwd&speed=70`
  - `http://<YOUR_RPI_IP>:8080/api/motor?action=mot_b_fwd&speed=70`
