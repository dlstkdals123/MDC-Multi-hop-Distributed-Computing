import paho.mqtt.client as mqtt
 
class Publisher:

    def __init__(self, config):
        self.client = mqtt.Client()
        self.client.keepalive = 10
        self.config = config
        self._bytes_sent = 0

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
        print(str(rc))

    def publish(self, topic, message):
        if isinstance(message, bytes):
            self.client.publish(topic, message)
            self.bytes_sent += len(message)
        else:
            encoded_message = message.encode('utf8')
            self.client.publish(topic, encoded_message)
            self.bytes_sent += len(encoded_message)
    
    @property
    def bytes_sent(self) -> int:
        return self._bytes_sent

    @bytes_sent.setter
    def bytes_sent(self, bytes_sent: int) -> None:
        self._bytes_sent = bytes_sent