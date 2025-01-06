class Buffer:

    __data: bytes

    def __init__(self) -> None:
        self.__data = b""

    def setData(self, data: bytes) -> None:
        self.__data = data

    def getData(self) -> bytes:
        return self.__data
