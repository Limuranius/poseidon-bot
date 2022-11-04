import time
import datetime
from ScheduleSolver import ScheduleSolver
import requests
import bs4
import json
from Paths import SCHEDULE_PATH, SCHEDULE_LOGS_PATH
from ConfigManager import ConfigManager
from Logger import LoggerInterface
from typing import Dict

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"

FEFU_URL = "https://esa.dvfu.ru/"
POSEIDON_INDEX_URL = "https://poseidon.dvfu.ru/index.php"
POSEIDON_AUTH_URL = "https://poseidon.dvfu.ru/includes/auth.php"
POSEIDON_GET_EVENTS_URL = "https://poseidon.dvfu.ru/includes/get-events.php"
POSEIDON_POST_EVENTS_URL = "https://poseidon.dvfu.ru/includes/check-events.php"



class Bot:
    session: requests.Session
    poseidon_headers: dict
    config_manager: ConfigManager
    solver: ScheduleSolver
    logger: LoggerInterface

    def __init__(self, config_manager: ConfigManager, logger: LoggerInterface):
        self.session = requests.Session()
        self.poseidon_headers = {}
        self.config_manager = config_manager
        self.solver = ScheduleSolver(self.config_manager)
        self.logger = logger

    def __auth_at_FEFU(self) -> None:
        """Авторизуется на сайте ДВФУ под учёткой пользователя и собирает все необходимые куки"""

        self.logger.log("Signing in to esa.dvfu.ru...")

        # Заходим на страницу ДВФУ
        response = self.session.get(FEFU_URL, headers={
            "User-Agent": USER_AGENT
        })
        # Получаем метатеги страницы
        page_metas = _get_metas(response.text)

        # Логинимся в учётную запись ДВФУ
        data = {
            "_csrf_univer": page_metas["csrf-token"],
            "csrftoken": page_metas["csrf-token-value"],
            "username": self.config_manager.username,
            "password": self.config_manager.password,
            "bu": POSEIDON_INDEX_URL,
        }
        self.session.post(FEFU_URL, data=data, headers={
            "User-Agent": USER_AGENT
        })

    def __auth_at_Poseidon(self) -> None:
        """Логинится на сайте Посейдона, используя куки, полученные при авторизации на сайте ДВФУ"""

        self.logger.log("Signing in to poseidon.dvfu.ru...")

        # Заходим на страницу посейдона
        response = self.session.get(POSEIDON_INDEX_URL, headers={
            "User-Agent": USER_AGENT
        })
        # Получаем CSRF токен страницы
        page_metas = _get_metas(response.text)
        self.poseidon_headers = {
            "User-Agent": USER_AGENT,
            "X-CSRF-TOKEN": page_metas["csrf_token"],
            "X-csrftoken": page_metas["csrf-token-value"]
        }
        # Отправляем запрос на авторизацию, иначе ничего не заработает
        self.session.get(POSEIDON_AUTH_URL, headers=self.poseidon_headers)

    def __getScheduleStr(self) -> str:
        """
        Запрашивает расписание с сайта.
        Возвращает ответ в виде строки.
        Если расписания на данный день ещё нет, то возвращает пустую строку.
        """
        response = self.session.get(POSEIDON_GET_EVENTS_URL,
                                    headers=self.poseidon_headers,
                                    params={
                                        "date": self.config_manager.Date.strftime("%a %b %d %Y")  # Mon May 02 2022
                                    })
        return response.text

    def __getScheduleJSON(self) -> dict:
        """Запрашивает расписание с сайта и возвращает ответ в виде объекта JSON"""
        return json.loads(self.__getScheduleStr())

    def __updateScheduleFile(self, schedule_json: dict) -> None:
        """
        Записывает в json с расписанием новое расписание
        Сохраняет расписание в логи, если функция включена в конфиге
        """
        self.logger.log("Updating schedule.json")
        with open(SCHEDULE_PATH, "w") as file:
            json.dump(schedule_json, file)
        if self.config_manager.LOG_SCHEDULES:
            with open(f"{SCHEDULE_LOGS_PATH}/{datetime.datetime.now().strftime('%d%m%Y %H.%M.%S.%f')}.json",
                      "w") as file:
                json.dump(schedule_json, file, indent=3, ensure_ascii=False)
        self.solver.read_schedule()

    def __tryBookTime(self) -> bool:
        """
        Используя раннее полученное расписание, совершает POST_COUNT_BEFORE_UPDATE попыток записаться.
        Если записаться получилось, возвращает True. Иначе False.
        """
        fmt = "%d-%m-%Y %H:%M:%S"  # Формат даты, отправляемой на сервер. Например, 05-03-2022 07:00:00
        intervals = self.solver.getPerfectMatches()  # Интервалы, подходящие под параметры конфига
        for i in range(min(self.config_manager.POST_COUNT_BEFORE_UPDATE, len(intervals))):
            interval = intervals[i]
            data = {
                "start": interval[0].strftime(fmt),
                "end": interval[1].strftime(fmt),
                "number": str(self.config_manager.MachineNumber),  # Номер машинки
            }
            self.logger.log(f"Booking time from {data['start']} to {data['end']} on machine #{data['number']}...")
            book_response = self.session.post(POSEIDON_POST_EVENTS_URL,
                                              headers=self.poseidon_headers,
                                              data=data)  # Отправляем запрос на запись на определённое время
            book_response = json.loads(book_response.text)
            if book_response["success"]:  # Записаться получилось
                self.logger.log("Successful!")
                return True
            else:  # Время занято
                self.logger.log("Failed")
        return False

    def __waitTillDayOpen(self) -> dict:
        """
        В цикле проверяет, не появилось ли расписание на день записи.
        Когда оно появится, возвращает расписание в виде JSON-объекта.
        """
        self.logger.log(f"Getting schedule on {self.config_manager.Date}...")
        while True:
            schedule = self.__getScheduleStr()
            if schedule == "":  # День ещё не открылся
                self.logger.log("Day is not available yet")
                time.sleep(1)
            else:
                self.logger.log("Day opened!")
                return json.loads(schedule)

    def __waitUntil(self, exec_time: datetime.time) -> None:
        """Останавливает работу программы, пока часы не стукнут exec_time"""
        self.logger.log(f"Waiting until: {exec_time}")
        while datetime.datetime.today().time() < exec_time:
            time.sleep(1)
        self.logger.log(f"Pizza time!")

    def run(self) -> None:
        # Останавливаем программу, пока не наступит время ExecuteAt
        self.__waitUntil(self.config_manager.ExecuteAt)

        # Логинимся на сайтах
        self.__auth_at_FEFU()
        self.__auth_at_Poseidon()

        # Ждём, когда на сайте появится расписание и записываем его в файл
        curr_schedule = self.__waitTillDayOpen()
        self.__updateScheduleFile(curr_schedule)

        while True:
            success = self.__tryBookTime()  # Пробуем записаться
            if success:  # Если записаться удалось, прекращаем попытки записаться
                break

            # Если записаться не удалось, заново обращаемся на сервер, смотрим, какие интервалы ещё не заняли
            self.__updateScheduleFile(self.__getScheduleJSON())
            if len(self.solver.getPerfectMatches()) == 0:  # Если не осталось ни одного свободного интервала
                self.logger.log("No matching times left. Task failed! Good luck next week!")
                break
        self.logger.log("Process finished.")


def _get_metas(response_text: str) -> Dict[str, str]:
    """Получает все meta-теги страницы"""
    soup = bs4.BeautifulSoup(response_text, features="html.parser")
    metas = soup.find_all("meta")
    return {meta.get("name"): meta.get("content") for meta in metas}
