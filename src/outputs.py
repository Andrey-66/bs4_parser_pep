import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import BASE_DIR, DATETIME_FORMAT, RESULTS_DIR

SAVE_FILE_MESSAGE = 'Файл с результатами был сохранён: {file_path}'
PRETTY_OUTPUT = 'pretty'
FILE_OUTPUT = 'file'
FILE_ENCODING = 'utf-8'


def default_output(results):
    for row in results:
        print(*row)


def pretty_output(results, **kwargs):
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args, **kwargs):
    directory = BASE_DIR / RESULTS_DIR
    directory.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now_formatted}.csv'
    file_path = directory / file_name
    with open(file_path, 'w', encoding=FILE_ENCODING) as f:
        writer = csv.writer(f, dialect=csv.unix_dialect)
        writer.writerows(results)
    logging.info(SAVE_FILE_MESSAGE.format(file_path=file_path))


OUTPUT_FUNCIONS = {
    PRETTY_OUTPUT: pretty_output,
    FILE_OUTPUT: file_output,
}


def control_output(results, cli_args):
    output = cli_args.output
    if output in OUTPUT_FUNCIONS:
        OUTPUT_FUNCIONS[output](results=results, cli_args=cli_args)
    else:
        default_output(results)
