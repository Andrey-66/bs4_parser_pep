import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import (BASE_DIR, DATETIME_FORMAT, PARSER_OUTPUT_FILE,
                       PARSER_OUTPUT_PRETTY, RESULTS_DIR)

SAVE_FILE_MESSAGE = 'Файл с результатами был сохранён: {file_path}'


def default_output(results, **kwargs):
    for row in results:
        print(*row)


def pretty_output(results, **kwargs):
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args, encoding='utf-8', **kwargs):
    directory = BASE_DIR / RESULTS_DIR
    directory.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    now_formatted = dt.datetime.now().strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now_formatted}.csv'
    file_path = directory / file_name
    with open(file_path, 'w', encoding=encoding) as f:
        csv.writer(f, dialect=csv.unix_dialect).writerows(results)
    logging.info(SAVE_FILE_MESSAGE.format(file_path=file_path))


OUTPUT_FUNCIONS = {
    PARSER_OUTPUT_PRETTY: pretty_output,
    PARSER_OUTPUT_FILE: file_output,
    None: default_output
}


def control_output(results, cli_args):
    output = cli_args.output
    OUTPUT_FUNCIONS[output](results=results, cli_args=cli_args)
