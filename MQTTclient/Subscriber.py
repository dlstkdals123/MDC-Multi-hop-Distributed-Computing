import paho.mqtt.client as mqtt
import paho.mqtt
 
class Subscriber:

    def __init__(self, config, queue):
        self.client = mqtt.Client(userdata=queue)
        self.client.keepalive = 10
        self.config = config
        self._bytes_received = 0

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_message = self.on_message

        self.client.connect(config["ip"], config["port"])
        
        # config.topics = ["parking/loopcoil"]
        self.client.subscribe(config["topics"])

        self.client.loop_start()
        

    def on_connect(self, client, userdata, flags, rc):
        # if rc == 0:
        #     print("connected OK")
        # else:
        #     print("Bad connection Returned code=", rc)
        pass

    def on_disconnect(self, client, userdata, flags, rc=0):
        print(str(rc))

    def on_subscribe(self, client, userdata, mid, granted_qos):
        # print("subscribed: " + str(mid) + " " + str(granted_qos))
        pass

    def on_message(self, client, userdata, msg):
        userdata.put(msg)
        self.bytes_received += len(msg.payload)

    @property
    def bytes_received(self) -> int:
        return self._bytes_received

    @bytes_received.setter
    def bytes_received(self, bytes_received: int) -> None:
        self._bytes_received = bytes_received