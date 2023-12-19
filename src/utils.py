from bs4 import BeautifulSoup
from requests import RequestException

from constants import REQUEST_ERROR_MESSAGE
from exceptions import ParserFindTagException

TAG_NOT_FIND_ERROR = 'Не найден тег {tag} {attrs}'


def get_response(session, url, encoding="utf-8"):
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except RequestException as e:
        raise RequestException(REQUEST_ERROR_MESSAGE.format(link=url, error=e))


def get_soup(session, url, features='lxml'):
    response = get_response(session, url)
    return BeautifulSoup(response.text, features=features)


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        raise ParserFindTagException(
            TAG_NOT_FIND_ERROR.format(tag=tag, attrs=attrs)
        )
    return searched_tag
