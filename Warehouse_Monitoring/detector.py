from typing import Any, Tuple
from cv2 import COLOR_BGR2RGBA, FONT_HERSHEY_SIMPLEX, LINE_AA, cvtColor, getTextSize, putText, rectangle
from mediapipe.tasks.python import vision
from mediapipe.tasks import python as mpPython
from mediapipe import Image as MpImage, ImageFormat as MpImageFormat
from numpy import mean


class Detector:

    __detector: Any

    def __init__(self, modelPath: str, scoreThreshold: float) -> None:
        options = vision.ObjectDetectorOptions(
            base_options=mpPython.BaseOptions(model_asset_path=modelPath),
            score_threshold=scoreThreshold,
        )
        self.__detector = vision.ObjectDetector.create_from_options(options)

    def getDetections(self, frame: Any) -> Any:
        image = MpImage(
            image_format=MpImageFormat.SRGBA,
            data=cvtColor(frame, COLOR_BGR2RGBA),
        )
        return self.__detector.detect(image).detections

    def markDetection(
        self,
        image: Any,
        bounds: tuple[int, int, int, int],
    ) -> Any:
        x1, y1, x2, y2 = bounds
        rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 1)
        return image

    def setCustomText(self, image: Any, position: Tuple[int, int], text: str) -> Any:
        x, y = position

        for char in text:
            char_size = getTextSize(char, FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            roi = image[y-15:y+char_size[1], x:x+char_size[0]]
            mean_brightness = mean(roi)

            text_color = (0, 0, 0) if mean_brightness > 127 else (
                255, 255, 255)

            putText(image, char, (x, y), FONT_HERSHEY_SIMPLEX,
                    0.5, text_color, 1, LINE_AA)

            x += char_size[0]

        return image
