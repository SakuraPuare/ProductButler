from utils import find_closest_string

from .typehints import Category


def parse_html_options(html):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'lxml')
    options = soup.find_all('dd')
    result = {}
    for option in options:
        value = option.get('lay-value')
        if not value:
            continue

        text = option.text.strip()
        result[text] = {
            'level': value,
            'children': []
        }
    return result


def get_category_level_1(category: 'Category', string: str):
    items = list(category.keys())
    idx = find_closest_string(string, items)
    return items[idx], category[items[idx]].get("level")


def get_category_level_2(category: 'Category', level_1: str, string: str):
    items = list(category[level_1]["children"].keys())
    idx = find_closest_string(string, items)
    return items[idx], category[level_1]["children"][items[idx]].get("level")
