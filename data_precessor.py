import openpyxl
import swalign
import string
import re

from utilities import Configs
from utilities import replace_words

def process_data(files):
    for file in files:
        wb = openpyxl.load_workbook(file)
        sheet_names = wb.get_sheet_names()
        for sheet_name in sheet_names:
            sheet = wb.get_sheet_by_name(sheet_name)


def adopt_to_algorithm(in_str):
    # remove digits from table
    remove_digits = str.maketrans('', '', string.digits)
    out_str = in_str.translate(remove_digits)

    # remove whitespace characters
    out_str = ' '.join(out_str.split())

    # remove special characters
    out_str = re.sub('[,.\"\'/()-]', '', out_str)

    # remove country аbbreviations
    out_str = re.sub('EU|USA|AU|UK|ITA|IT|FR|FRA|ITA', '', out_str)

    # remove frequently encountered words
    return replace_words(out_str, [('SMALL', 'S'),
                                   ('LARGE', 'L'),
                                   ('MEDIUM', 'M'),
                                   ('CHEST', ''),
                                   ('WIDTH', ''),
                                   ('LENGTH', ''),
                                   ('WIDTH', ''),
                                   ('SOCKS', ''),
                                   ('BUST', ''),
                                   ('WAIST', ''),
                                   (' CM ', ''),
                                   ('LEG', ''),
                                   ('INCHES', ''),
                                   ('INCH', ''),
                                   ('BLAZERS', ''),
                                   ('TROUSERS', ''),
                                   ('BLAZER', '')])


# setup smith waterman and return instance
def get_smith_waterman():
    match = 4
    mismatch = -1
    scoring = swalign.NucleotideScoringMatrix(match, mismatch)
    return swalign.LocalAlignment(scoring)


# use smith waterman algorithm
def get_interested_tables(tables):
    filtered_tables = []
    sizes = Configs.get('sizes')
    allowed_score = Configs.get('matching_minimum_score')
    for table in tables:
        my_table = adopt_to_algorithm(table.text)
        if not my_table:
            continue

        sw = get_smith_waterman()
        alignment = sw.align(my_table, sizes)
        if alignment.score >= allowed_score:
            filtered_tables += table

    return filtered_tables
