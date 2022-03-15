import json
import datetime
from paths import *

datePair = tuple[datetime.datetime, datetime.datetime]


class ScheduleSolver:
    def __init__(self):
        self.schedule_json = None
        # self.read_schedule()

        self.config_json = None
        self.date = None
        self.min_pref_len = None
        self.max_pref_len = None
        self.pref_intervals = None
        self.read_config()

    def read_schedule(self):
        with open(SCHEDULE_PATH, "r") as file:
            self.schedule_json = json.load(file)

    def read_config(self):
        with open(BOT_CONFIG_PATH, "r") as file:
            self.config_json = json.load(file)
        self.date = datetime.datetime.strptime(self.config_json["Date"], "%d.%m.%Y").date()
        self.updatePreferredTimeIntervals()
        self.updatePreferredTimeLength()

    def updatePreferredTimeIntervals(self):
        intervals = [(i["start"], i["end"]) for i in self.config_json["TimeIntervals"]]
        parsed_intervals = []
        for interval in intervals:
            start = datetime.datetime.strptime(interval[0], "%H:%M").time()
            start = datetime.datetime.combine(self.date, start)
            end = datetime.datetime.strptime(interval[1], "%H:%M").time()
            end = datetime.datetime.combine(self.date, end)
            parsed_intervals.append((start, end))
        self.pref_intervals = parsed_intervals

    def updatePreferredTimeLength(self):
        hours, minutes = [int(i) for i in self.config_json["MinTimeLength"].split(":")]
        self.min_pref_len = datetime.timedelta(hours=hours, minutes=minutes)
        hours, minutes = [int(i) for i in self.config_json["MaxTimeLength"].split(":")]
        self.max_pref_len = datetime.timedelta(hours=hours, minutes=minutes)

    def getFreeTimeIntervals(self) -> list[datePair]:
        intervals = []
        for interval in self.schedule_json["data"][1]["entries"]:
            if interval["isBusy"]:
                continue
            else:
                start = datetime.datetime.strptime(interval["start"], "%Y/%m/%d %H:%M:%S")  # "2022/03/05 07:00:00"
                max_end = datetime.datetime.strptime(interval["max_end"], "%Y/%m/%d %H:%M:%S")
                intervals.append((start, max_end))
        return intervals

    def applyPreferredTimeLength(self, intervals: list[datePair]) -> list[datePair]:
        new_intervals = []
        for interval in intervals:
            dt = interval[1] - interval[0]
            if self.min_pref_len <= dt <= self.max_pref_len:
                new_intervals.append(interval)
        return new_intervals

    def applyPreferredTimeIntervals(self, intervals: list[datePair]) -> list[datePair]:
        new_intervals = []
        for interval in intervals:
            start, end = interval
            for pref_interval in self.pref_intervals:
                pref_start, pref_end = pref_interval
                if start >= pref_start or end <= pref_end:  # Если промежутки хоть как-то пересекаются
                    new_intervals.append((max(start, pref_start), min(end, pref_end)))
        return new_intervals

    def removeOverlappingIntervals(self, intervals: list[datePair]):
        new_intervals = []
        intervals = sorted(list(set(intervals)))  # Убираем дупликаты
        for i in range(len(intervals)):
            interv1 = intervals[i]
            is_overlapped = False
            for j in range(len(intervals)):
                if i != j:
                    interv2 = intervals[j]
                    if interv2[0] <= interv1[0] and interv1[1] <= interv2[1]:
                        is_overlapped = True
                        break
            if not is_overlapped:
                new_intervals.append(interv1)
        return new_intervals

    def getPerfectMatches(self) -> list[datePair]:
        intervals = self.getFreeTimeIntervals()
        intervals = self.applyPreferredTimeIntervals(intervals)
        intervals = self.applyPreferredTimeLength(intervals)
        intervals = self.removeOverlappingIntervals(intervals)
        return intervals


def inputPreferredTimeLength() -> datetime.timedelta:
    while True:
        inp = input(
            "Введите минимальную продолжительность сеанса в формате hh:mm, кратную 15 минутам. Например, 2:15\n")
        # inp = "2:15"
        if isDateCorrect(inp):
            hours, minutes = [int(i) for i in inp.split(":")]
            return datetime.timedelta(hours=hours, minutes=minutes)
        else:
            print("Неверный ввод! Попробуйте снова.")


def isDateCorrect(date: str) -> bool:
    """Проверяет на правильность дату формата hh:mm, делящуюся на 15 минут"""
    date = date.split(":")
    if len(date) == 2:
        if date[0].isdigit() and date[1].isdigit():
            hours = int(date[0])
            minutes = int(date[1])
            if (minutes < 60) and ((hours * 60 + minutes) <= 180) and ((hours * 60 + minutes) % 15 == 0):
                return True
    return False
