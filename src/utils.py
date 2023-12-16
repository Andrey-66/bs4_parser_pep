import logging

from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException

REQUEST_ERROR = 'Возникла ошибка при загрузке страницы {url}'
TAG_NOT_FIND_ERROR = 'Не найден тег {tag} {attrs}'


def get_response(session, url, encoding="utf-8"):
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except RequestException:
        raise RequestException(REQUEST_ERROR.format(url=url))


def get_soup(session, url):
    response = get_response(session, url)
    if response is None:
        logging.error(f"{url} is not responding")
        return
    response.encoding = 'utf-8'
    return BeautifulSoup(response.text, features='lxml')


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        raise ParserFindTagException(
            TAG_NOT_FIND_ERROR.format(tag=tag, attrs=attrs)
        )
    return searched_tag
