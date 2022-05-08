from kivy.app import App
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from ConfigManager import ConfigManager
from Bot import Bot
import threading


class LoginWindow(Screen):
    username_box = ObjectProperty(None)
    password_box = ObjectProperty(None)

    def btn_save(self):
        App.get_running_app().saveUserConfigInput()

    def get_input(self) -> dict:
        """Возвращает введённые "логин" и "пароль" по ключам "username" и "password" соответственно"""
        return {
            "username": self.username_box.get_input(),
            "password": self.password_box.get_input()
        }

    def set_input(self, username: str, password: str):
        """Записывает логин и пароль в формы"""
        self.username_box.set_input(username)
        self.password_box.set_input(password)


class FromToBox(BoxLayout):
    from_box = ObjectProperty(None)
    to_box = ObjectProperty(None)

    def remove(self):
        self.parent.remove_widget(self)

    def get_input(self) -> dict:
        """Возвращает введёные значения "от" и "до" по ключам "start" и "end" соответственно"""
        return {
            "start": self.from_box.get_input(),
            "end": self.to_box.get_input()
        }

    def set_input(self, start: str, end: str):
        self.from_box.set_input(start)
        self.to_box.set_input(end)


class ConfigWindow(Screen):
    exec_at_box = ObjectProperty(None)
    date_box = ObjectProperty(None)
    min_len_box = ObjectProperty(None)
    max_len_box = ObjectProperty(None)
    machine_number_box = ObjectProperty(None)
    time_intervals_container = ObjectProperty(None)
    time_intervals_list: list[FromToBox] = []

    def btn_save(self):
        App.get_running_app().saveBotConfigInput()

    def append_time_interval_form(self):
        widget = FromToBox()
        self.time_intervals_container.add_widget(widget)
        self.time_intervals_list.append(widget)

    def remove_time_interval_form(self, obj: FromToBox):
        self.time_intervals_list.remove(obj)
        obj.remove()

    def get_input(self) -> dict:
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
                  time_intervals: list[dict]):
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
    output_label = ObjectProperty(None)

    def btn_run(self):
        bot_thread = threading.Thread(target=App.get_running_app().runBot)
        bot_thread.start()


class LabelInputBox(BoxLayout):
    input_form = ObjectProperty(None)
    label_text = StringProperty("Default")

    def set_input(self, text: str):
        self.input_form.text = text

    def get_input(self):
        return self.input_form.text


class WindowsManager(ScreenManager):
    login_win = ObjectProperty(None)
    config_win = ObjectProperty(None)
    run_win = ObjectProperty(None)


kv = Builder.load_file("ui.kv")


class MyApp(App):
    config_manager: ConfigManager
    bot: Bot

    def __init__(self, config_manager: ConfigManager, bot: Bot = None, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = config_manager
        self.bot = bot

    def on_start(self):
        self.loadUserConfig()
        self.loadBotConfig()

    def build(self):
        return kv

    def setBot(self, bot: Bot):
        self.bot = bot

    def getOutputLabel(self):
        return self.root.run_win.output_label

    def runBot(self):
        self.bot.run()

    def saveUserConfigInput(self):
        login_input = self.root.login_win.get_input()
        self.bot.config_manager.setUsername(login_input["username"])
        self.bot.config_manager.setPassword(login_input["password"])
        self.bot.config_manager.saveToUserDataFile()

    def saveBotConfigInput(self):
        config_input = self.root.config_win.get_input()
        self.bot.config_manager.setExecuteAt(config_input["ExecuteAt"])
        self.bot.config_manager.setDate(config_input["Date"])
        self.bot.config_manager.setMinTimeLength(config_input["MinLen"])
        self.bot.config_manager.setMaxTimeLength(config_input["MaxLen"])
        self.bot.config_manager.setMachineNumber(config_input["MachineNumber"])
        self.bot.config_manager.setTimeIntervals(config_input["TimeIntervals"])
        self.bot.config_manager.saveToConfigFile()

    def loadUserConfig(self):
        username = self.bot.config_manager.username
        password = self.bot.config_manager.password
        self.root.login_win.set_input(username, password)

    def loadBotConfig(self):
        exec_at = self.bot.config_manager.getExecAtString()
        date = self.bot.config_manager.getDateString()
        min_len = self.bot.config_manager.getMinTimeLengthString()
        max_len = self.bot.config_manager.getMaxTimeLengthString()
        machine_number = self.bot.config_manager.getMachinNumberString()
        time_intervals = self.bot.config_manager.getTimeIntervalsString()
        self.root.config_win.set_input(exec_at, date, min_len, max_len, machine_number, time_intervals)
