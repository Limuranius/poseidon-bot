import datetime
from Paths import LOG_FILE_PATH
from kivy.uix.label import Label


class LoggerInterface:
    def log(self, message: str):
        pass


class ConsoleLogger(LoggerInterface):
    def log(self, message: str):
        print(f"{datetime.datetime.now()}   {message}")


class FileLoggerDecorator(LoggerInterface):
    wrapped_logger: LoggerInterface
    file_path: str

    def __init__(self, logger: LoggerInterface, file_path: str):
        self.wrapped_logger = logger
        self.file_path = file_path

    def log(self, message: str):
        self.wrapped_logger.log(message)
        with open(self.file_path, "a") as file:
            file.write(f"{datetime.datetime.now()}   {message}\n")


class LabelLoggerDecorator(LoggerInterface):
    wrapped_logger: LoggerInterface
    label: Label

    def __init__(self, logger: LoggerInterface, label: Label):
        self.wrapped_logger = logger
        self.label = label

    def log(self, message: str):
        self.wrapped_logger.log(message)
        self.label.text += f"{datetime.datetime.now()}   {message}\n"


def createConsoleFileLabelLogger(label: Label):
    logger = ConsoleLogger()
    logger = FileLoggerDecorator(logger, LOG_FILE_PATH)
    logger = LabelLoggerDecorator(logger, label)
    return logger


def createConsoleLabelLogger(label: Label):
    logger = ConsoleLogger()
    logger = LabelLoggerDecorator(logger, label)
    return logger
