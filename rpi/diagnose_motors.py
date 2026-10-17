#!/usr/bin/env python3
"""
L298N Individual Motor Diagnostic Script
Tests Motor A and Motor B separately to verify that GPIO channels and motor outputs are independent.
"""

import time
import sys
import RPi.GPIO as GPIO

# Pin Configurations (BCM)
ENA = 12  # Left Motor Speed
IN1 = 17  # Left Motor Dir 1
IN2 = 27  # Left Motor Dir 2

ENB = 13  # Right Motor Speed
IN3 = 22  # Right Motor Dir 1
IN4 = 23  # Right Motor Dir 2

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for p in [IN1, IN2, IN3, IN4, ENA, ENB]:
        GPIO.setup(p, GPIO.OUT)
        GPIO.output(p, GPIO.LOW)

    pwm_a = GPIO.PWM(ENA, 100)
    pwm_b = GPIO.PWM(ENB, 100)
    pwm_a.start(0)
    pwm_b.start(0)
    return pwm_a, pwm_b

def stop_all(pwm_a, pwm_b):
    pwm_a.ChangeDutyCycle(0)
    pwm_b.ChangeDutyCycle(0)
    for p in [IN1, IN2, IN3, IN4]:
        GPIO.output(p, GPIO.LOW)

def run_test():
    pwm_a, pwm_b = setup()
    stop_all(pwm_a, pwm_b)

    print("=" * 60)
    print(" L298N 개별 모터 독립 동작 진단 테스트")
    print("=" * 60)
    print("1단계: [모터 A (왼쪽 모터)] 만 2.5초간 단독 회전합니다.")
    print("       (이때 모터 B는 완전히 멈춰있어야 정상입니다!)")
    print("=" * 60)
    time.sleep(1)

    # Test Motor A only
    print(">> [모터 A 단독 회전 시작... (GPIO 17/27, PWM 12)]")
    pwm_a.ChangeDutyCycle(80)
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    time.sleep(2.5)

    stop_all(pwm_a, pwm_b)
    print(">> [모터 A 정지 완료]\n")
    time.sleep(1.5)

    print("=" * 60)
    print("2단계: [모터 B (오른쪽 모터)] 만 2.5초간 단독 회전합니다.")
    print("       (이때 모터 A는 완전히 멈춰있어야 정상입니다!)")
    print("=" * 60)
    time.sleep(1)

    # Test Motor B only
    print(">> [모터 B 단독 회전 시작... (GPIO 22/23, PWM 13)]")
    pwm_b.ChangeDutyCycle(80)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    time.sleep(2.5)

    stop_all(pwm_a, pwm_b)
    print(">> [모터 B 정지 완료]\n")

    pwm_a.stop()
    pwm_b.stop()
    GPIO.cleanup()

    print("=" * 60)
    print(" 진단 결과 확인 안내:")
    print(" 1) 모터 A 회전 시 모터 B도 같이 돌았다면:")
    print("    -> 점퍼선 결선 시 IN1과 IN3가 같은 핀에 꽂혔거나,")
    print("       모터 두 개가 같은 출력단자(OUT1/2)에 묶여 있을 가능성이 높습니다.")
    print(" 2) 각 모터가 차례대로 1개씩 따로 돌았다면:")
    print("    -> 하드웨어 결선은 정상 분리되어 있으며, 주행 로직에서 좌/우 개별 제어가 가능합니다!")
    print("=" * 60)

if __name__ == '__main__':
    run_test()
