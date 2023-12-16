# Проект парсинга pep
## Технологии проекта
Python, BeautifulSoup4, Prettytable

## Команды развертывания
- Клонировать репозиторий  
`git clone https://github.com/Andrey-66/bs4_parser_pep.git`  
`git clone git@github.com:Andrey-66/bs4_parser_pep.git`
- Cоздать и активировать виртуальное окружение  
`python3 -m venv env && source env/bin/activate`
- Установить зависимости
`pip install -r requirements.txt`
- Команды запуска  
    - Справка  
    `python main.py pep -h`
    - Получить нововведения  
    `python main.py whats-new`
    - Получить информацию о pep в виде файла
    `python main.py pep -o file`
    - Получить последние версии в виде консольной таблицы
    `python main.py latest-versions -o pretty`