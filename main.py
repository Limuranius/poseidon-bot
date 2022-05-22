import os
import src


def createFolders():
    if not os.path.exists(src.LOGS_FOLDER):
        os.mkdir(src.LOGS_FOLDER)
    if not os.path.exists(src.SCHEDULE_LOGS_PATH):
        os.mkdir(src.SCHEDULE_LOGS_PATH)


def main():
    createFolders()
    cm = src.ConfigManager()
    app = src.MyApp(cm)
    logger = src.Logger.createConsoleLabelLogger(src.kv.run_win.output_label)
    bot = src.Bot(cm, logger)
    app.setBot(bot)
    app.run()


if __name__ == "__main__":
    main()
