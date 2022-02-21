from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
from MyData import MyData


def get_metas(response_text: str) -> dict:
    soup = BeautifulSoup(response_text, features="html.parser")
    metas = soup.find_all("meta")
    return {meta.get("name"): meta.get("content") for meta in metas}


url_dvfu = "https://esa.dvfu.ru/"
url_poseidon_index = "https://poseidon.dvfu.ru/index.php"
url_poseidon_auth = "https://poseidon.dvfu.ru/includes/auth.php"
url_poseidon_get = "https://poseidon.dvfu.ru/includes/get-events.php"
url_poseidon_book = "https://poseidon.dvfu.ru/includes/check-events.php"
url_poseidon_write = "https://poseidon.dvfu.ru/index.php#/write"

ua = UserAgent()
session = requests.Session()
response = session.get(url_dvfu, headers={
    "User-Agent": ua.random
})

attrs = get_metas(response.text)
data = {
    "_csrf_univer": attrs["csrf-token"],
    "csrftoken": attrs["csrf-token-value"],
    "username": MyData.username,
    "password": MyData.password,
    "bu": "https://poseidon.dvfu.ru/index.php",
    "rememberMe": "1"
}

session.post(url_dvfu, data=data, headers={
    "User-Agent": ua.random
})

response = session.get(url_poseidon_index, headers={
    "User-Agent": ua.random
})

attrs = get_metas(response.text)

response = session.get(url_poseidon_auth, headers={
    "User-Agent": ua.random,
    "X-CSRF-Token": attrs["csrf_token"]
})

response = session.get(url_poseidon_get, headers={
    "User-Agent": ua.random,
    "X-CSRF-Token": attrs["csrf_token"],
    "X-csrftoken": attrs["csrf-token-value"]
})

print(response.status_code)
print(response.text)
