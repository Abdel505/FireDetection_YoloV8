# main.py for ESP32
import machine
import uselect
import sys
import time

# --- Configuration ---
RED_PIN = 5       # ON on FIRE
YELLOW_PIN = 18   # Flicker ALWAYS (System Power)
BUZZER_PIN = 23   # ON on FIRE

# Initialize Pins
red_led = machine.Pin(RED_PIN, machine.Pin.OUT)
yellow_led = machine.Pin(YELLOW_PIN, machine.Pin.OUT)
buzzer = machine.PWM(machine.Pin(BUZZER_PIN))
buzzer.duty(0) # Ensure buzzer is off initially

# Setup Serial Polling (Non-blocking read)
poll_obj = uselect.poll()
poll_obj.register(sys.stdin, uselect.POLLIN)

print("ESP32 Fire Alert System Ready...")

fire_active = False
last_yellow_time = 0
last_alarm_time = 0
alarm_high_pitch = False
FLICKER_DELAY = 500  # ms
ALARM_DELAY = 300    # ms for siren toggle (speed of the siren)

while True:
    current_time = time.ticks_ms()

    # --- Yellow LED: Always flickers (System Heartbeat) ---
    if time.ticks_diff(current_time, last_yellow_time) > FLICKER_DELAY:
        yellow_led.value(not yellow_led.value())
        last_yellow_time = current_time

    # --- Serial Communication ---
    # Check if data is available (0 timeout for non-blocking)
    poll_results = poll_obj.poll(0)
    
    if poll_results:
        command = sys.stdin.readline().strip()
        if command == "FIRE":
            fire_active = True
        elif command == "RESET":
            fire_active = False

    # --- Alarm Logic ---
    if fire_active:
        # Fire Detected: Red ON, Buzzer ON (Latched until RESET)
        red_led.value(1)
        
        # Two-tone Siren Effect (Sophisticated Alarm)
        if time.ticks_diff(current_time, last_alarm_time) > ALARM_DELAY:
            alarm_high_pitch = not alarm_high_pitch
            buzzer.freq(2500 if alarm_high_pitch else 1500) # Toggle between 2.5kHz and 1.5kHz
            buzzer.duty(50) # Reduced volume (approx 5% duty cycle)
            last_alarm_time = current_time
    else:
        # Safe: Red OFF, Buzzer OFF
        red_led.value(0)
        buzzer.duty(0) # Silence buzzer (Volume OFF)
