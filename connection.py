import paho.mqtt.client as mqtt
import time

# MQTT broker details
broker_host = "broker.emqx.io"
broker_port = 1883

# MQTT topics
connection_status_topic = "gateway/connection_status"
network_stats_topic = "gateway/network_stats"

# Creating a MQTT client instance
client = mqtt.Client()

# tracking connection status
connected = False
connection_start_time = None
connection_end_time = None
retry_count = 0

# Callback function for successful connection
def on_connect(client, userdata, flags, rc):
    global connected
    print("Connected to MQTT broker")
    connected = True
    client.subscribe(connection_status_topic)

# Callback function for incoming messages
def on_message(client, userdata, msg):
    if msg.topic == connection_status_topic:
        if msg.payload.decode() == "connected":
            record_connection()
        elif msg.payload.decode() == "disconnected":
            record_disconnection()

# recording connection status
def record_connection():
    global connection_start_time
    connection_start_time = time.time()
    print("Connection established at", time.ctime(connection_start_time))
    # Sending connection status to the MQTT broker
    client.publish(network_stats_topic, f"Connection established at {time.ctime(connection_start_time)}")

#  recording disconnection status
def record_disconnection():
    global connection_end_time, retry_count
    connection_end_time = time.time()
    retry_count += 1
    print("Connection lost at", time.ctime(connection_end_time))
    # Sending disconnection status to the MQTT broker
    client.publish(network_stats_topic, f"Connection lost at {time.ctime(connection_end_time)}")

# Setting MQTT client callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connection to MQTT broker
client.connect(broker_host, broker_port)

# Starting  the MQTT loop
client.loop_start()

# Main program logic
while True:
    # Checking if the network connection is active
    if connected:
        print("Network connection is active")
         client.publish("sensor_data", "Sensor value")
    else:
        print("Network connection is lost")
    time.sleep(10)

    # Checking if connection has been lost for more than 5 seconds
    if connected and time.time() - connection_end_time > 5:
        connected = False
        client.publish(connection_status_topic, "disconnected")

    # Checkng if the connection need a retry
    if not connected and time.time() - connection_end_time > 5:
        retry_count += 1
        client.publish(connection_status_topic, "connected")
        connection_start_time = time.time()
        print("Retrying connection at", time.ctime(connection_start_time))

    # Send network stats
    if connection_start_time is not None:
        stats = f"Connection time: {time.ctime(connection_start_time)} - {time.ctime(connection_end_time)} | Retries: {retry_count}"
        client.publish(network_stats_topic, stats)

# Stop the MQTT loop
client.loop_stop()
