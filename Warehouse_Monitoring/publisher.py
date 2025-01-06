from paho.mqtt import client as mqtt


class Publisher:

    __mqttClient: mqtt.Client
    __mqttHost: str
    __mqttPort: int

    def __init__(self, mqttHost: str, mqttPort: int):
        self.__mqttClient = mqtt.Client()
        self.__mqttHost = mqttHost
        self.__mqttPort = mqttPort

    def connect(self, keepalive: int) -> mqtt.Client:
        self.__mqttClient.connect(self.__mqttHost, self.__mqttPort, keepalive)
        self.__mqttClient.loop_start()
        return self.__mqttClient

    def disconnect(self) -> None:
        self.__mqttClient.disconnect()

    def setOnConnectCallback(self, callback: mqtt.Client.on_connect) -> None:
        self.__mqttClient.on_connect = callback

    def setOnMessageCallback(self, callback: mqtt.Client.on_message) -> None:
        self.__mqttClient.on_message = callback

    def setOnDisconnectCallback(self, callback: mqtt.Client.on_disconnect) -> None:
        self.__mqttClient.on_disconnect = callback
