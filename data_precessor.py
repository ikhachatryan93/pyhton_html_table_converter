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
    # remove digit information from table
    remove_digits = str.maketrans('', '', string.digits)
    out_str = in_str.translate(remove_digits)
    out_str_ = ' '.join(out_str.split())

    # remove special characters
    out_str = re.sub('[,.\"\'/()-]', '', out_str_)
    out_str = re.sub('EU|US|AU|UK|BUST|WAIST|CM|SIZE|Size|Length|LENGTH|WIDTH|SOCKS|Socks', '', out_str)
    return replace_words(out_str, [('SMALL', 'S'),
                                   ('LARGE', 'L'),
                                   ('MEDIUM', 'M')])


# use smith waterman algorithm
def get_interested_tables(tables):
    filtered_tables = []
    sizes = Configs.get('sizes')
    match = 4
    mismatch = -1
    allowed_score = Configs.get('matching_minimum_score')
    for table in tables:
        # remove multiple whitespaces, and numbers as only letters are needed for detecting (S M L XS XM XL) like
        # rows/columns
        my_table = adopt_to_algorithm(table.text)
        my_table = ' '.join(my_table.split())
        scoring = swalign.NucleotideScoringMatrix(match, mismatch)
        sw = swalign.LocalAlignment(scoring)
        alignment = sw.align(my_table, sizes)
        if alignment.score >= allowed_score:
            filtered_tables += table

    return table
