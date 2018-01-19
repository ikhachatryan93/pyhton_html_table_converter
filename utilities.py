import configparser
import re
import ssl
import bs4
import json
import urllib3


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
        Configs.config['matching_minimum_score'] = config_parser.getint('config', 'matching_minimum_score')

        Configs.config['label_description'] = json.loads(config_parser.get('extraction_details', 'label_description'))
        Configs.config['usual_words'] = json.loads(config_parser.get('extraction_details', 'usual_words'))
        Configs.config['sizes'] = config_parser.get('extraction_details', 'sizes')

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


http = urllib3.PoolManager()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def load_page(url):
    ##req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'})
    # sessons = requests.Session()
    # retry = Retry(connect=3, backoff_factor=0.5)
    # adapter = HTTPAdapter(max_retries=retry)
    # sessons.mount('http://', adapter)
    # sessons.mount('https://', adapter)
    # header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'}
    ##response = http.request('GET', url, headers=header)
    # response = sessons.get(url, headers=header)
    # req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'})
    # req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'})
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'}
    response = http.request('GET', url, headers=header)

    return bs4.BeautifulSoup(response.data, 'html5lib')
