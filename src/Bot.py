import time
import datetime
from ScheduleSolver import ScheduleSolver
import requests
import bs4
import json
from fake_useragent import UserAgent
from Paths import SCHEDULE_PATH, SCHEDULE_LOGS_PATH
from ConfigManager import ConfigManager
from Logger import LoggerInterface
import pyautogui
import threading
import multiprocessing


class Bot:
    session: requests.Session
    ua: UserAgent
    poseidon_headers: dict
    config_manager: ConfigManager
    solver: ScheduleSolver
    logger: LoggerInterface

    def __init__(self, config_manager: ConfigManager, logger: LoggerInterface):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.poseidon_headers = {}
        self.config_manager = config_manager
        self.solver = ScheduleSolver(self.config_manager)
        self.logger = logger

    def accessBookPage(self) -> None:
        self.logger.log("Signing in esa.dvfu.ru...")

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
            "username": self.config_manager.username,
            "password": self.config_manager.password,
            "bu": "https://poseidon.dvfu.ru/index.php",
        }
        self.session.post("https://esa.dvfu.ru/", data=data, headers={
            "User-Agent": self.ua.chrome
        })

        # Заходим на страницу посейдона
        self.logger.log("Getting to book page...")
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
                                        "date": self.config_manager.date.strftime("%a %b %d %Y")  # Mon May 02 2022
                                    })
        return response.text

    def getScheduleJSON(self) -> dict:
        """Возможна ошибка, если запрос возвращает пустую строку"""
        return json.loads(self.getScheduleStr())

    def waitTillDayOpen(self) -> dict:
        self.logger.log(f"Getting schedule on {self.config_manager.date}...")
        while True:
            schedule = self.getScheduleStr()
            if schedule == "":  # День ещё не открылся
                self.logger.log("Day is not available yet")
                time.sleep(1)
            else:
                self.logger.log("Day opened!")
                return json.loads(schedule)

    def updateScheduleFile(self, sch_json: dict) -> None:
        self.logger.log("Updating schedule.json")
        with open(SCHEDULE_PATH, "w") as file:
            json.dump(sch_json, file)
        if self.config_manager.log_schedules:
            with open(f"{SCHEDULE_LOGS_PATH}/{datetime.datetime.now().strftime('%d%m%Y %H.%M.%S.%f')}.json",
                      "w") as file:
                json.dump(sch_json, file, indent=3, ensure_ascii=False)
        self.solver.read_schedule()

    def tryBookTime(self) -> bool:
        fmt = "%d-%m-%Y %H:%M:%S"  # Например, 05-03-2022 07:00:00
        intervals = self.solver.getPerfectMatches()
        for i in range(min(self.config_manager.post_count, len(intervals))):
            interval = intervals[i]
            data = {
                "start": interval[0].strftime(fmt),
                "end": interval[1].strftime(fmt),
                "number": str(self.config_manager.machine_number),  # Номер машинки
            }
            self.logger.log(f"Booking time from {data['start']} to {data['end']} on machine #{data['number']}...")
            book_response = self.session.post("https://poseidon.dvfu.ru/includes/check-events.php",
                                              headers=self.poseidon_headers,
                                              data=data)
            book_response = json.loads(book_response.text)
            if book_response["success"]:
                self.logger.log("Successful!")
                return True
            else:
                self.logger.log("Failed")
        return False

    def waitUntil(self, exec_time: datetime.time):
        self.logger.log(f"Ждём до: {exec_time}")
        sleep_preventer = multiprocessing.Process(target=prevent_sleep)
        sleep_preventer.start()
        while datetime.datetime.today().time() < exec_time:
            time.sleep(1)
        sleep_preventer.terminate()
        self.logger.log(f"Дождались!")

    def run(self):
        self.waitUntil(self.config_manager.exec_at)

        self.accessBookPage()

        curr_schedule = self.waitTillDayOpen()
        self.updateScheduleFile(curr_schedule)

        success = False
        while not success:
            success = self.tryBookTime()
            self.updateScheduleFile(self.getScheduleJSON())
            if len(self.solver.getPerfectMatches()) == 0:
                self.logger.log("No matching times left. Task failed! Good luck next week!")
                break
        self.logger.log("Process finished.")


def prevent_sleep():
    """
    Не даёт компу уснуть
    """
    interval = 240
    while True:
        pyautogui.press("volumeup")
        time.sleep(0.5)
        pyautogui.press("volumedown")
        time.sleep(interval)


def get_metas(response_text: str) -> dict[str, str]:
    soup = bs4.BeautifulSoup(response_text, features="html.parser")
    metas = soup.find_all("meta")
    return {meta.get("name"): meta.get("content") for meta in metas}
