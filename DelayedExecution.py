import pyautogui
import time
import datetime
import multiprocessing
import Bot


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


def get_curr_date_with_custom_time(time_str: str) -> datetime.datetime:
    """
    :param time_str: hh:mm:ss
    """
    time_list = [int(i) for i in time_str.split(":")]
    t = datetime.time(hour=time_list[0], minute=time_list[1], second=time_list[2])
    d = datetime.date.today()
    return datetime.datetime.combine(d, t)


def wait(execute_at: str):
    target_time = get_curr_date_with_custom_time(execute_at)
    sleep_preventer = multiprocessing.Process(target=prevent_sleep)
    sleep_preventer.start()
    while True:
        curr_time = datetime.datetime.today()
        if curr_time >= target_time:
            sleep_preventer.terminate()
            break
        time.sleep(0.5)
    Bot.run()
