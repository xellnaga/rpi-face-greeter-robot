#!/usr/bin/env python3
"""
L298N Dual DC Motor Controller for Raspberry Pi 3
Supports variable speed via PWM and directional control.
Supports independent (individual) motor control and coordinated vehicle drive.
Compatible with Python 3.4+
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None
    print("[WARN] RPi.GPIO not available. Running in mock simulation mode.")

# Default Pin Configurations (BCM numbering)
DEFAULT_PINS = {
    'ENA': 12,  # Left motor PWM speed (Header Pin 32)
    'IN1': 17,  # Left motor direction 1 (Header Pin 11)
    'IN2': 27,  # Left motor direction 2 (Header Pin 13)
    'IN3': 22,  # Right motor direction 1 (Header Pin 15)
    'IN4': 23,  # Right motor direction 2 (Header Pin 16)
    'ENB': 13,  # Right motor PWM speed (Header Pin 33)
}

class MotorController:
    def __init__(self, pins=None, pwm_freq=100):
        self.pins = pins or DEFAULT_PINS
        self.pwm_freq = pwm_freq
        self.pwm_a = None
        self.pwm_b = None
        self.current_speed = 70  # Default speed (0 ~ 100%)
        self.is_mock = GPIO is None
        self._init_gpio()

    def _init_gpio(self):
        if self.is_mock:
            print("[MotorController] Initialized in mock mode.")
            return

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Setup direction pins
        for pin_name in ['IN1', 'IN2', 'IN3', 'IN4']:
            pin = self.pins[pin_name]
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        # Setup PWM enable pins
        GPIO.setup(self.pins['ENA'], GPIO.OUT)
        GPIO.setup(self.pins['ENB'], GPIO.OUT)

        self.pwm_a = GPIO.PWM(self.pins['ENA'], self.pwm_freq)
        self.pwm_b = GPIO.PWM(self.pins['ENB'], self.pwm_freq)
        self.pwm_a.start(0)
        self.pwm_b.start(0)
        print("[MotorController] GPIO initialized successfully.")

    def set_speed(self, speed):
        """Set speed percentage: 0 to 100"""
        self.current_speed = max(0, min(100, int(speed)))
        if not self.is_mock:
            self.pwm_a.ChangeDutyCycle(self.current_speed)
            self.pwm_b.ChangeDutyCycle(self.current_speed)

    # -------------------------------------------------------------
    # Individual Motor Controls (개별 모터 독립 제어)
    # -------------------------------------------------------------
    def motor_left(self, direction='forward', speed=None):
        """Control Left Motor (Motor A) individually: 'forward', 'backward', 'stop'"""
        spd = self.current_speed if speed is None else max(0, min(100, int(speed)))
        if not self.is_mock:
            if direction == 'forward':
                self.pwm_a.ChangeDutyCycle(spd)
                GPIO.output(self.pins['IN1'], GPIO.HIGH)
                GPIO.output(self.pins['IN2'], GPIO.LOW)
            elif direction == 'backward':
                self.pwm_a.ChangeDutyCycle(spd)
                GPIO.output(self.pins['IN1'], GPIO.LOW)
                GPIO.output(self.pins['IN2'], GPIO.HIGH)
            else:  # stop
                self.pwm_a.ChangeDutyCycle(0)
                GPIO.output(self.pins['IN1'], GPIO.LOW)
                GPIO.output(self.pins['IN2'], GPIO.LOW)
        else:
            print("[Mock Motor] Left Motor -> {} (Speed: {}%)".format(direction, spd))

    def motor_right(self, direction='forward', speed=None):
        """Control Right Motor (Motor B) individually: 'forward', 'backward', 'stop'"""
        spd = self.current_speed if speed is None else max(0, min(100, int(speed)))
        if not self.is_mock:
            if direction == 'forward':
                self.pwm_b.ChangeDutyCycle(spd)
                GPIO.output(self.pins['IN3'], GPIO.HIGH)
                GPIO.output(self.pins['IN4'], GPIO.LOW)
            elif direction == 'backward':
                self.pwm_b.ChangeDutyCycle(spd)
                GPIO.output(self.pins['IN3'], GPIO.LOW)
                GPIO.output(self.pins['IN4'], GPIO.HIGH)
            else:  # stop
                self.pwm_b.ChangeDutyCycle(0)
                GPIO.output(self.pins['IN3'], GPIO.LOW)
                GPIO.output(self.pins['IN4'], GPIO.LOW)
        else:
            print("[Mock Motor] Right Motor -> {} (Speed: {}%)".format(direction, spd))

    # -------------------------------------------------------------
    # Coordinated Dual Motor Drive (양쪽 모터 통합 주행)
    # -------------------------------------------------------------
    def forward(self, speed=None):
        """Move forward (both motors forward)"""
        self.motor_left('forward', speed)
        self.motor_right('forward', speed)

    def backward(self, speed=None):
        """Move backward (both motors backward)"""
        self.motor_left('backward', speed)
        self.motor_right('backward', speed)

    def turn_left(self, speed=None):
        """One-wheel turn left: Left Motor STOP, Right Motor FORWARD (한쪽만 회전)"""
        self.motor_left('stop')
        self.motor_right('forward', speed)

    def turn_right(self, speed=None):
        """One-wheel turn right: Right Motor STOP, Left Motor FORWARD (한쪽만 회전)"""
        self.motor_right('stop')
        self.motor_left('forward', speed)

    def spin_left(self, speed=None):
        """In-place pivot turn left: Left backward, Right forward"""
        self.motor_left('backward', speed)
        self.motor_right('forward', speed)

    def spin_right(self, speed=None):
        """In-place pivot turn right: Left forward, Right backward"""
        self.motor_left('forward', speed)
        self.motor_right('backward', speed)

    def stop(self):
        """Stop both motors"""
        self.motor_left('stop')
        self.motor_right('stop')

    def cleanup(self):
        """Safely release GPIO resources"""
        self.stop()
        if not self.is_mock:
            if self.pwm_a:
                self.pwm_a.stop()
            if self.pwm_b:
                self.pwm_b.stop()
            GPIO.cleanup()
        print("[MotorController] Cleaned up GPIO.")

def interactive_cli():
    print("=" * 60)
    print(" L298N Motor Interactive CLI Controller")
    print("=" * 60)
    print(" [양쪽 모터 주행]")
    print("   [W] Forward      [S] Backward")
    print("   [A] Turn Left (오른쪽만 구동)   [D] Turn Right (왼쪽만 구동)")
    print("   [J] Spin Left (제자리 회전)    [L] Spin Right (제자리 회전)")
    print(" [개별 모터 단독 제어]")
    print("   [1] 모터 A(왼쪽) 전진     [2] 모터 A 정지")
    print("   [3] 모터 B(오른쪽) 전진   [4] 모터 B 정지")
    print(" [기타]")
    print("   [Space] 전체 정지         [+] / [-] 속도 조절")
    print("   [X] 종료")
    print("=" * 60)

    motor = MotorController()
    speed = 70
    motor.set_speed(speed)

    try:
        import termios
        import tty

        def getch():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

        while True:
            char = getch().lower()
            if char == 'w':
                print("\r[주행] 전진 (양쪽 모터 전진)                ", end="")
                motor.forward()
            elif char == 's':
                print("\r[주행] 후진 (양쪽 모터 후진)                ", end="")
                motor.backward()
            elif char == 'a':
                print("\r[주행] 좌회전 (왼쪽 정지, 오른쪽만 회전)    ", end="")
                motor.turn_left()
            elif char == 'd':
                print("\r[주행] 우회전 (오른쪽 정지, 왼쪽만 회전)    ", end="")
                motor.turn_right()
            elif char == 'j':
                print("\r[주행] 제자리 좌회전 (스핀)                 ", end="")
                motor.spin_left()
            elif char == 'l':
                print("\r[주행] 제자리 우회전 (스핀)                 ", end="")
                motor.spin_right()
            elif char == '1':
                print("\r[개별] 모터 A (왼쪽) 만 단독 전진!          ", end="")
                motor.motor_left('forward')
            elif char == '2':
                print("\r[개별] 모터 A (왼쪽) 정지                   ", end="")
                motor.motor_left('stop')
            elif char == '3':
                print("\r[개별] 모터 B (오른쪽) 만 단독 전진!        ", end="")
                motor.motor_right('forward')
            elif char == '4':
                print("\r[개별] 모터 B (오른쪽) 정지                 ", end="")
                motor.motor_right('stop')
            elif char in (' ', 'x', '\x1b'):
                print("\r[정지] 전체 모터 정지                       ", end="")
                motor.stop()
                if char == 'x':
                    break
            elif char in ('+', '='):
                speed = min(100, speed + 10)
                motor.set_speed(speed)
                print("\r[속도] {}% 로 증가                         ".format(speed), end="")
            elif char in ('-', '_'):
                speed = max(20, speed - 10)
                motor.set_speed(speed)
                print("\r[속도] {}% 로 감소                         ".format(speed), end="")
    except KeyboardInterrupt:
        pass
    finally:
        motor.cleanup()
        print("\n종료되었습니다.")

if __name__ == '__main__':
    interactive_cli()
