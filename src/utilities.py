import configparser
import re
import os
import bs4
import json
import urllib.request
import errno

from bs4.element import Comment


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


class Configs:
    cfg_file = "configs.ini"
    input_file = "input.txt"
    config = {}
    parsed = False

    @staticmethod
    def parse_config_file():
        config_parser = configparser.RawConfigParser()
        config_parser.read([Configs.cfg_file, Configs.input_file])

        Configs.config['try_to_find_out_titles'] = config_parser.getboolean('config', "try_to_find_out_titles")
        Configs.config['matching_minimum_score'] = config_parser.getint('config', 'matching_minimum_score')

        Configs.config['label_description'] = json.loads(config_parser.get('extraction_details', 'label_description'))
        Configs.config['usual_words'] = json.loads(config_parser.get('extraction_details', 'usual_words'))
        Configs.config['measurements'] = json.loads(config_parser.get('extraction_details', 'measurements'))
        Configs.config['sizes'] = config_parser.get('extraction_details', 'sizes')

        Configs.config['urls'] = dict(config_parser.items('input_urls'))

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
        string = insensitive_word.sub(replace, string)

    return string


def load_page(url):
    req = urllib.request.Request(
        url,
        data=None,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        }
    )

    data = urllib.request.urlopen(req, timeout=4)

    return bs4.BeautifulSoup(data.read().decode('utf-8'), 'html5lib')


def create_dir(dirname):
    if not os.path.exists(dirname):
        try:
            os.makedirs(dirname)
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
