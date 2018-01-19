import openpyxl
import swalign
import string
import re
import bs4
import json
import time

from utilities import Configs
from utilities import replace_words
from utilities import load_page


def process_data(files):
    for file in files:
        wb = openpyxl.load_workbook(file)
        sheet_names = wb.get_sheet_names()
        for sheet_name in sheet_names:
            sheet = wb.get_sheet_by_name(sheet_name)


# return closest number, if distance is same return smallest one
def get_closest_number(a, b, c):
    dist1 = abs(c - a)
    dist2 = abs(c - b)

    if dist1 == dist2:
        return min(a, b)

    return min([a, b], key=lambda v: abs(c - v))


def try_find_table_name(tb):
    tags = []
    if tb:
        tags = tb.find_previous_siblings()
    else:
        return "UNKNOWN"

    if tags:
        for tag in reversed(tags):
            if tag.name == 'table' or len(tag.text.strip()) > 40:
                tags.remove(tag)

    if not tags:
        return try_find_table_name(tb.parent)

    titles = Configs.get("label_description")
    #sm = get_smith_waterman()
    if tags:
        for tag in tags:
            if not isinstance(tag, bs4.NavigableString):
                if 'DRESSES'.upper() in tag.text.upper():
                    print('asd')

                supposed_title = tag.text.strip()

                # best_title_score = 0
                best_title = ''
                for title in titles:
                    # alignment = sm.align(title, supposed_title, case_sensitive=False)
                    # alignment = sm.align(title, supposed_title)
                    if title.upper() in supposed_title.upper():
                        best_title = title
                    # if alignment.identity == 1 and alignment.score >= best_title_score:

                    # if scores are equal, get closest one with length of text
                    # if alignment.score == best_title_score:
                    #    len1 = len(best_title)
                    #    len2 = len(title)
                    #    # find closest text size to html_supposed_title
                    #    if len1 == get_closest_number(len1, len2, len(supposed_title)):
                    #        continue

                    # best_title_score = alignment.score
                    # best_title = title

                if best_title:
                    return best_title.strip()
                    return


def adopt_to_algorithm(in_str):
    # remove digits from table
    remove_digits = str.maketrans('', '', string.digits)
    out_str = in_str.translate(remove_digits)

    # remove whitespace characters
    out_str = ' '.join(out_str.split())

    # remove special characters
    out_str = re.sub('[,.\"\'/()-]', '', out_str)

    # remove country аbbreviations
    out_str = re.sub('EU|USA|AU|UK|ITA|IT|FR|FRA', '', out_str)

    # temporary remove some words to get more correct results in smith-waterman
    words_to_replace = []
    for option in Configs.get('label_description'):
        words_to_replace.append(tuple((option, '')))

    for option in Configs.get('usual_words'):
        words_to_replace.append(tuple((option, '')))

    words_to_replace.append(tuple(('SMALL', 'S')))
    words_to_replace.append(tuple(('LARGE', 'L')))
    words_to_replace.append(tuple(('MEDIUM', 'M')))

    return replace_words(out_str, words_to_replace).strip()


# setup smith waterman and return instance
def get_smith_waterman():
    match = 4
    mismatch = -1
    scoring = swalign.NucleotideScoringMatrix(match, mismatch)
    return swalign.LocalAlignment(scoring, globalalign=True)


# use smith waterman algorithm
def get_interested_tables(url):
    soup = load_page(url)
    tables = soup.findAll('table')

    filtered_tables = []

    sizes = Configs.get('sizes')
    allowed_score = Configs.get('matching_minimum_score')

    sw = get_smith_waterman()
    for table in tables:
        if isinstance(table, bs4.NavigableString):
            continue

        my_table = adopt_to_algorithm(table.text)
        if not my_table:
            continue

        alignment = sw.align(my_table, sizes)
        if alignment.score >= allowed_score:
            filtered_tables.append(table)

    return filtered_tables
