import logging
import re
from collections import defaultdict
from urllib.parse import urljoin

import requests_cache
from requests import RequestException
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (BASE_DIR, DOWNLOADS_DIR, EXPECTED_STATUS, MAIN_DOC_URL,
                       PEP_URL, REQUEST_ERROR_MESSAGE)
from outputs import control_output
from utils import find_tag, get_soup

DOWNLOAD_MESSAGE = 'Архив был загружен и сохранён: {archive_path}'
START_MESSAGE = 'Парсер запущен!'
NOT_FIND_MESSAGE = 'Ничего не нашлось'
ERROR_MESSAGE = 'Ошибка во время выполнения: {error}'
ARGS_MESSAGE = 'Аргументы командной строки: {args}'
END_MESSAGE = 'Парсер завершил работу.'
STATUS_ERROR_MESSAGE = ('Несовпадающие статусы:\n'
                        '{url}\n'
                        'Статус в карточке: {status_pep_page}\n'
                        'Ожидаемые статусы: '
                        '{expected_status}')


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    soup = get_soup(session, whats_new_url)
    sections_by_python = soup.select('#what-s-new-in-python '
                                     'div.toctree-wrapper '
                                     'li.toctree-l1 a')

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        href = section['href']
        version_link = urljoin(whats_new_url, href)
        try:
            soup = get_soup(session, version_link)
            results.append(
                (
                    version_link,
                    find_tag(soup, 'h1').text,
                    find_tag(soup, 'dl').text.replace('\n', ' ')
                )
            )
        except RequestException as e:
            logging.error(REQUEST_ERROR_MESSAGE.format(
                link=version_link,
                error=e)
            )

    return results


def latest_versions(session):
    soup = get_soup(session, MAIN_DOC_URL)
    sidebar = find_tag(soup, 'div', attrs={"class": "sphinxsidebarwrapper"})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise RuntimeError(NOT_FIND_MESSAGE)
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (a_tag['href'], version, status)
        )
    return results


def download(session):
    download_dir = BASE_DIR / DOWNLOADS_DIR
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    soup = get_soup(session, downloads_url)
    pdf_a4_link = soup.select_one('div[role="main"] '
                                  'table.docutils '
                                  'a[href$="pdf-a4.zip"]')['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]

    download_dir.mkdir(exist_ok=True)
    archive_path = download_dir / filename

    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(DOWNLOAD_MESSAGE.format(archive_path=archive_path))


def pep(session):
    soup = get_soup(session, PEP_URL)
    section_tag = find_tag(soup, 'section', attrs={'id': 'numerical-index'})
    tbody_tag = find_tag(section_tag, 'tbody')
    tr_tags = tbody_tag.find_all('tr')
    status_sum = defaultdict(int)
    warning_messages = []
    for tag in tqdm(tr_tags):
        status_list = list(find_tag(tag, 'abbr').text)
        status = ''
        if len(status_list) > 1:
            status = status_list[1:][0]
        url = urljoin(PEP_URL, find_tag(tag, 'a', attrs={
            'class': 'pep reference internal'})['href'])
        try:
            element_soup = get_soup(session, url)
            table = find_tag(element_soup, 'dl',
                             attrs={'class': 'rfc2822 field-list simple'})
            status_pep_page = table.find(
                string='Status').parent.find_next_sibling('dd').string
            status_sum[status_pep_page] += 1
            if status_pep_page not in EXPECTED_STATUS[status]:
                warning_messages.append(STATUS_ERROR_MESSAGE.format(
                    url=url,
                    status_pep_page=status_pep_page,
                    expected_status=EXPECTED_STATUS[status])
                )
        except RequestException as e:
            logging.error(REQUEST_ERROR_MESSAGE.format(link=url, error=e))
        logging.warning('\n'.join(warning_messages))
    return [
        ('Статус', 'Количество'),
        *status_sum.items(),
        ('Итог', sum(status_sum.values())),
    ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info(START_MESSAGE)
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(ARGS_MESSAGE.format(args=args))
    try:
        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()
        parser_mode = args.mode
        results = MODE_TO_FUNCTION[parser_mode](session)
        if results is not None:
            control_output(results, args)
    except Exception as e:
        logging.error(ERROR_MESSAGE.format(error=e))
    logging.info(END_MESSAGE)


if __name__ == '__main__':
    main()
