from argparse import ArgumentParser
from typing import List


class Arguments:

    __description: str
    __captureDevice: int
    __captureWidth: int
    __captureHeight: int
    __modelIndex: int
    __scoreThreshold: float
    __mqttHost: str
    __mqttPort: int
    __mqttTopic: str
    __httpHost: str
    __httpPort: int
    __httpPath: str
    __debug: bool

    def __init__(self):
        parser = ArgumentParser()
        parser.add_argument(
            "--description",
            type=str,
            default="",
            help="Description will display on the screen (default: '')",
        )
        parser.add_argument(
            "--device",
            type=int,
            default=0,
            help="Device ID of your camera (default: 0)",
        )
        parser.add_argument(
            "--width",
            type=int,
            default=960,
            help="Captured video frame width (default: 960)",
        )
        parser.add_argument(
            "--height",
            type=int,
            default=540,
            help="Captured video frame height (default: 540)",
        )
        parser.add_argument(
            "--model",
            type=int,
            default=0,
            help="""
            0: EfficientDet-Lite0 (int8)
            1: EfficientDet-Lite0 (float 16)
            2: EfficientDet-Lite0 (float 32)
            3: EfficientDet-Lite2 (int8)
            4: EfficientDet-Lite2 (float 16)
            5: EfficientDet-Lite2 (float 32)
            6: SSDMobileNet-V2 (int8)
            7: SSDMobileNet-V2 (float 32)
            (default: 0)
            """,
            choices=[0, 1, 2, 3, 4, 5, 6, 7],
        )
        parser.add_argument(
            "--score_threshold",
            type=float,
            default=0.5,
            help="Score threshold for detections (default: 0.5)",
        )
        parser.add_argument(
            "--mqtt_host",
            type=str,
            default="localhost",
            help="MQTT host (default: localhost)",
        )
        parser.add_argument(
            "--mqtt_port",
            type=int,
            default=1883,
            help="MQTT port (default: 1883)",
        )
        parser.add_argument(
            "--mqtt_topic",
            type=str,
            default="msg",
            help="MQTT topic (default: msg)",
        )
        parser.add_argument(
            "--http_host",
            type=str,
            default="0.0.0.0",
            help="HTTP host (default: 0.0.0.0)",
        )
        parser.add_argument(
            "--http_port",
            type=int,
            default=2001,
            help="HTTP port (default: 2001)",
        )
        parser.add_argument(
            "--http_path",
            type=str,
            default="/",
            help="HTTP path (default: /)",
        )
        parser.add_argument(
            "--debug",
            type=bool,
            default=False,
            help="Enable debug mode (default: false)",
        )

        cmd = parser.parse_args()
        self.__description = cmd.description
        self.__captureDevice = cmd.device
        self.__captureWidth = cmd.width
        self.__captureHeight = cmd.height
        self.__modelIndex = cmd.model
        self.__scoreThreshold = cmd.score_threshold
        self.__debug = cmd.debug
        self.__mqttHost = cmd.mqtt_host
        self.__mqttPort = cmd.mqtt_port
        self.__mqttTopic = cmd.mqtt_topic
        self.__httpHost = cmd.http_host
        self.__httpPort = cmd.http_port
        self.__httpPath = cmd.http_path

    def getDescription(self) -> str:
        return self.__description

    def getCaptureDevice(self) -> int:
        return self.__captureDevice

    def getVideoWidth(self) -> int:
        return self.__captureWidth

    def getVideoHeight(self) -> int:
        return self.__captureHeight

    def getModelPath(self) -> int:
        modelMap: List[str] = [
            'model/efficientdet_lite0_int8.tflite',
            'model/efficientdet_lite0_float16.tflite',
            'model/efficientdet_lite0_float32.tflite',
            'model/efficientdet_lite2_int8.tflite',
            'model/efficientdet_lite2_float16.tflite',
            'model/efficientdet_lite2_float32.tflite',
            'model/ssd_mobilenet_v2_float16.tflite',
            'model/ssd_mobilenet_v2_float32.tflite',
        ]
        return modelMap[self.__modelIndex]

    def getScoreThreshold(self) -> float:
        return self.__scoreThreshold

    def getDebug(self) -> bool:
        return self.__debug

    def getMqttHost(self) -> str:
        return self.__mqttHost

    def getMqttPort(self) -> int:
        return self.__mqttPort

    def getMqttTopic(self) -> str:
        return self.__mqttTopic

    def getHttpHost(self) -> str:
        return self.__httpHost

    def getHttpPort(self) -> int:
        return self.__httpPort

    def getHttpPath(self) -> str:
        return self.__httpPath
