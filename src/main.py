from Paths import *
from Bot import Bot
import Logger
import os
from ui import MyApp, kv
from ConfigManager import ConfigManager


def createFolders():
    if not os.path.exists(LOGS_FOLDER):
        os.mkdir(LOGS_FOLDER)
    if not os.path.exists(SCHEDULE_LOGS_PATH):
        os.mkdir(SCHEDULE_LOGS_PATH)


def main():
    createFolders()
    cm = ConfigManager()
    app = MyApp(cm)
    logger = Logger.createConsoleLabelLogger(kv.run_win.output_label)
    bot = Bot(cm, logger)
    app.setBot(bot)
    app.run()


if __name__ == "__main__":
    main()
