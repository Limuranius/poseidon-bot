import requests
import bs4
import json
from MyData import MyData


def get_metas(response_text: str) -> dict:
    soup = bs4.BeautifulSoup(response_text, features="html.parser")
    metas = soup.find_all("meta")
    return {meta.get("name"): meta.get("content") for meta in metas}


dvfu_auth_url = "https://esa.dvfu.ru/"

dvfu_auth_headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
}

session = requests.Session()
response = session.get(dvfu_auth_url, headers=dvfu_auth_headers)
attrs = get_metas(response.text)

dvfu_auth_data = {
    "_csrf_univer": attrs["csrf-token"],
    "csrftoken": attrs["csrf-token-value"],
    "username": MyData.username,
    "password": MyData.password,
    "bu": "https://poseidon.dvfu.ru/index.php",
    "rememberMe": "1"
}

post_response = session.post(dvfu_auth_url, data=dvfu_auth_data, headers=dvfu_auth_headers)


print(session.cookies.get_dict())

poseidon_book_url = "https://poseidon.dvfu.ru/includes/check-events.php"
poseidon_index_url = "https://poseidon.dvfu.ru/index.php"
session.get(poseidon_index_url, headers=dvfu_auth_headers)
print(session.cookies.get_dict())

poseidon_book_data = {
    "start": "16-01-2022 11:00:00",
    "end": "16-01-2022 12:00:00",
    "number": "2"
}

session.get(poseidon_book_url, headers=dvfu_auth_headers)
response = session.post(poseidon_book_url, data=poseidon_book_data, headers=dvfu_auth_headers)
print(response.status_code)
print(response.text)
