#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base64 import b64encode
from json import dumps
from logging import DEBUG, INFO, Logger, StreamHandler
from signal import SIGINT, SIGTERM, signal
from threading import Thread
from time import localtime, strftime, time, sleep
from typing import Generator
from colorlog import ColoredFormatter
from cv2 import imencode
from flask import Flask, Response
from arguments import Arguments
from buffer import Buffer
from detector import Detector
from publisher import Publisher
from video import Video


def handleInterrupt(publisher: Publisher, video: Video, logger: Logger) -> None:
    logger.info("exit signal received, releasing capture device...")
    publisher.disconnect()
    video.close()
    exit(0)


def setupLogger(level=INFO) -> Logger:
    consoleHandler = StreamHandler()
    consoleHandler.setLevel(level)
    consoleHandler.setFormatter(ColoredFormatter(
        fmt="%(asctime)s.%(msecs)03d %(log_color)s[%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={"DEBUG": "white", "INFO": "green",
                    "WARNING": "yellow", "ERROR": "red"},
    ))
    logger = Logger(__name__)
    logger.addHandler(consoleHandler)
    return logger


def handleHttpRequest(data: Buffer) -> Generator[bytes, None, None]:
    while (True):
        sleep(0.1)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + data.getData() + b'\r\n')


def setupWebServer(data: Buffer, addr: str, port: int, path: str) -> None:
    app = Flask(__name__)

    @app.route(path, methods=['GET'])
    def _():
        return Response(
            response=handleHttpRequest(data),
            mimetype='multipart/x-mixed-replace; boundary=frame',
        )
    app.run(host=addr, port=port, threaded=True, debug=False)


def main() -> None:
    # Read options from command line
    args = Arguments()
    description = args.getDescription()
    capDevice = args.getCaptureDevice()
    capWidth = args.getVideoWidth()
    capHeight = args.getVideoHeight()
    modelPath = args.getModelPath()
    scoreThreshold = args.getScoreThreshold()
    mqttServer = args.getMqttHost()
    mqttPort = args.getMqttPort()
    mqttTopic = args.getMqttTopic()

    # Setup logger
    logger = setupLogger(DEBUG if args.getDebug() else INFO)
    logger.info("loaded arguments from command line")
    logger.debug(f"current device for capturing: {capDevice}")
    logger.debug(f"width for video capturing: {capWidth}")
    logger.debug(f"height for video capturing: {capHeight}")
    logger.debug(f"score threshold is set to: {scoreThreshold}")
    logger.debug(f"path to .tflite model: {modelPath}")
    logger.debug(f"MQTT server is set to: {mqttServer}:{mqttPort}")
    logger.debug(f"messages will be published to: {mqttTopic}")

    # Connect to MQTT server
    publisher = Publisher(mqttServer, mqttPort)
    publisher.setOnConnectCallback(
        lambda __client__, __userdata__, __flags__, __rc__: logger.info(
            f"connected to MQTT server: {mqttServer}:{mqttPort}"
        ),
    )
    mqttClient = publisher.connect(60)

    # Create object detector
    detector = Detector(modelPath, scoreThreshold)
    video = Video(capDevice, capWidth, capHeight)

    # System signal handlers
    signal(
        SIGTERM,
        lambda __sig__, __frame__: handleInterrupt(
            publisher, video, logger,
        ),
    )
    signal(
        SIGINT,
        lambda __sig__, __frame__: handleInterrupt(
            publisher, video, logger,
        ),
    )

    bufferData = Buffer()  # buffer to hold image data
    Thread(
        target=setupWebServer,
        args=(
            bufferData,
            args.getHttpHost(),
            args.getHttpPort(),
            args.getHttpPath(),
        ),
    ).start()

    logger.info("successfully initialized object detector")
    while True:
        currentTime = round(time() * 1000)
        videoFrame = video.capture()

        # Filter out all non-person detections
        detectionResult = [
            detection for detection in detector.getDetections(videoFrame)
            if detection.categories[0].category_name == "person"
        ]

        personData = []
        for index, person in enumerate(detectionResult):
            x1 = person.bounding_box.origin_x
            y1 = person.bounding_box.origin_y
            x2 = x1 + person.bounding_box.width
            y2 = y1 + person.bounding_box.height
            score = person.categories[0].score
            personData.append({
                "index": index,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "score": score,
            })
            videoFrame = detector.markDetection(videoFrame, (x1, y1, x2, y2))

        # Add timestamp to image
        currentTimeObj = localtime(currentTime/1000)
        detector.setCustomText(
            videoFrame,
            (10, 20),
            f"{strftime('%Y-%m-%d %H:%M:%S', currentTimeObj)} {currentTimeObj.tm_zone}",
        )

        # Add description to image
        detector.setCustomText(
            videoFrame,
            (10, 40),
            description
        )
        _, buffer = imencode(".jpeg", videoFrame)

        # Add image to buffer
        bufferData.setData(buffer.tobytes())
        # Send message to MQTT server with base64 encoded image
        snapshot = b64encode(buffer).decode("utf-8")
        payload = {
            "snapshot": {"image": f"data:image/jpeg;base64,{snapshot}", "width": capWidth, "height": capHeight},
            "timestamp": currentTime,
            "persons": {
                "count": len(personData),
                "data": personData
            },
            "alert": len(personData) > 0
        }
        mqttClient.publish(mqttTopic, dumps(payload))


if __name__ == "__main__":
    main()
