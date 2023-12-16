import logging
import re
from collections import defaultdict
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, MAIN_DOC_URL, PEP_URL, EXPECTED_STATUS, DOWNLOADS_DIR
from outputs import control_output
from utils import find_tag, get_soup

DOWNLOAD_MSG = 'Архив был загружен и сохранён: {archive_path}'
START_MSG = 'Парсер запущен!'
NOT_FIND_MSG = 'Ничего не нашлось'
ERR_MSG = 'Ошибка во время выполнения: {err}'
ARGS_MSG = 'Аргументы командной строки: {args}'
END_MSG = 'Парсер завершил работу.'
STATUS_ERR_MSG = ('Несовпадающие статусы:\n'
                  '{url}\n'
                  'Статус в карточке: {status_pep_page}\n'
                  'Ожидаемые статусы: '
                  '{expected_status}')
DOC_HREF = 'Ссылка на документацию'
PAGE_HREF = 'Ссылка на статью'
VERSION = 'Версия'
STATUS = 'Статус'
TITLE = 'Заголовок'
AUTHOR = 'Редактор, Автор'
COUNT = 'Количество'
TOTAL = 'Итог'


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    soup = get_soup(session, whats_new_url)
    sections_by_python = soup.select('#what-s-new-in-python div.toctree-wrapper li.toctree-l1')

    results = [(PAGE_HREF, TITLE, AUTHOR)]
    for section in tqdm(sections_by_python):
        version_a_tag = section.find('a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        soup = get_soup(session, version_link)
        if soup is None:
            continue
        results.append(
            (
                version_link,
                find_tag(soup, 'h1').text,
                find_tag(soup, 'dl').text.replace('\n', ' ')
            )
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
        raise ValueError(NOT_FIND_MSG)
    results = [(DOC_HREF, VERSION, STATUS)]
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
    pdf_a4_link = soup.select_one('div[role="main"] table.docutils a[href$="pdf-a4.zip"]')['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]

    download_dir.mkdir(exist_ok=True)
    archive_path = download_dir / filename

    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(DOWNLOAD_MSG.format(archive_path=archive_path))


def pep(session):
    soup = get_soup(session, PEP_URL)
    section_tag = find_tag(soup, 'section', attrs={'id': 'numerical-index'})
    tbody_tag = find_tag(section_tag, 'tbody')
    tr_tags = tbody_tag.find_all('tr')
    status_sum = defaultdict(int)
    results = [(STATUS, COUNT)]
    warning_messages = []
    for tag in tqdm(tr_tags):
        status_list = list(find_tag(tag, 'abbr').text)
        status = ''
        if len(status_list) > 1:
            status = status_list[1:][0]
        url = urljoin(PEP_URL, find_tag(tag, 'a', attrs={
            'class': 'pep reference internal'})['href'])
        element_soup = get_soup(session, url)
        table = find_tag(element_soup, 'dl',
                         attrs={'class': 'rfc2822 field-list simple'})
        status_pep_page = table.find(
            string='Status').parent.find_next_sibling('dd').string
        status_sum[status_pep_page] += 1
        if status_pep_page not in EXPECTED_STATUS[status]:
            warning_messages.append(STATUS_ERR_MSG.format(
                url=url,
                status_pep_page=status_pep_page,
                expected_status=EXPECTED_STATUS[status])
            )
    logging.warning('\n'.join(warning_messages))
    return [
        ('Статус', 'Количество'),
        *results.items(),
        ('Всего', sum(results.values())),
    ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info(START_MSG)
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(ARGS_MSG.format(args=args))
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    try:
        results = MODE_TO_FUNCTION[parser_mode](session)
        if results is not None:
            control_output(results, args)
    except Exception as e:
        logging.error(ERR_MSG.format(err=e))
    logging.info(END_MSG)


if __name__ == '__main__':
    main()
