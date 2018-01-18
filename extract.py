import bs4
from bs4.element import Comment
from urllib.request import Request, urlopen

import xlsxwriter
from urllib.request import urljoin
import re
import threading
import data_precessor

from utilities import Configs

def load_page(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    web_page = urlopen(req).read().decode('utf-8')

    return bs4.BeautifulSoup(web_page, 'html5lib')


def update_columns(worksheet, row, col):
    for merge in worksheet.merge:
        if merge[0] <= row <= merge[2] and merge[1] <= col <= merge[3]:
            col += merge[3] - merge[1] + 1
            col = update_columns(worksheet, row, col)
    return col


def try_find_table_name(tb, worksheet, row_num):
    if isinstance(tb, bs4.NavigableString):
        return

    prev = tb.find_previous_siblings()
    if not prev:
        prev = tb.parent.find_previous_siblings()

    if not isinstance(prev, bs4.NavigableString) and prev and len(prev[0].text) < 30:
        worksheet.write(row_num, 0, prev[0].text.strip())


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


def write_tables_to_excel(tables, filename, domain):
    if not tables or isinstance(tables, bs4.NavigableString):
        return
    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook('{}.xlsx'.format(filename.replace('.xslx', '')))
    worksheet = workbook.add_worksheet()

    row_num = 1

    for table in tables:
        if not tag_visible(table):
            continue

        if Configs.get("try_to_find_out_titles"):
            try_find_table_name(table, worksheet, row_num)
            row_num += 1

        for row in table.findAll("tr"):
            col_num = 0
            for elem in row:
                if isinstance(elem, bs4.NavigableString):
                    continue

                tag = elem.find('a')

                hyperlink = None
                if elem.text == '':
                    text = ' '
                else:
                    if tag is not None and tag.has_attr('href'):
                        hyperlink = tag['href']
                    text = elem.text

                row_span = 1
                col_span = 1

                if elem.has_attr("rowspan"):
                    row_span = int(elem["rowspan"])
                if elem.has_attr("colspan"):
                    col_span = int(elem["colspan"])

                col_num = update_columns(worksheet, row_num, col_num)

                if col_span > 1 or row_span > 1:
                    y = col_num + (col_span - 1)
                    x = row_num + (row_span - 1)
                    if hyperlink is not None:
                        text = '''=HYPERLINK(\"{}\", \"{}\")'''.format(urljoin(domain, hyperlink), text)

                    worksheet.merge_range(row_num, col_num, x, y, text)

                else:
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
        soup = load_page(url)
        tables = soup.findAll('table')
        tables = data_precessor.get_interested_tables(tables)
        write_tables_to_excel(tables, filename, urljoin(url, '/'))

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
