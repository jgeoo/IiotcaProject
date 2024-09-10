import RPi.GPIO as GPIO
import time
import os
import io
from google.cloud import vision
import pandas as pd
from google.cloud import vision_v1
import paho.mqtt.client as mqtt
import pyrebase
import random
import threading
import re
import drivers
from datetime import datetime
 
 
GPIO.setwarnings(False)
display = drivers.Lcd()
 
plate_numbers = ['TM-20-KKJ','TM-57-GRZ','BH-44-JAC','BH-87-KLA','GJ-43-BOS']
 
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"ServiceAccountToken.json"
 
config = {
	"apiKey": "  ",
	"authDomain":"  ",
	"databaseURL": "  ",
	"storageBucket": "  "
}
 
firebase = pyrebase.initialize_app(config)
 
db = firebase.database()
 
 
SENSOR_PIN = 12
 
 
def api(image_path):
    client = vision.ImageAnnotatorClient()
 
    # Read the image content
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
 
    # Create an image instance
    image = vision_v1.Image(content=content)
 
    # Annotate Image Response
    response = client.text_detection(image=image)  
    df = pd.DataFrame(columns=['locale', 'description'])
 
    texts = response.text_annotations
    for text in texts:
        df.loc[len(df)] = {'locale': text.locale, 'description': text.description}
 
    return df['description'][0]
 
def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(SENSOR_PIN, GPIO.IN)
    GPIO.setup(11, GPIO.OUT)
    GPIO.setup(13, GPIO.OUT)
    GPIO.setwarnings(False)
 
def handle_motion():
    global img_counter
    comand = "fswebcam -S 10 "
    data = "image" + str(img_counter) + ".jpg"
    comand = comand + data
    img_counter += 1
    os.system(comand)
    return data
 
def extract_plate_and_date(text):
      # Split the text based on the newline character
    separated_strings = text.split("\n")
    completedate = separated_strings[1]
 
    splitdate = completedate.split()
 
    singledate = splitdate[0]
 
    date_obj = datetime.strptime(singledate,'%Y-%m-%d')
 
    weekday_index = date_obj.weekday()
 
    weekday_names = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
 
    weekday_name = weekday_names[weekday_index]
 
    getstatus=validate_plate(separated_strings[0])
    display.lcd_display_string(separated_strings[0], 1)
    display.lcd_display_string(getstatus, 2)
    return {
        "Plate Name": separated_strings[0],
        "Date": separated_strings[1],
        "Day": weekday_name,
        "SatusType": getstatus
    }
 
def validate_plate(plate):
    if plate in plate_numbers:
        return 'Accepted'
    else:
        return 'Rejected'
 
 
def loop():
    while True:
        try:
            if GPIO.input(SENSOR_PIN) == 1:
                GPIO.output(11, GPIO.HIGH)
                GPIO.output(13, GPIO.LOW)
                data = handle_motion()
                text = api(data)
                separated_text = extract_plate_and_date(text)
 
                print("Detected text:", separated_text)
                db.child("Status").push(separated_text)
                db.update(separated_text)
                print("Sent")
                time.sleep(10)
            else:
                GPIO.output(11, GPIO.LOW)
                GPIO.output(13, GPIO.HIGH)
            time.sleep(1)
        except RuntimeError as error:
            print(error.args[0])
 
 
def cleanup():
    GPIO.cleanup()
    GPIO.output(11, GPIO.LOW)
    GPIO.output(13, GPIO.LOW)
 
def mqtt_thread():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
 
    # Replace with the address of your MQTT broker
    client.connect("localhost", 1883, 60) 
 
    print("Listening Forever")
 
    try:
        client.loop_forever()  # This keeps the client running forever
    except:
        print("Something Happened Connecting to the Broker!")
 
def on_connect(client,userdata, flags, rc):
    print(f"Conneced with result code {rc}")
    client.subscribe("makephoto")
 
def on_message(mqtt_client,userdata, msg):
    print(f"Received message on topic {msg.topic}: {msg.payload}")
    if msg.payload == b"Yes":
        try:
            data = handle_motion()
            text = api(data)
            separated_text = extract_plate_and_date(text)
 
            print("Detected text:", separated_text)
            db.child("Status").push(separated_text)
            db.update(separated_text)
            print("Sent")
            print("Photo made")
        except Exception as e:
            print(e)
    else:
        print("No photo took")
 
 
if __name__ == "__main__":
    img_counter = 0
    setup()
    threading.Thread(target = mqtt_thread, daemon = True).start()
    try:
        loop()
    except KeyboardInterrupt:
        cleanup()
 