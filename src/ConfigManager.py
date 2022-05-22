from Paths import USER_DATA_PATH, BOT_CONFIG_PATH
import datetime
import json
from typing import TypedDict, List, Tuple, Dict


class FromToDict(TypedDict):
    start: str
    end: str


class ConfigInterface(TypedDict):
    ExecuteAt: str
    Date: str
    MinTimeLength: str
    MaxTimeLength: str
    MachineNumber: int
    TimeIntervals: List[FromToDict]
    POST_COUNT_BEFORE_UPDATE: int
    LOG_SCHEDULES: bool


class UserDataInterface(TypedDict):
    username: str
    password: str


datePair = Tuple[datetime.datetime, datetime.datetime]


class ConfigManager:
    config_json: ConfigInterface
    user_data_json: UserDataInterface

    username: str
    password: str

    exec_at: datetime.time
    date: datetime.date
    min_pref_len: datetime.timedelta
    max_pref_len: datetime.timedelta
    machine_number: int
    time_intervals: List[datePair]
    post_count: int
    log_schedules: bool

    def __init__(self):
        self.__readConfig()
        self.__readUserData()

    def __readUserData(self) -> None:
        with open(USER_DATA_PATH, "r") as file:
            self.user_data_json = json.load(file)
        self.username = self.user_data_json["username"]
        self.password = self.user_data_json["password"]

    def __readConfig(self) -> None:
        with open(BOT_CONFIG_PATH, "r") as file:
            self.config_json = json.load(file)
        self.exec_at = datetime.datetime.strptime(self.config_json["ExecuteAt"], "%H:%M:%S").time()
        self.date = datetime.datetime.strptime(self.config_json["Date"], "%d.%m.%Y").date()
        self.__readPreferredTimeLength()
        self.machine_number = self.config_json["MachineNumber"]
        self.__readPreferredTimeIntervals()
        self.post_count = self.config_json["POST_COUNT_BEFORE_UPDATE"]
        self.log_schedules = self.config_json["LOG_SCHEDULES"]

    def __readPreferredTimeLength(self) -> None:
        hours, minutes = [int(i) for i in self.config_json["MinTimeLength"].split(":")]
        self.min_pref_len = datetime.timedelta(hours=hours, minutes=minutes)
        hours, minutes = [int(i) for i in self.config_json["MaxTimeLength"].split(":")]
        self.max_pref_len = datetime.timedelta(hours=hours, minutes=minutes)

    def __readPreferredTimeIntervals(self) -> None:
        """Парсит значения из поля TimeIntervals из конфига, преобразовывая в объекты класса datetime"""
        intervals = [(i["start"], i["end"]) for i in self.config_json["TimeIntervals"]]
        parsed_intervals = []
        for interval in intervals:
            start = datetime.datetime.strptime(interval[0], "%H:%M").time()
            start = datetime.datetime.combine(self.date, start)
            end = datetime.datetime.strptime(interval[1], "%H:%M").time()
            end = datetime.datetime.combine(self.date, end)
            parsed_intervals.append((start, end))
        self.time_intervals = parsed_intervals

    def saveToConfigFile(self) -> None:
        with open(BOT_CONFIG_PATH, "w") as file:
            json.dump(self.config_json, file, indent=2)

    def saveToUserDataFile(self) -> None:
        with open(USER_DATA_PATH, "w") as file:
            json.dump(self.user_data_json, file, indent=2)

    def setUsername(self, username: str) -> None:
        self.username = username
        self.user_data_json["username"] = username

    def setPassword(self, password: str) -> None:
        self.password = password
        self.user_data_json["password"] = password

    def setExecuteAt(self, exec_at: str) -> None:
        self.exec_at = datetime.datetime.strptime(exec_at, "%H:%M:%S").time()
        self.config_json["ExecuteAt"] = exec_at

    def setDate(self, date: str) -> None:
        self.date = datetime.datetime.strptime(date, "%d.%m.%Y").date()
        self.config_json["Date"] = date

    def setMinTimeLength(self, min_pref_len: str) -> None:
        hours, minutes = [int(i) for i in min_pref_len.split(":")]
        self.min_pref_len = datetime.timedelta(hours=hours, minutes=minutes)
        self.config_json["MinTimeLength"] = min_pref_len

    def setMaxTimeLength(self, max_pref_len: str) -> None:
        hours, minutes = [int(i) for i in max_pref_len.split(":")]
        self.max_pref_len = datetime.timedelta(hours=hours, minutes=minutes)
        self.config_json["MaxTimeLength"] = max_pref_len

    def setMachineNumber(self, machine_number: int) -> None:
        self.machine_number = machine_number
        self.config_json["MachineNumber"] = machine_number

    def setTimeIntervals(self, time_intervals: List[FromToDict]) -> None:
        self.config_json["TimeIntervals"] = time_intervals
        self.__readPreferredTimeIntervals()

    def setPostCount(self, post_count: int) -> None:
        self.post_count = post_count
        self.config_json["POST_COUNT_BEFORE_UPDATE"] = post_count

    def setLogSchedules(self, log_schedules: bool) -> None:
        self.log_schedules = log_schedules
        self.config_json["LOG_SCHEDULES"] = log_schedules

    def getExecAtString(self) -> str:
        return self.config_json["ExecuteAt"]

    def getDateString(self) -> str:
        return self.config_json["Date"]

    def getMinTimeLengthString(self) -> str:
        return self.config_json["MinTimeLength"]

    def getMaxTimeLengthString(self) -> str:
        return self.config_json["MaxTimeLength"]

    def getMachinNumberString(self) -> str:
        return str(self.config_json["MachineNumber"])

    def getTimeIntervalsString(self) -> List[FromToDict]:
        return self.config_json["TimeIntervals"]
