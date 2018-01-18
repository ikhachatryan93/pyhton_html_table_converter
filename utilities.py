import configparser
from os import path
import sys
import re

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
        Configs.config['try_to_find_out_titles'] = config_parser.getboolean('config', "try_to_find_out_titles")
        Configs.config['write_in_one_file'] = config_parser.getboolean('config', 'write_in_one_file')
        Configs.config['sizes'] = config_parser.get('international_sizes', 'sizes')
        Configs.config['matching_minimum_score'] = config_parser.getint('config', 'matching_minimum_score')

        Configs.read = True

    @staticmethod
    def get(key):
        if not Configs.parsed:
            Configs.parse_config_file()
        return Configs.config[key]


# case insensitive
def replace_words(string, pairs):
    for word, replace in pairs:
        insensitive_word = re.compile(re.escape(word), re.IGNORECASE)
        return insensitive_word.sub(replace, string)
