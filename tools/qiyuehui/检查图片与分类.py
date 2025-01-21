import pathlib
import sys
import asyncio

import pandas as pd

sys.path.append(
    str(pathlib.Path(__file__).parent.parent.parent)
)

import threading
import concurrent.futures
from tqdm.auto import tqdm
from loguru import logger
import os


logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)

from upload.qiyuehui.utils import fmt_desc, get_keyword_category, get_price_category
from utils import find_closest_string, get_folder_actual_name, glob_file_in_folder
from upload.qiyuehui.cos import upload_files
from upload.qiyuehui.apis import get_category, get_goods_detail, update
from upload.qiyuehui.headers import table_headers, valid_headers


def image_need_to_reupload(detail):
    if detail['goods']['gallery'] is None:
        return True
    gallery = detail['goods']['gallery']
    if len(gallery) == 0 or len(gallery) != len(set(gallery)):
        logger.info(f'{detail["goods"]["name"]} 图片数量不一致 {len(gallery)} != {len(set(gallery))}')
        return True

    import re
    desc = detail['goods']['desc']
    # find all image url in desc
    image_urls = re.findall(r'https?://[^ ]+"', desc)
    if len(image_urls) == 0 or len(image_urls) != len(set(image_urls)):
        logger.info(f'{detail["goods"]["name"]} 图片数量不一致 {len(image_urls)} != {len(set(image_urls))}')
        return True

    return False

def category_need_to_reupload(detail):
    if detail['goods']['categoryId'] is None:
        return True
    
    good = goods.loc[data[detail['goods']['id'] == data['id']]['loc']]

    cate = []
    cate.extend(get_price_category(category, float(good['含税代发价'].iloc[0])))
    cate.extend(get_price_category(category, float(good['市场价'].iloc[0])))
    cate.extend(get_keyword_category(category, f"{good['品牌'].iloc[0]} {good['商品名称'].iloc[0]} {good['一级分类'].iloc[0]} {good['二级分类'].iloc[0]} "))
    cate = list({cat['level']: cat for cat in cate}.values())
    l = [i.get('level') for i in cate]
    n = [i.get('name') for i in cate]

    if sorted(detail['goods']['categoryId'].split(',')) != sorted(l):
        return True

    if sorted(detail['goods']['categoryName'].split(',')) != sorted(n):
        return True
    
    return False

async def process_single_item(line, category):
    """处理单个商品的函数"""

    detail = await get_goods_detail(line['id'])

    if category_need_to_reupload(detail):
        with open('need_to_reupload.txt', 'a') as f:
            f.write(f'{line["ids"]}\n')
    else:
        with open('not_need_to_reupload.txt', 'a') as f:
            f.write(f'{line["ids"]}\n')


async def main():
    global category
    category = await get_category()
    rows = list(data.iterrows())
    
    for line in tqdm(range(1, len(rows), 10)):
        batch = rows[line:line + 10]
        await asyncio.gather(*[
            process_single_item(line, category)
            for idx, line in batch
        ])


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


    goods = pd.read_excel(
        r'C:\Users\SakuraPuare\Desktop\HongLiTong\data\qiyuehui\职友团上架明细表.xls', dtype={'商品代码': str})
    goods.columns = table_headers
    goods = goods[valid_headers]
    asyncio.run(main())
