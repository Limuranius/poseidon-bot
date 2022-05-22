from kivy.app import App
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from ConfigManager import ConfigManager
from Bot import Bot
from Paths import KV_FILE_PATH
import threading
from typing import List, TypedDict


class FromToDict(TypedDict):
    start: str
    end: str


class LoginWinInputDict(TypedDict):
    username: str
    password: str


class ConfigWinInputDict(TypedDict):
    ExecuteAt: str
    Date: str
    MinLen: str
    MaxLen: str
    MachineNumber: str
    TimeIntervals: List[FromToDict]


class LabelInputBox(BoxLayout):
    """Виджет. Представляет из себя поле ввода с надписью"""
    input_form: TextInput = ObjectProperty(None)
    label_text = StringProperty("Default")

    def set_input(self, text: str) -> None:
        self.input_form.text = text

    def get_input(self) -> str:
        return self.input_form.text


class ContainerBox(BoxLayout):
    """Декоративный контейнер, который содержит различные виджеты"""
    pass


class MainBox(BoxLayout):
    """Декоративный контейнер. Располагается в каждом окне в вершине иерархии"""
    pass


class FromToBox(BoxLayout):
    """Виджет. Содержит поля ввода "от" и "до" """
    from_box: LabelInputBox = ObjectProperty(None)
    to_box: LabelInputBox = ObjectProperty(None)

    def remove(self) -> None:
        self.parent.remove_widget(self)

    def get_input(self) -> FromToDict:
        """Возвращает введёные значения "от" и "до" по ключам "start" и "end" соответственно"""
        return {
            "start": self.from_box.get_input(),
            "end": self.to_box.get_input()
        }

    def set_input(self, start: str, end: str) -> None:
        self.from_box.set_input(start)
        self.to_box.set_input(end)


class LoginWindow(Screen):
    username_box: LabelInputBox = ObjectProperty(None)
    password_box: LabelInputBox = ObjectProperty(None)

    @staticmethod
    def btn_save() -> None:
        App.get_running_app().saveUserConfigInput()

    def get_input(self) -> LoginWinInputDict:
        """Возвращает введённые "логин" и "пароль" по ключам "username" и "password" соответственно"""
        return {
            "username": self.username_box.get_input(),
            "password": self.password_box.get_input()
        }

    def set_input(self, username: str, password: str) -> None:
        """Записывает логин и пароль в формы"""
        self.username_box.set_input(username)
        self.password_box.set_input(password)


class ConfigWindow(Screen):
    exec_at_box: LabelInputBox = ObjectProperty(None)
    date_box: LabelInputBox = ObjectProperty(None)
    min_len_box: LabelInputBox = ObjectProperty(None)
    max_len_box: LabelInputBox = ObjectProperty(None)
    machine_number_box: LabelInputBox = ObjectProperty(None)
    time_intervals_container: ContainerBox = ObjectProperty(None)
    time_intervals_list: List[FromToBox] = []

    @staticmethod
    def btn_save() -> None:
        App.get_running_app().saveBotConfigInput()

    def append_time_interval_form(self) -> None:
        widget = FromToBox()
        self.time_intervals_container.add_widget(widget)
        self.time_intervals_list.append(widget)

    def remove_time_interval_form(self, obj: FromToBox) -> None:
        self.time_intervals_list.remove(obj)
        obj.remove()

    def get_input(self) -> ConfigWinInputDict:
        """Возвращает введёные значения по ключам
        "ExecuteAt",
        "Date",
        "MinLen",
        "MaxLen",
        "MachineNumber",
        "TimeIntervals": list[dict["start": ..., "end": ...]] """
        return {
            "ExecuteAt": self.exec_at_box.get_input(),
            "Date": self.date_box.get_input(),
            "MinLen": self.min_len_box.get_input(),
            "MaxLen": self.max_len_box.get_input(),
            "MachineNumber": self.machine_number_box.get_input(),
            "TimeIntervals": [interval.get_input() for interval in self.time_intervals_list]
        }

    def set_input(self, exec_at: str, date: str, min_len: str, max_len: str, machine_number: str,
                  time_intervals: List[FromToDict]) -> None:
        self.exec_at_box.set_input(exec_at)
        self.date_box.set_input(date)
        self.min_len_box.set_input(min_len)
        self.max_len_box.set_input(max_len)
        self.machine_number_box.set_input(machine_number)

        # Расфасовываем информацию из time_intervals по формам
        while len(self.time_intervals_list) < len(
                time_intervals):  # Если вставляем больше информации, чем у нас есть форм
            self.append_time_interval_form()
        for i in range(len(self.time_intervals_list)):
            interval_box = self.time_intervals_list[i]
            interval = time_intervals[i]
            interval_box.set_input(interval["start"], interval["end"])


class RunWindow(Screen):
    output_label: Label = ObjectProperty(None)

    @staticmethod
    def btn_run() -> None:
        bot_thread = threading.Thread(target=App.get_running_app().runBot)
        bot_thread.start()


class WindowsManager(ScreenManager):
    login_win: LoginWindow = ObjectProperty(None)
    config_win: ConfigWindow = ObjectProperty(None)
    run_win: RunWindow = ObjectProperty(None)


kv = Builder.load_file(KV_FILE_PATH)


class MyApp(App):
    config_manager: ConfigManager
    bot: Bot
    root: WindowsManager

    def __init__(self, config_manager: ConfigManager, bot: Bot = None, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = config_manager
        self.bot = bot

    def on_start(self):
        self.loadUserConfig()
        self.loadBotConfig()

    def build(self):
        return kv

    def setBot(self, bot: Bot) -> None:
        self.bot = bot

    def getOutputLabel(self) -> Label:
        return self.root.run_win.output_label

    def runBot(self) -> None:
        self.bot.run()

    def saveUserConfigInput(self) -> None:
        login_input = self.root.login_win.get_input()
        self.bot.config_manager.setUsername(login_input["username"])
        self.bot.config_manager.setPassword(login_input["password"])
        self.bot.config_manager.saveToUserDataFile()

    def saveBotConfigInput(self) -> None:
        config_input = self.root.config_win.get_input()
        self.bot.config_manager.setExecuteAt(config_input["ExecuteAt"])
        self.bot.config_manager.setDate(config_input["Date"])
        self.bot.config_manager.setMinTimeLength(config_input["MinLen"])
        self.bot.config_manager.setMaxTimeLength(config_input["MaxLen"])
        self.bot.config_manager.setMachineNumber(int(config_input["MachineNumber"]))
        self.bot.config_manager.setTimeIntervals(config_input["TimeIntervals"])
        self.bot.config_manager.saveToConfigFile()

    def loadUserConfig(self) -> None:
        username = self.bot.config_manager.username
        password = self.bot.config_manager.password
        self.root.login_win.set_input(username, password)

    def loadBotConfig(self) -> None:
        exec_at = self.bot.config_manager.getExecAtString()
        date = self.bot.config_manager.getDateString()
        min_len = self.bot.config_manager.getMinTimeLengthString()
        max_len = self.bot.config_manager.getMaxTimeLengthString()
        machine_number = self.bot.config_manager.getMachinNumberString()
        time_intervals = self.bot.config_manager.getTimeIntervalsString()
        self.root.config_win.set_input(exec_at, date, min_len, max_len, machine_number, time_intervals)
