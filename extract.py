import bs4
from urllib.request import Request, urlopen

import xlsxwriter

from utilities import Configs


def load_page(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    web_page = urlopen(req).read().decode('utf-8')

    return bs4.BeautifulSoup(web_page, "lxml")


def write_tables_to_excel(tables, filename):
    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook('{}.xlsx'.format(filename.lstrip('''.xslx''')))
    worksheet = workbook.add_worksheet()

    row_num = 1
    for table in tables:
        for row in table.findAll("tr"):
            col_num = 0
            for elem in row:
                if isinstance(elem, bs4.NavigableString):
                    continue

                if elem.text == "":
                    col_num += 1
                    worksheet.write(row_num, col_num, " ")
                    continue

                row_span = 1
                col_span = 1

                if elem.has_attr("rowspan"):
                    row_span = int(elem["rowspan"])
                if elem.has_attr("colspan"):
                    col_span = int(elem["colspan"])

                if col_span > 1 or row_span > 1:
                    y = col_num + (col_span - 1)
                    x = row_num + (row_span - 1)
                    worksheet.merge_range(row_num, col_num, x, y, elem.text)
                else:
                    worksheet.write(row_num, col_num, elem.text)

                col_num = (col_num + 1) + (col_span - 1)
            row_num += 1
        # empty row before new table
        row_num += 1

    workbook.close()


def main():
    urls = Configs.get("urls")
    for filename, url in urls.items():
        soup = load_page(url)
        tables = soup.findAll('table')
        write_tables_to_excel(tables, filename)


if __name__ == "__main__":
    main()
