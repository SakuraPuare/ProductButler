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

    if pd.isna(good_code):
        good_code = ''
    if pd.isna(good_name):
        good_name = ''

    import re


    # 删除所有空格和换行符
    empty_replace = re.compile(r'\s+')
    good_name = empty_replace.sub('', good_name)
    good_code = empty_replace.sub('', good_code)

    # 定义替换表
    replace_map = {
        '＆': '&',
        '\xa0': ' ',
    }

    def replace_space(name):
        return name.str.replace(' ', '', regex=False).str.replace('\n', '', regex=False)

    def try_match(name, code):
        # Filter out NA values first
        valid_codes = table_data["商品代码"].notna()
        valid_names = table_data["商品名称"].notna()
        
        # Match on non-NA values
        code_match = replace_space(table_data["商品代码"]).str.contains(code, regex=False).map(bool) & valid_codes
        name_match = replace_space(table_data["商品名称"]).str.contains(name, regex=False).map(bool) & valid_names

        # both matches
        matched = table_data[code_match & name_match]
        if matched.empty:
            matched = valid_codes[code_match]
            if matched.empty or len(matched) > 1:
                matched = valid_names[name_match] 
                if matched.empty:
                    return None
                elif len(matched) > 1:
                    # Check for exact name matches ignoring whitespace
                    exact_matches = matched[replace_space(matched["商品名称"]) == name]
                    if not exact_matches.empty:
                        return exact_matches.index[0]
                    return None
        elif len(matched) > 1:
            # Check for exact matches ignoring whitespace
            exact_matches = matched[replace_space(matched["商品名称"]) == name]
            if not exact_matches.empty:
                return exact_matches.index[0]

            # Try code match
            matched = table_data[code_match]
            if matched.empty or len(matched) > 1:
                # Try name match
                matched = table_data[name_match]
                if matched.empty:
                    return None
                elif len(matched) > 1:
                    # Check for exact name matches ignoring whitespace
                    exact_matches = matched[replace_space(matched["商品名称"]) == name]
                    if not exact_matches.empty:
                        return exact_matches.index[0]
                    return None

        return matched.index[0]

    # 第一次尝试匹配
    result = try_match(good_name, good_code)
    if result is not None:
        return result

    import loguru
    loguru.logger.warning(f"[{good_name}] 第一次匹配失败，尝试替换一些字符")

    for char, replacement in replace_map.items():
        if good_name.count(char) == 0:
            continue

        test_name = good_name.replace(char, replacement)

        result = try_match(test_name, good_code)
        if result is not None:
            return result
        
        loguru.logger.warning(f"[{good_name}] 替换字符对 '{char}'/'{replacement}' 后匹配失败")

    # 逐个检查替换表中的字符对
    for char, replacement in replace_map.items():
        if good_name.count(char) == 0:
            continue

        # 对输入的good_name删除左右两边对应的字符
        test_name = good_name.replace(char, "").replace(replacement, "")

        # 创建临时的name_match条件，删除右边字符
        name_match = table_data["商品名称"] \
            .str.replace(replacement, "", regex=False) \
            .str.contains(test_name, regex=False)
        matched = table_data[name_match]

        if not matched.empty:
            if len(matched) == 1:
                loguru.logger.warning(
                    f"[{good_name}] 删除字符对 '{char}'/'{replacement}' 后匹配 {matched.iloc[0]['商品名称']} 成功，请检查是否正确")
                return matched.index[0]
            else:
                # 检查精确匹配
                exact_matches = matched[matched["商品名称"].str.replace(replacement, "",
                                                                   regex=False).str.strip() == test_name.strip()]
                if not exact_matches.empty:
                    loguru.logger.warning(
                        f"[{good_name}] 删除字符对 '{char}'/'{replacement}' 后精确匹配 {exact_matches.iloc[0]['商品名称']} 成功，请检查是否正确")
                    return exact_matches.index[0]

    loguru.logger.warning(f"[{good_name}] 所有字符对替换匹配失败")
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
