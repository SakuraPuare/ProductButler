import pathlib
import sys

import pandas as pd

sys.path.append(
    str(pathlib.Path(__file__).parent.parent.parent)
)

from upload.qiyuehui.headers import table_headers, valid_headers


def get_loc_by_goods_detail(data, code_not_na, name_not_na, good_name, good_code):
    """根据商品名称和代码在表格数据中查找对应的位置

    Args:
        table_data: DataFrame 包含商品数据的表格
        good_name: str 商品名称
        good_code: str 商品代码

    Returns:
        int|None: 找到的位置索引,未找到返回None
    """

    if pd.isna(good_name):
        good_name = ''
    if pd.isna(good_code):
        good_code = ''

    import re
    good_name = re.sub(r'\s+', '', good_name)
    good_code = re.sub(r'\s+', '', good_code)

    def try_match(name, code):
        # both match
        code_match = code_not_na & (data["商品代码"].str.strip() == code)
        name_equal = name_not_na & (data["商品名称"].str.strip() == name)
        name_contain = name_not_na & (
            data["商品名称"].str.contains(name, regex=False))
        equal_match = code_match & name_equal
        contain_match = code_match & name_contain

        # 如果匹配结果大于1，或匹配结果为0，则尝试匹配code或name
        if equal_match.sum() == 1:
            return data[equal_match].index[0]

        if contain_match.sum() == 1:
            return data[contain_match].index[0]

        if equal_match.sum() == 1:
            return data[equal_match].index[0]
        if code_match.sum() > 0:
            return data[code_match].index[0]
        if name_contain.sum() > 0:
            return data[name_contain].index[0]
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


from tqdm.auto import tqdm


def main():
    goods = pd.read_excel('goods_list.xlsx', dtype={'goodsSn': str})
    data = pd.read_excel(
        r'C:\Users\SakuraPuare\Desktop\HongLiTong\data\qiyuehui\职友团上架明细表.xls', dtype={'商品代码': str})

    data.columns = table_headers
    data = data[valid_headers]

    import re
    empty_space_re = re.compile(r'\s+', re.IGNORECASE)

    # set code as str
    data["商品代码"] = data["商品代码"].astype(str)
    data["商品名称"] = data["商品名称"].astype(str)

    data["商品代码"] = data["商品代码"].str.replace(empty_space_re, '', regex=True)
    data["商品名称"] = data["商品名称"].str.replace(empty_space_re, '', regex=True)

    code_not_na = data["商品代码"].notna() & (data["商品代码"] != '')
    name_not_na = data["商品名称"].notna() & (data["商品名称"] != '')

    from functools import partial

    get_loc_by_goods_detail_ = partial(
        get_loc_by_goods_detail, data, code_not_na, name_not_na)

    tqdm.pandas()

    goods['loc'] = goods.progress_apply(lambda row: get_loc_by_goods_detail_(
        row['name'], row['goodsSn']), axis=1)
    # replace nan with empty string
    goods.fillna('', inplace=True)

    goods['ids'] = goods['loc'].apply(
        lambda row: data.loc[row, '序号'] if row != '' else '')

    print(goods)

    # 保存到excel
    goods.to_excel('goods_list_with_ids.xlsx', index=False)


if __name__ == '__main__':
    main()
