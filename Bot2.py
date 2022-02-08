import time
import datetime
from selenium import webdriver
from MyData import MyData
import requests
import bs4
import json
from fake_useragent import UserAgent

PATH = "C:/Program Files (x86)/chromedriver.exe"
LOG_FILE_PATH = "log.txt"


def get_metas(response_text: str) -> dict[str, str]:
    soup = bs4.BeautifulSoup(response_text, features="html.parser")
    metas = soup.find_all("meta")
    return {meta.get("name"): meta.get("content") for meta in metas}


def log_message(message: str):
    with open(LOG_FILE_PATH, "a") as file:
        file.write(f"{datetime.datetime.now()}   {message}\n")


driver = webdriver.Chrome(PATH)

# -------------------------------Signing in esa.dvfu.ru-----------------------------------------------
log_message("Signing in esa.dvfu.ru...")
driver.get("https://esa.dvfu.ru/?bu=https://poseidon.dvfu.ru/index.php")

username = driver.find_element_by_id("inputAccount")  #
password = driver.find_element_by_id("inputPwd")  # Находим поля авторизации

username.send_keys(MyData.username)  #
password.send_keys(MyData.password)  # Вводим данные в поля авторизации

login_button = driver.find_element_by_name("login-button")  # Находим кнопку "Войти"
login_button.click()

# -------------------------------Poseidon index-------------------------------------------------------
driver.implicitly_wait(5)
log_message("Getting to book page...")

book = driver.find_element_by_id("block-1").find_element_by_tag_name("a")  # Находим кнопку "Запись на стирку"
book.click()

# -------------------------------Getting data from book page------------------------------------------
log_message("Getting data from book page...")
page_metas = get_metas(driver.page_source)

ua = UserAgent()
headers = {
    "User-Agent": ua.random,
    "X-CSRF-TOKEN": page_metas["csrf_token"],
    "X-csrftoken": page_metas["csrf-token-value"]
}

params = {
    "date": "Thu Feb 10 2022"
}

# Переносим все куки из браузера в requests.Session
cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
session = requests.Session()
for c in cookies.items():
    session.cookies.set(c[0], c[1])

day_is_available = False
while not day_is_available:
    response = session.get('https://poseidon.dvfu.ru/includes/get-events.php', headers=headers, params=params)
    if response.text == "":  # День ещё не открылся
        log_message("Day is not available yet")
        time.sleep(2)
    else:
        log_message("Got data!")
        day_is_available = True

with open("day_table.txt", "w", encoding="utf-8") as file:
    json_response = json.loads(response.text)
    json.dump(json_response, file, indent=4)

# -------------------------------Booking time---------------------------------------------------------
log_message("Booking time")
data_array = [  # Список времён, которые хотим занять
    {
        "start": "10-02-2022 07:00:00",
        "end": "10-02-2022 08:00:00",
        "number": "2"
    },
    {
        "start": "10-02-2022 08:00:00",
        "end": "10-02-2022 09:00:00",
        "number": "2"
    },
    {
        "start": "10-02-2022 09:00:00",
        "end": "10-02-2022 10:00:00",
        "number": "2"
    },
    {
        "start": "10-02-2022 10:00:00",
        "end": "10-02-2022 11:00:00",
        "number": "2"
    }]

for data in data_array:
    log_message(f"Booking time from {data['start']} to {data['end']} on machine #{data['number']}...")
    book_response = session.post("https://poseidon.dvfu.ru/includes/check-events.php", headers=headers, data=data)
    json_response = json.loads(book_response.text)
    if json_response["success"] == True:
        log_message("Successful!")
        break
    else:
        log_message("Failed")
        time.sleep(1)


