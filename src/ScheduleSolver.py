import json
import datetime
from ConfigManager import ConfigManager
from Paths import SCHEDULE_PATH

datePair = tuple[datetime.datetime, datetime.datetime]


class ScheduleSolver:
    schedule_json: dict
    config_manager: ConfigManager

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def read_schedule(self):
        with open(SCHEDULE_PATH, "r") as file:
            self.schedule_json = json.load(file)

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
            if self.config_manager.min_pref_len <= dt <= self.config_manager.max_pref_len:
                new_intervals.append(interval)
        return new_intervals

    def applyPreferredTimeIntervals(self, intervals: list[datePair]) -> list[datePair]:
        new_intervals = []
        for interval in intervals:
            start, end = interval
            for pref_interval in self.config_manager.time_intervals:
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
