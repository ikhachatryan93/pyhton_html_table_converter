import string
import re
import xlsxwriter
import bs4
from urllib.request import urljoin

from utilities import Configs
from utilities import replace_words
from utilities import load_page
from utilities import tag_visible

from os import path, sep
import sys

# add local modules into PATH
dir_path = path.dirname(path.realpath(__file__))
sys.path.insert(0, dir_path + sep + "modules")

import swalign


#class Data:
#    serial_no = 0
#    data = dict(Serial_No=0, Brand='', Website_Link='', Measurement=[], Standard_Sizing=[],
#                Metric=[], XXS=[], XXS_=[], XS=[], XS_=[], S=[], S_=[], M=[], M_=[], L=[], L_=[],
#                XL=[], XL_=[], XXL=[], XXL_=[], XXXL=[], XXXL_=[], XXXXL=[], XXXXL_=[])
#
#    @staticmethod
#    def find_metric_info_from_cell(target):
#        if 'INCHES' in target.upper() or '"' in target:
#            Data.data['Metric'] = 'inches'
#            return True
#        elif 'CM' == target.upper() or "CENTIMETER" in target.upper():
#            Data.data['Metric'] = target.lower()
#            return True
#        return False
#
#    @staticmethod
#    def collect_data(worksheet, brand):
#        Data.data['Serial_No'] = Data.serial_no
#        Data.data['Brand'] = brand
#        Data.data['Website_Link'] = str(Configs.get('urls')[brand])
#
#        if is_vertical_table(worksheet):
#            rows = worksheet.iter_cols()
#        else:
#            rows = worksheet.iter_rows()
#
#        val = str(rows[0].value.strip())
#        key = ""
#        idx = 0
#        if val in Configs.get('sizes'):
#            key = val
#            idx = 1
#
#        for cell in rows[idx:]:
#            target = str(cell.value).strip()
#
#            if not target:
#                continue
#
#            if re.match(r'((^\d+(\.\d*)?)(\"?))$', target):
#                # size but unknown Metric
#                if not key:
#                    continue
#
#                Data.data[key].append(float(target.rstrip('\"')))
#                if '\"' in target:
#                    Data.data['Metric'] = 'inches'
#                continue
#
#            ######### check for measurement #########
#            cont = False
#            for measurement in Configs.get('measurements'):
#                find_metric_info_from_cell(target)
#                if measurement.upper() in target.upper():
#                    data['Measurement'] = measurement
#                    cont = True
#            if cont:
#                continue
#            ###################################
#
#            ######### check for ##########
#
#            find_metric_info_from_cell(target)
#
#        return False


def is_vertical_table(wsheet):
    sw = get_smith_waterman()
    allowed_score = Configs.get('matching_minimum_score')
    for column in wsheet.iter_cols(max_col=1):
        column_as_string = ''
        for cell in column:
            column_as_string += str(cell.value)

        adopted_str = adopt_to_algorithm(column_as_string)
        alignment = sw.align(adopted_str, Configs.get('sizes'))
        if alignment.score >= allowed_score:
            return True

    return False


# rotate from (S) to (S M L) format
#             (M)
#             (L)
def rotate_to_horizontal(wb):
    sheet_names = wb.get_sheet_names()
    for sheet_name in sheet_names:
        wsheet = wb.get_sheet_by_name(sheet_name)
        if is_vertical_table(wsheet):
            wsheet_rotated = wb.create_sheet("new")
            for idx, row in enumerate(wsheet.rows):
                for idy, cell in enumerate(row):
                    wsheet_rotated.cell(row=idy + 1, column=idx + 1).value = cell.value
            wb.remove_sheet(wsheet)
            wsheet_rotated.title = sheet_name


# return closest number, if distance is same return smallest one
def get_closest_number(a, b, c):
    dist1 = abs(c - a)
    dist2 = abs(c - b)

    if dist1 == dist2:
        return min(a, b)

    return min([a, b], key=lambda v: abs(c - v))


def try_find_table_name(tb):
    if tb:
        tags = tb.find_previous_siblings()
    else:
        return "TABLENAME_N.A"

    if tags:
        for tag in reversed(tags):
            if tag.name == 'table' or tag.name == 'img' or len(tag.text.strip()) > 40:
                tags.remove(tag)

    if not tags:
        return try_find_table_name(tb.parent)

    titles = Configs.get("label_description")
    # sm = get_smith_waterman()
    if tags:
        for tag in tags[:1]:
            if not isinstance(tag, bs4.NavigableString):
                supposed_title = tag.text.strip()
                if not supposed_title:
                    continue

                # best_title_score = 0
                best_title = ''
                best_title_string = ''
                for title in titles:
                    if title.upper() in supposed_title.upper():
                        best_title = title
                        best_title_string = supposed_title

                if best_title:
                    if len(str(best_title_string)) < 20:
                        whitelist = set('abcdefghijklmnopqrstuvwxy ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                        cleaned_up_text = ''.join(filter(whitelist.__contains__, str(best_title_string.strip())))
                        return cleaned_up_text
                    else:
                        return best_title.strip().upper()
    return 'TABLENAME_N.A'


def update_columns(worksheet, row, col):
    for merge in worksheet.merge:
        if merge[0] <= row <= merge[2] and merge[1] <= col <= merge[3]:
            col += merge[3] - merge[1] + 1
            col = update_columns(worksheet, row, col)
    return col


def write_tables_to_excel(tables, filename, domain):
    if (not tables) or isinstance(tables, bs4.NavigableString):
        return False

    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook('{}.xlsx'.format(filename.replace('.xslx', '')))

    unknown_worksheet_id = 0
    for table in tables:
        if not tag_visible(table) or isinstance(table, bs4.NavigableString):
            continue

        row_num = 0

        if Configs.get("try_to_find_out_titles"):
            title = try_find_table_name(table)

            idx = ''
            while True:
                try:
                    worksheet = workbook.add_worksheet('{}{}'.format(title, idx))
                    break
                except Exception as msg:
                    if str(msg).startswith("Sheetname") and "with case ignored, is already in use." in str(msg):
                        idx = 1 if not idx else idx + 1
                    else:
                        print(msg)
                        exit

        for row in table.findAll("tr"):
            col_num = 0
            for elem in row:
                if isinstance(elem, bs4.NavigableString):
                    continue

                hyperlink = ''
                text = ''
                if elem.text:
                    tag = elem.find('a')
                    if tag and tag.has_attr('href'):
                        hyperlink = tag['href']
                    text = elem.text

                # remove extra new lines
                if text:
                    text = text.strip()

                if not text:
                    text = ' '

                row_span = 1
                col_span = 1

                # get html rowspan and colspan values, use them in cells merging
                if elem.has_attr("rowspan"):
                    row_span = int(elem["rowspan"])
                if elem.has_attr("colspan"):
                    col_span = int(elem["colspan"])

                # Do some magic to fix merged columns issues
                col_num = update_columns(worksheet, row_num, col_num)
                if hyperlink:
                    text = '''=HYPERLINK(\"{}\", \"{}\")'''.format(urljoin(domain, hyperlink), text)

                # write in merged cells
                if col_span > 1 or row_span > 1:
                    y = col_num + (col_span - 1)
                    x = row_num + (row_span - 1)
                    worksheet.merge_range(row_num, col_num, x, y, text)

                else:
                    # write in a single cell
                    worksheet.write(row_num, col_num, text)

                col_num = (col_num + 1) + (col_span - 1)
            row_num += 1

    workbook.close()
    return True


def adopt_to_algorithm(in_str):
    # remove digits from table
    remove_digits = str.maketrans('', '', string.digits)
    out_str = in_str.translate(remove_digits)

    # remove whitespace characters
    out_str = ' '.join(out_str.split())

    # remove special characters
    out_str = re.sub('[,.\"\'/()-]', '', out_str)

    # remove country аbbreviations
    out_str = re.sub('ITA|IT|FRA|FR|EUR|EU|USA|US|AU|UK', '', out_str)

    # temporary remove some words to get more correct results in smith-waterman
    words_to_replace = []
    for option in Configs.get('label_description'):
        words_to_replace.append(tuple((option, '')))

    for option in Configs.get('usual_words'):
        words_to_replace.append(tuple((option, '')))

    words_to_replace.append(tuple(('¼', '')))
    words_to_replace.append(tuple(('½', '')))
    words_to_replace.append(tuple(('¾', '')))
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
        heads = table.findAll('thead')
        if heads:
            for head in heads[1:]:
                head.decompose()

        bodies = table.findAll('tbody')
        if bodies:
            for body in bodies[1:]:
                body.decompose()

        if isinstance(table, bs4.NavigableString):
            continue

        my_table = adopt_to_algorithm(table.text)
        if not my_table:
            continue

        alignment = sw.align(my_table, sizes)
        if alignment.score >= allowed_score:
            filtered_tables.append(table)

    return filtered_tables
