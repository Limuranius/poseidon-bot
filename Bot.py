import requests
import bs4
import json
import pprint
from MyData import MyData


def get_metas(response_text: str) -> dict:
    soup = bs4.BeautifulSoup(response_text, features="html.parser")
    metas = soup.find_all("meta")
    return {meta.get("name"): meta.get("content") for meta in metas}


dvfu_auth_url = "https://esa.dvfu.ru/"

dvfu_auth_headers = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'
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
with open("text.txt", "w", encoding="utf-8") as file_write:
    file_write.write(post_response.text)

poseidon_book_url = "https://poseidon.dvfu.ru/includes/check-events.php"
poseidon_index_url = "https://poseidon.dvfu.ru/index.php"
poseidon_request = session.get(poseidon_index_url, headers=dvfu_auth_headers)
poseidon_metas = get_metas(poseidon_request.text)
with open("poseidon_index.txt", "w", encoding="utf-8") as file_write:
    file_write.write(poseidon_request.text)

poseidon_book_data = {
    "start": "16-01-2022 11:00:00",
    "end": "16-01-2022 12:00:00",
    "number": "2"
}
# dvfu_auth_headers["X-CSRF-Token"] = "fetch"
# print(session.get("https://poseidon.dvfu.ru", headers=dvfu_auth_headers).text)

# print(session.get(poseidon_book_url, headers=dvfu_auth_headers).text)
# response = session.post(poseidon_book_url, data=poseidon_book_data, headers=dvfu_auth_headers)
# print(poseidon_metas)

# print(session.cookies.get_dict())
# print(session.cookies.get_dict())
dvfu_auth_headers["X-CSRF-TOKEN"] = poseidon_metas["csrf_token"]
dvfu_auth_headers["X-csrftoken"] = poseidon_metas["csrf-token-value"]
response = session.get(
    "https://poseidon.dvfu.ru/includes/get-events.php",  # https://poseidon.dvfu.ru/includes/auth.php
    params={
        "date": "Sun Jan 30 2022"
    },
    headers=dvfu_auth_headers)

print(response.status_code)
# pprint.pprint(json.loads(response.text))
print(response.text)
print(session.cookies.get_dict())