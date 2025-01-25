import asyncio
import os
import pathlib
import sys
import threading

import pandas as pd
from loguru import logger
from tqdm.auto import tqdm
from tqdm.contrib.concurrent import process_map

sys.path.append(
    str(pathlib.Path(__file__).parent.parent.parent)
)

from upload.qiyuehui.utils import get_keyword_category, get_price_category
from upload.qiyuehui.headers import table_headers, valid_headers
from upload.qiyuehui.apis import get_category

logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)


def image_need_to_reupload(detail):
    if detail['goods']['gallery'] is None:
        return True
    gallery = detail['goods']['gallery']
    if len(gallery) == 0 or len(gallery) != len(set(gallery)):
        logger.info(f'{detail["goods"]["name"]} 图片数量不一致 {
        len(gallery)} != {len(set(gallery))}')
        return True

    import re
    desc = detail['goods']['desc']
    # find all image url in desc
    image_urls = re.findall(r'https?://[^ ]+"', desc)
    if len(image_urls) == 0 or len(image_urls) != len(set(image_urls)):
        logger.info(f'{detail["goods"]["name"]} 图片数量不一致 {
        len(image_urls)} != {len(set(image_urls))}')
        return True

    return False


def category_need_to_reupload(detail):
    if detail['goods']['categoryId'] is None:
        return True

    good = goods.loc[data[detail['goods']['id'] == data['id']]['loc']]

    cate = []
    cate.extend(get_price_category(category, float(good['含税代发价'].iloc[0])))
    cate.extend(get_price_category(category, float(good['市场价'].iloc[0])))
    cate.extend(get_keyword_category(category, f"{good['品牌'].iloc[0]} {
    good['商品名称'].iloc[0]} {good['一级分类'].iloc[0]} {good['二级分类'].iloc[0]} "))
    cate = list({cat['level']: cat for cat in cate}.values())
    l = [i.get('level') for i in cate]
    n = [i.get('name') for i in cate]

    if sorted(detail['goods']['categoryId'].split(',')) != sorted(l):
        return True

    if sorted(detail['goods']['categoryName'].split(',')) != sorted(n):
        return True

    return False


def category_need_to_reupload_local(category, data, goods, line):
    good = goods.loc[data[line['id'] == data['id']]['loc']]

    cate = []
    cate.extend(get_price_category(category, float(good['含税代发价'].iloc[0])))
    cate.extend(get_price_category(category, float(good['市场价'].iloc[0])))
    cate.extend(get_keyword_category(category, f"{good['品牌'].iloc[0]} {
    good['商品名称'].iloc[0]} {good['一级分类'].iloc[0]} {good['二级分类'].iloc[0]} "))
    cate = list({cat['level']: cat for cat in cate}.values())
    l = [i.get('level') for i in cate]
    n = [i.get('name') for i in cate]

    if sorted([i for i in line['categoryId'].split(',') if i]) != sorted(l):
        return True

    if sorted([i for i in line['categoryName'].split(',') if i]) != sorted(n):
        return True

    return False


async def process_single_item(line, category):
    """处理单个商品的函数"""

    # # retry 3 times
    # for i in range(3):
    #     try:
    #         detail = await get_goods_detail(line['id'])
    #         break
    #     except Exception as e:
    #         logger.error(f'{line["ids"]} 获取商品详情失败: {e}')

    if category_need_to_reupload_local(line):
        with open('need_to_reupload.txt', 'a') as f:
            f.write(f'{line["ids"]}\n')
    else:
        with open('not_need_to_reupload.txt', 'a') as f:
            f.write(f'{line["ids"]}\n')


lock_a = threading.Lock()
lock_b = threading.Lock()


def process_single_item_local(category, data, goods, line):
    if category_need_to_reupload_local(category, data, goods, line):
        with lock_a:
            with open('need_to_reupload.txt', 'a') as f:
                f.write(f'{line["ids"]}\n')
    else:
        with lock_b:
            with open('not_need_to_reupload.txt', 'a') as f:
                f.write(f'{line["ids"]}\n')


async def main():
    global category
    category = await get_category()
    idx, rows = list(zip(*data.iterrows()))

    from functools import partial
    func = partial(process_single_item_local, category, data, goods)
    process_map(
        func, rows, chunksize=10, max_workers=32
    )

    # for i in rows:
    #     partial(process_single_item_local,category, data, goods)

    # for line in tqdm(range(1, len(rows), 10)):
    #     batch = rows[line:line + 10]
    #     await asyncio.gather(*[
    #         process_single_item(line, category)
    #         for idx, line in batch
    #     ])


category = {}

if __name__ == "__main__":
    data = pd.read_excel('goods_list_with_ids.xlsx')
    # drop sharePic column
    data.drop(columns=['sharePic'], inplace=True)

    # drop ids nan
    data.dropna(subset=['ids'], inplace=True)
    data['ids'] = data['ids'].astype(int)

    if os.path.exists('not_need_to_reupload.txt'):
        with open('not_need_to_reupload.txt', 'r') as f:
            not_need_to_reupload = [int(i) for i in f.read().splitlines() if i]
            not_need_to_reupload = set(not_need_to_reupload)

            data = data[~data['ids'].isin(not_need_to_reupload)]

    # if os.path.exists('need_to_reupload.txt'):
    #     with open('need_to_reupload.txt', 'r') as f:
    #         need_to_reupload = [int(i) for i in f.read().splitlines() if i]
    #         need_to_reupload = set(need_to_reupload)

    #         data = data[~data['ids'].isin(need_to_reupload)]

    goods = pd.read_excel(
        r'C:\Users\SakuraPuare\Desktop\HongLiTong\data\qiyuehui\职友团上架明细表.xls', dtype={'商品代码': str})
    goods.columns = table_headers
    goods = goods[valid_headers]
    asyncio.run(main())
