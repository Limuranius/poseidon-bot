import sys
import os

fpath = os.path.dirname(__file__)
sys.path.append(fpath)

from Bot import Bot
from ConfigManager import ConfigManager
from Paths import *
import Logger
from ui import MyApp, kv
