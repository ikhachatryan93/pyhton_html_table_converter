import bs4
from bs4.element import Comment
import xlsxwriter
from urllib.request import urljoin

from utilities import Configs
from utilities import load_page
from os import path, sep
import sys

# add local modules into PATH
#dir_path = path.dirname(path.realpath(__file__))
#sys.path.insert(0, dir_path + sep + "modules")

import data_precessor


def update_columns(worksheet, row, col):
    for merge in worksheet.merge:
        if merge[0] <= row <= merge[2] and merge[1] <= col <= merge[3]:
            col += merge[3] - merge[1] + 1
            col = update_columns(worksheet, row, col)
    return col


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


def write_tables_to_excel(tables, filename, domain):
    if (not tables) or isinstance(tables, bs4.NavigableString):
        return

    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook('{}.xlsx'.format(filename.replace('.xslx', '')))
    worksheet = workbook.add_worksheet()

    row_num = 0

    for table in tables:
        if not tag_visible(table) or isinstance(table, bs4.NavigableString):
            continue

        if Configs.get("try_to_find_out_titles"):
            title = data_precessor.try_find_table_name(table)
            worksheet.write(row_num, 0, title)
            row_num += 1

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
        # empty row before new table
        row_num += 1

    workbook.close()


def write_in_single_file(urls):
    tables = []
    for filename, url in urls.items():
        print("Extracting tables from {}".format(filename))
        soup = load_page(url)
        tables += soup.findAll('table')

    if tables:
        write_tables_to_excel(tables, 'output', 'www.unknownwebsite.com')


def write_in_multiple_files(urls):
    for filename, url in urls.items():
        print("Extracting tables from {}".format(filename))
        tables = data_precessor.get_interested_tables(url)
        write_tables_to_excel(tables, filename, urljoin(url, '/'))
        # write_tables_to_excel(tables, filename, urljoin(url, '/'))


# def process_date(files)

def main():
    files = []
    urls = Configs.get('urls')
    if Configs.get('write_in_one_file'):
        files = write_in_single_file(urls)
    else:
        files = write_in_multiple_files(urls)

    print("Processing extracting data...")
    # printcess_data(files)


if __name__ == "__main__":
    main()
