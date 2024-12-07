from typehints import Category
from utils import find_closest_string


def fmt_desc(image_list: list[str]):
    return ''.join([f'<p><img src="{image}" style=""/></p>' for image in image_list])


def get_price_category(category: 'Category', price: float) -> list[dict]:
    import re
    keys = list(category.keys())
    prices = category[
        keys[find_closest_string('价格区间', keys)]
    ].get('children', {})

    ret = []

    for k, v in prices.items():
        # match all number
        numbers = re.findall(r'\d+', k)
        if len(numbers) == 2:
            low, high = map(int, numbers)
            if low <= price <= high:
                ret.append(v)
        elif len(numbers) == 1:
            numbers = int(numbers[0])
            if '上' in k and price >= numbers:
                ret.append(v)
            elif '下' in k and price <= numbers:
                ret.append(v)

    return ret


def get_keyword_category(category: 'Category', keyword: str) -> list[dict]:
    ret = []
    for key in category.keys():
        children = category[key].get('children', {})
        for k, v in children.items():
            if k in keyword:
                ret.append(v)
    return ret


def get_category(category: 'Category', category_name: str) -> dict:
    secondary = [
        category[key] for key in category.keys()
        if category_name in key
    ]
    return secondary[find_closest_string(category_name, secondary)]
