import paho.mqtt.client as mqtt
from django.conf import settings
import asyncio
from utils import get_env
MQREQUESTSUB = get_env('MQREQUESTSUB')
MQREPONSEPUB = get_env('MQREPONSEPUB')

def on_connect(mqtt_client, userdata, flags, rc):
    if rc == 0:
        print('Connected successfully')
        # mqtt_client.subscribe('lkr_test_ramak_response')
    else:
        print('Bad connection. Code:', rc)


def on_message(mqtt_client, userdata, msg):
    print(f'Received message on topic: {msg.topic} with payload: {msg.payload.decode("UTF-8")}')


client = mqtt.Client()
# client.on_connect = on_connect
# client.on_message = on_message
# client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASSWORD)
client.connect(
    host=settings.MQTT_SERVER,
    port=settings.MQTT_PORT,
    keepalive=settings.MQTT_KEEPALIVE
)

def publish_message(topic, data, qos = 1):
    rc, mid = client.publish(MQREQUESTSUB,data,qos)
    return {'code': rc}