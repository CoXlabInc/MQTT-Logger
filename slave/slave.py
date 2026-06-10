import serial
import sys
import json
import paho.mqtt.client as mqtt
import datetime
import pytz
import time
import argparse

def on_connect(client, userdata, flags, reason_code, properties):
    print("server connect")

def on_message(client, userdata, msg):
    topic = msg.topic
    topic_head = 'command/' + idnum

    if topic == topic_head + "/reboot":
        resetDevice()

def resetDevice():
    print("reset start")
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(26, GPIO.OUT, initial=0)
    time.sleep(1)
    GPIO.output(26, 1)
    GPIO.cleanup()
    print("reset finish")

def clock():
    utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
    utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
    return datetime.datetime.now().replace(tzinfo=pytz.utc).isoformat()

parser = argparse.ArgumentParser(description='this program send log to server')
parser.add_argument('--s', required=True, help=' ex) --s=log-server.local:1883')
parser.add_argument('--p', required=True, help=' ex) --p=/dev/ttyACM0 or --p=stdin')
parser.add_argument('--n', required=True, help=' ex) --n=id1')
parser.add_argument('--b', required=False, default='115200', help=' ex) --b=1024')

args = parser.parse_args()

address = args.s.split(':')
device = args.p
bitrate = args.b
idnum = args.n

broker_address = str(address[0])
broker_port = int(address[1])

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(host=broker_address, port=broker_port)
client.subscribe('command/' + idnum + '/#', 1)
client.loop_start()

while not client.is_connected():
    time.sleep(0.05)

def publish(line):
    record = {
        "timestamp": clock(),
        "msg": line.rstrip(),
        "device": idnum,
    }
    payload = json.dumps(record, separators=(",", ":"))
    print(record["timestamp"], "/", record["msg"])
    client.publish("log/" + idnum, payload)

if device == 'stdin':
    for line in sys.stdin:
        if line.strip():
            publish(line)
    time.sleep(0.5)
    client.loop_stop()
    client.disconnect()
else:
    ser = serial.Serial(port=device,
            baudrate=bitrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=2)
    while True:
        logline = ser.readline().decode('utf-8', errors='replace')
        if logline != "":
            publish(logline)
