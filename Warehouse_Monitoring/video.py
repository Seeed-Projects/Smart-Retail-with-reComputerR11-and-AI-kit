from cv2 import CAP_PROP_FRAME_HEIGHT, CAP_PROP_FRAME_WIDTH, VideoCapture, typing as cvTyping


class Video:

    __capture: VideoCapture

    def __init__(self, device: int, width: int, height: int) -> None:
        self.__capture = VideoCapture(device)
        self.__capture.set(CAP_PROP_FRAME_WIDTH, width)
        self.__capture.set(CAP_PROP_FRAME_HEIGHT, height)

    def capture(self) -> cvTyping.MatLike:
        _, frame = self.__capture.read()
        return frame

    def close(self) -> None:
        self.__capture.release()
