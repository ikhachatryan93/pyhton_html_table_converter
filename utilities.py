import configparser
from os import path
import sys

dir_path = path.dirname(path.realpath(__file__))
sys.path.append(dir_path + "modules")
sys.path.append(dir_path + "drivers")


class Configs:
    file = r"./configs.txt"
    config = {}
    parsed = False

    @staticmethod
    def parse_config_file():
        config_parser = configparser.RawConfigParser()
        config_parser.read(Configs.file)

        Configs.config['urls'] = dict(config_parser.items('urls'))

        Configs.read = True

    @staticmethod
    def get(key):
        if not Configs.parsed:
            Configs.parse_config_file()
        return Configs.config[key]