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


def get_loc_by_goods_detail(table_data, good_name, good_code):
    """根据商品名称和代码在表格数据中查找对应的位置
    
    Args:
        table_data: DataFrame 包含商品数据的表格
        good_name: str 商品名称
        good_code: str 商品代码
        
    Returns:
        int|None: 找到的位置索引,未找到返回None
    """
    import pandas as pd
    if pd.isna(good_name):
        good_name = ''
    if pd.isna(good_code):
        good_code = ''

    import re
    good_name = re.sub(r'\s+', '', good_name)
    good_code = re.sub(r'\s+', '', good_code)

    # 先把表格里的空格和换行符去掉，不要修改原始数据
    table_data["商品代码"] = table_data["商品代码"].str.replace(r'\s+', '', regex=True)
    table_data["商品名称"] = table_data["商品名称"].str.replace(r'\s+', '', regex=True)

    # 筛选出非空数据
    code_not_na = table_data["商品代码"].notna() & (table_data["商品代码"] != '')
    name_not_na = table_data["商品名称"].notna() & (table_data["商品名称"] != '')

    def try_match(name, code):
        # both match
        code_match = code_not_na & (table_data["商品代码"].str.strip() == code)
        name_equal = name_not_na & (table_data["商品名称"].str.strip() == name)
        name_contain = name_not_na & (table_data["商品名称"].str.contains(name, regex=False))
        equal_match = code_match & name_equal
        contain_match = code_match & name_contain

        # 如果匹配结果大于1，或匹配结果为0，则尝试匹配code或name
        if equal_match.sum() == 1:
            return table_data[equal_match].index[0]

        if contain_match.sum() == 1:
            return table_data[contain_match].index[0]

        if equal_match.sum() == 1:
            return table_data[equal_match].index[0]
        if code_match.sum() == 1:
            return table_data[code_match].index[0]
        if name_contain.sum() == 1:
            return table_data[name_contain].index[0]
        return None

    result = try_match(good_name, good_code)
    if result is not None:
        return result

    # 定义替换表
    replace_map = {
        '＆': '&',
        '\xa0': '',
    }

    for k, v in replace_map.items():
        good_name = good_name.replace(k, v)
        good_code = good_code.replace(k, v)

    result = try_match(good_name, good_code)
    if result is not None:
        return result
    return None


def get_price_by_goods_detail(table_data, good_name, good_code):
    loc = get_loc_by_goods_detail(table_data, good_name, good_code)
    if loc is None:
        return None
    return table_data.loc[loc][[
        "普通会员价格",
        "高级会员价",
        "VIP会员价",
        "至尊VIP会员价",
    ]]
