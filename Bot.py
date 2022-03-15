import time
import datetime
from MyData import MyData
from ScheduleSolver import ScheduleSolver
import requests
import bs4
import json
from fake_useragent import UserAgent
from paths import *


class Bot:
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.poseidon_headers = None

        self.solver = ScheduleSolver()  # Вычисляет подходящие времена
        self.date = None  # Дата, на которую записываемся
        self.post_count = None  # Сколько запросов отправится перед тем, как бот обновить таблицу занятых ячеек
        self.log_schedules = None  # Надо ли на каждом обновлении записывать расписание в новый файл
        self.readConfig()

    def readConfig(self):
        with open(BOT_CONFIG_PATH, "r") as file:
            config_json = json.load(file)
        self.date = datetime.datetime.strptime(config_json["Date"], "%d.%m.%Y").date()
        self.post_count = config_json["POST_COUNT_BEFORE_UPDATE"]
        self.log_schedules = config_json["LOG_SCHEDULES"]

    def accessBookPage(self) -> None:
        log_message("Signing in esa.dvfu.ru...")

        # Заходим на страницу ДВФУ
        response = self.session.get("https://esa.dvfu.ru/", headers={
            "User-Agent": self.ua.chrome
        })
        # Получаем метатеги страницы
        page_metas = get_metas(response.text)

        # Логинимся в учётную запись ДВФУ
        data = {
            "_csrf_univer": page_metas["csrf-token"],
            "csrftoken": page_metas["csrf-token-value"],
            "username": MyData.username,
            "password": MyData.password,
            "bu": "https://poseidon.dvfu.ru/index.php",
        }
        self.session.post("https://esa.dvfu.ru/", data=data, headers={
            "User-Agent": self.ua.chrome
        })

        # Заходим на страницу посейдона
        log_message("Getting to book page...")
        response = self.session.get("https://poseidon.dvfu.ru/index.php", headers={
            "User-Agent": self.ua.chrome
        })
        # Получаем токены страницы
        page_metas = get_metas(response.text)
        self.poseidon_headers = {
            "User-Agent": self.ua.chrome,
            "X-CSRF-TOKEN": page_metas["csrf_token"],
            "X-csrftoken": page_metas["csrf-token-value"]
        }
        # Отправляем запрос на авторизацию, иначе ничего не заработает
        self.session.get("https://poseidon.dvfu.ru/includes/auth.php", headers=self.poseidon_headers)

    def getScheduleStr(self) -> str:
        response = self.session.get('https://poseidon.dvfu.ru/includes/get-events.php',
                                    headers=self.poseidon_headers,
                                    params={
                                        "date": self.date
                                    })
        return response.text

    def getScheduleJSON(self) -> dict:
        """Возможна ошибка, если запрос возвращает пустую строку"""
        return json.loads(self.getScheduleStr())

    def waitTillDayOpen(self) -> dict:
        log_message(f"Getting schedule on {self.date}...")
        while True:
            schedule = self.getScheduleStr()
            if schedule == "":  # День ещё не открылся
                log_message("Day is not available yet")
                time.sleep(1)
            else:
                log_message("Day opened!")
                return json.loads(schedule)

    def updateScheduleFile(self, sch_json: dict) -> None:
        log_message("Updating schedule.json")
        with open(SCHEDULE_PATH, "w") as file:
            json.dump(sch_json, file)
        if self.log_schedules:
            with open(f"{LOGS_FOLDER}/{datetime.datetime.now().strftime('%d%m%Y %H.%M.%S.%f')}.json", "w") as file:
                json.dump(sch_json, file, indent=3, ensure_ascii=False)
        self.solver.read_schedule()

    def tryBookTime(self) -> bool:
        fmt = "%d-%m-%Y %H:%M:%S"  # Например, 05-03-2022 07:00:00
        intervals = self.solver.getPerfectMatches()
        for i in range(min(self.post_count, len(intervals))):
            interval = intervals[i]
            data = {
                "start": interval[0].strftime(fmt),
                "end": interval[1].strftime(fmt),
                "number": "2",  # Номер машинки
            }
            log_message(f"Booking time from {data['start']} to {data['end']} on machine #{data['number']}...")
            book_response = self.session.post("https://poseidon.dvfu.ru/includes/check-events.php",
                                              headers=self.poseidon_headers,
                                              data=data)
            book_response = json.loads(book_response.text)
            if book_response["success"]:
                log_message("Successful!")
                return True
            else:
                log_message("Failed")
        return False

    def run(self):
        self.accessBookPage()

        curr_schedule = self.waitTillDayOpen()
        self.updateScheduleFile(curr_schedule)

        success = False
        while not success:
            success = self.tryBookTime()
            self.updateScheduleFile(self.getScheduleJSON())
            if len(self.solver.getPerfectMatches()) == 0:
                log_message("No matching times left. Task failed! Good luck next week!")
                break
        log_message("Process finished.")


def get_metas(response_text: str) -> dict[str, str]:
    soup = bs4.BeautifulSoup(response_text, features="html.parser")
    metas = soup.find_all("meta")
    return {meta.get("name"): meta.get("content") for meta in metas}


def log_message(message: str):
    with open(LOG_FILE_PATH, "a") as file:
        file.write(f"{datetime.datetime.now()}   {message}\n")


def run():
    bot = Bot()
    bot.run()


if __name__ == "__main__":
    run()
