import time
import datetime
from selenium.webdriver.common.by import By
from selenium import webdriver
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
        self.poseidon_headers = None

        self.driver = webdriver.Chrome(DRIVER_PATH)
        self.driver.implicitly_wait(10)

        self.solver = ScheduleSolver()  # Вычисляет подходящие времена
        self.date = None  # Дата, на которую записываемся
        self.post_count = None  # Сколько запросов отправится перед тем, как бот обновить таблицу занятых ячеек
        self.readConfig()

    def readConfig(self):
        with open(BOT_CONFIG_PATH, "r") as file:
            config_json = json.load(file)
        self.date = datetime.datetime.strptime(config_json["Date"], "%d.%m.%Y").date()
        self.post_count = config_json["POST_COUNT_BEFORE_UPDATE"]

    def accessBookPage(self) -> None:
        log_message("Signing in esa.dvfu.ru...")
        self.driver.get("https://esa.dvfu.ru/?bu=https://poseidon.dvfu.ru/index.php")

        username = self.driver.find_element(By.ID, "inputAccount")  #
        password = self.driver.find_element(By.ID, "inputPwd")  # Находим поля авторизации

        username.send_keys(MyData.username)  #
        password.send_keys(MyData.password)  # Вводим данные в поля авторизации

        login_button = self.driver.find_element(By.NAME, "login-button")  # Находим кнопку "Войти"
        login_button.click()

        log_message("Getting to book page...")
        book = self.driver.find_element(By.ID, "block-1").find_element(By.TAG_NAME,
                                                                       "a")  # Находим кнопку "Запись на стирку"
        book.click()

    def updateHeaders(self) -> None:
        page_metas = get_metas(self.driver.page_source)
        ua = UserAgent()
        self.poseidon_headers = {
            "User-Agent": ua.random,
            "X-CSRF-TOKEN": page_metas["csrf_token"],
            "X-csrftoken": page_metas["csrf-token-value"]
        }

    def transportCookies(self) -> None:
        # Переносим все куки из браузера в requests.Session
        cookies = {c["name"]: c["value"] for c in self.driver.get_cookies()}
        for c in cookies.items():
            self.session.cookies.set(c[0], c[1])

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
        with open(f"files/{datetime.datetime.now().strftime('%H.%M.%S.%f')}.json", "w") as file:
            json.dump(sch_json, file)
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


def get_metas(response_text: str) -> dict[str, str]:
    soup = bs4.BeautifulSoup(response_text, features="html.parser")
    metas = soup.find_all("meta")
    return {meta.get("name"): meta.get("content") for meta in metas}


def log_message(message: str):
    with open(LOG_FILE_PATH, "a") as file:
        file.write(f"{datetime.datetime.now()}   {message}\n")


def main():
    bot = Bot()
    bot.accessBookPage()
    bot.updateHeaders()
    bot.transportCookies()

    curr_schedule = bot.waitTillDayOpen()
    bot.updateScheduleFile(curr_schedule)

    success = False
    while not success:
        success = bot.tryBookTime()
        bot.updateScheduleFile(bot.getScheduleJSON())
        if len(bot.solver.getPerfectMatches()) == 0:
            log_message("No matching times left. Task failed! Good luck next week!")
            break
    log_message("Process finished.")


if __name__ == "__main__":
    main()
