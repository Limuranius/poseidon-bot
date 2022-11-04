from Paths import USER_DATA_PATH, BOT_CONFIG_PATH
import datetime
import json
from typing import List, Tuple, Any
from dataclasses import dataclass


@dataclass
class Config:
    ExecuteAt: datetime.time  # Время, в которое нужно запустить бота
    Date: datetime.date  # Дата, на которую бот будет записываться
    MinTimeLength: datetime.timedelta  # Минимально возможная длительность стирки
    MaxTimeLength: datetime.timedelta  # Максимально возможная длительность стирки
    MachineNumber: int  # Номер стиральной машинки
    TimeIntervals: List[Tuple[datetime.datetime, datetime.datetime]]  # Временные интервалы, в которых бот будет искать
    POST_COUNT_BEFORE_UPDATE: int  # Сколько раз бот попытается записаться, перед тем, как обновить расписание
    LOG_SCHEDULES: bool  # Если True, то расписания будут сохранятся в папку с логами


@dataclass
class UserData:
    username: str
    password: str


class ConfigJSONEncoder(json.JSONEncoder):
    """Приводит структуры конфига к виду, необходимому для сериализации в JSON"""

    def default(self, o: Any) -> Any:
        if isinstance(o, Config):
            return {
                "ExecuteAt": o.ExecuteAt.strftime("%H:%M:%S"),
                "Date": o.Date.strftime("%d.%m.%Y"),
                "MinTimeLength": self.timedelta_to_str(o.MinTimeLength),
                "MaxTimeLength": self.timedelta_to_str(o.MaxTimeLength),
                "MachineNumber": o.MachineNumber,
                "TimeIntervals": self.serialize_intervals_list(o.TimeIntervals),
                "POST_COUNT_BEFORE_UPDATE": o.POST_COUNT_BEFORE_UPDATE,
                "LOG_SCHEDULES": o.LOG_SCHEDULES,
            }
        elif isinstance(o, UserData):
            return {
                "username": o.username,
                "password": o.password
            }

    def timedelta_to_str(self, td: datetime.timedelta):
        """Приводит datetime.timedelta к виду HH:MM"""
        seconds = td.total_seconds()
        hours = round(seconds / 3600)
        minutes = round(seconds / 60) % 60
        return "{}:{}".format(hours, minutes)

    def serialize_intervals_list(self, intervals: List[Tuple[datetime.datetime, datetime.datetime]]):
        res = []
        for interval in intervals:
            start = interval[0].strftime("%H:%M")
            end = interval[1].strftime("%H:%M")
            res.append({
                "start": start,
                "end": end
            })
        return res


class ConfigManager:
    _config: Config
    _user_data: UserData

    def __init__(self):
        with open(BOT_CONFIG_PATH, "r") as file:
            config_json = json.load(file)
            self.__readConfig(config_json)
        with open(USER_DATA_PATH, "r") as file:
            user_data_json = json.load(file)
            self.__readUserData(user_data_json)

    def __readUserData(self, user_data_json: dict) -> None:
        """Читает json с данными пользователя"""
        self._user_data.username = user_data_json["username"]
        self._user_data.password = user_data_json["password"]

    def __readConfig(self, config_json: dict) -> None:
        """Читает json с конфигом для бота"""
        self._config.ExecuteAt = datetime.datetime.strptime(config_json["ExecuteAt"], "%H:%M:%S").time()  # 15:59:30
        self._config.Date = datetime.datetime.strptime(config_json["Date"], "%d.%m.%Y").date()  # 30.06.2022
        self.__readPreferredTimeLength(config_json)
        self._config.MachineNumber = config_json["MachineNumber"]
        self.__readPreferredTimeIntervals(config_json)
        self._config.POST_COUNT_BEFORE_UPDATE = config_json["POST_COUNT_BEFORE_UPDATE"]
        self._config.LOG_SCHEDULES = config_json["LOG_SCHEDULES"]

    def __readPreferredTimeLength(self, config_json: dict) -> None:
        """Читает из конфига поля MinTimeLength и MaxTimeLength и конвертирует их в datetime.timedelta"""
        hours, minutes = [int(i) for i in config_json["MinTimeLength"].split(":")]  # 01:30
        self._config.MinTimeLength = datetime.timedelta(hours=hours, minutes=minutes)
        hours, minutes = [int(i) for i in config_json["MaxTimeLength"].split(":")]  # 03:00
        self._config.MaxTimeLength = datetime.timedelta(hours=hours, minutes=minutes)

    def __readPreferredTimeIntervals(self, config_json: dict) -> None:
        """Парсит значения из поля TimeIntervals из конфига, преобразовывая в datetime.datetime"""
        intervals = [(i["start"], i["end"]) for i in config_json["TimeIntervals"]]
        parsed_intervals = []
        for interval in intervals:
            start = datetime.datetime.strptime(interval[0], "%H:%M").time()  # 13:30
            start = datetime.datetime.combine(self._config.Date, start)  # Соединяем дату из конфига с временем
            end = datetime.datetime.strptime(interval[1], "%H:%M").time()
            end = datetime.datetime.combine(self._config.Date, end)
            parsed_intervals.append((start, end))
        self._config.TimeIntervals = parsed_intervals

    def saveToConfigFile(self) -> None:
        with open(BOT_CONFIG_PATH, "w") as file:
            json.dump(self._config, file, cls=ConfigJSONEncoder, indent=2)

    def saveToUserDataFile(self) -> None:
        with open(USER_DATA_PATH, "w") as file:
            json.dump(self._user_data, file, cls=ConfigJSONEncoder, indent=2)

    @property
    def username(self):
        return self._user_data.username

    @property
    def password(self):
        return self._user_data.password

    @property
    def ExecuteAt(self):
        return self._config.ExecuteAt

    @property
    def Date(self):
        return self._config.Date

    @property
    def MinTimeLength(self):
        return self._config.MinTimeLength

    @property
    def MaxTimeLength(self):
        return self._config.MaxTimeLength

    @property
    def MachineNumber(self):
        return self._config.MachineNumber

    @property
    def TimeIntervals(self):
        return self._config.TimeIntervals

    @property
    def POST_COUNT_BEFORE_UPDATE(self):
        return self._config.POST_COUNT_BEFORE_UPDATE

    @property
    def LOG_SCHEDULES(self):
        return self._config.LOG_SCHEDULES
