import paho.mqtt.client as mqtt
 
class Publisher:

    def __init__(self, config):
        self.client = mqtt.Client()
        self.client.keepalive = 10
        self.config = config

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

        self.client.connect(config["ip"], config["port"])

        self.client.loop_start()
        

    def on_connect(self, client, userdata, flags, rc):
        # if rc == 0:
        #     print("connected OK")
        # else:
        #     print("Bad connection Returned code=", rc)
        pass

    def on_disconnect(self, client, userdata, flags, rc=0):
        print(f"Disconnected from {self.config['ip']} with return code: {rc}")

    def publish(self, topic, message):
        if isinstance(message, bytes):
            self.client.publish(topic, message)
        else:
            encoded_message = message.encode('utf8')
            self.client.publish(topic, encoded_message)
    