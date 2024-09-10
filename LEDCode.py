import RPi.GPIO as GPIO
import time
import os
img_counter = 0
 
SENSOR_PIN = 12
def setup():
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(SENSOR_PIN, GPIO.IN)
        GPIO.setup(11, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)
def handle_motion():
        global img_counter
        comand ="fswebcam -S 10 "
        data = "image"+str(img_counter)+".jpg"
        comand = comand + data
        img_counter +=1
        #print("%s",(comand))
        os.system(comand)
 
def loop():
        while True:
                if GPIO.input(SENSOR_PIN) == 1:
 
                        GPIO.output(11,GPIO.HIGH)
                        GPIO.output(13,GPIO.LOW)
                        handle_motion()
                        time.sleep(1)
                else:
                        GPIO.output(11,GPIO.LOW)
                        GPIO.output(13,GPIO.HIGH)
                time.sleep(1)
def cleanup():
        GPIO.cleanup()
        GPIO.output(11,GPIO.LOW)
        GPIO.output(13,GPIO.LOW)
 
 
if __name__ == "__main__":
        setup()
        try:
                loop()
        except KeyboardInterrupt:
                cleanup()
 