import DelayedExecution
from paths import *
import json
import os


def createFolders():
    if not os.path.exists(LOGS_FOLDER):
        os.mkdir(LOGS_FOLDER)


def main():
    input("Заполните файл botconfig.json и нажмите Enter, чтобы продолжить\n")
    createFolders()
    with open(BOT_CONFIG_PATH, "r") as file:
        js = json.load(file)
        execute_at = js["ExecuteAt"]
    DelayedExecution.wait(execute_at)


if __name__ == "__main__":
    main()
