import pathlib
import sys

import pandas as pd

sys.path.append(
    str(pathlib.Path(__file__).parent.parent.parent)
)

import threading
from tqdm.auto import tqdm
from loguru import logger

logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)

from upload.qiyuehui.utils import fmt_desc, get_keyword_category, get_loc_by_goods_detail, get_price_category
from utils import find_closest_string, folder_start_with, glob_file_in_folder
from upload.qiyuehui.cos import upload_files
from upload.qiyuehui.apis import get_category, get_goods_detail, update

table_headers = [
    "序号",
    "一级分类",
    "二级分类",
    "品牌",
    "商品名称",
    "商品代码",
    "含税集采价",
    "含税代发价",
    "市场价",
    "职友团平台价",
    "最终利润率",
    "标准利润率",
    "利润完成比",
    "利润线",
    "满足价格",
    "等级满足比",
    "普通会员价格",
    "利润线",
    "满足价格",
    "等级满足比",
    "高级会员价",
    "利润线",
    "满足价格",
    "等级满足比",
    "VIP会员价",
    "利润线",
    "满足价格",
    "等级满足比",
    "至尊VIP会员价",
]
valid_headers = [
    "序号",
    "一级分类",
    "二级分类",
    "品牌",
    "商品名称",
    "商品代码",
    "含税代发价",
    "市场价",
    "职友团平台价",
    "普通会员价格",
    "高级会员价",
    "VIP会员价",
    "至尊VIP会员价",
]


def cache():
    goods = pd.read_excel('goods_list.xlsx', dtype={'goodsSn': str})
    data = pd.read_excel(
        r'C:\Users\SakuraPuare\Desktop\HongLiTong\data\qiyuehui\职友团上架明细表.xls', dtype={'商品代码': str})

    data.columns = table_headers
    data = data[valid_headers]
    data = data.dropna()

    # ignore addTime before 2025-01-7 13:25
    goods = goods[goods['addTime'] >= '2025-01-07 13:25:00']
    goods['loc'] = goods.apply(lambda row: get_loc_by_goods_detail(
        data, row['name'], row['goodsSn']), axis=1)
    goods['ids'] = goods['loc'].apply(lambda row: data.loc[row, '序号'])

    print(goods)

    # 保存到excel
    goods.to_excel('goods_list_with_ids.xlsx', index=False)


def need_to_reupload(detail):
    if detail['goods']['gallery'] is None:
        return True
    gallery = detail['goods']['gallery']
    if len(gallery) == 0 or len(gallery) != len(set(gallery)):
        return True

    import re
    desc = detail['goods']['desc']
    # find all image url in desc
    image_urls = re.findall(r'https?://[^ ]+', desc)
    if len(image_urls) == 0 or len(image_urls) != len(set(image_urls)):
        return True

    return False


# 创建一个文件写入锁
file_lock = threading.Lock()


async def process_single_item(line, category):
    """处理单个商品的函数"""
    if str(line['ids']) in black_list or str(line['ids']) in notfound:
        return False

    try:
        image_folder = [
            i for i in image_folder_list if folder_start_with(i, str(line['ids']))]
        if len(image_folder) == 0:
            raise AssertionError(f'{line["ids"]} 没有找到对应的图片文件夹')
        elif len(image_folder) > 1:
            image_folder = image_folder[find_closest_string(
                line['name'], [i.name for i in image_folder])]
        else:
            image_folder = image_folder[0]

        posts, details = glob_file_in_folder(image_folder)
        if len(posts) == 0 or len(details) == 0:
            raise AssertionError(f'{line["ids"]} 没有找到对应的图片文件夹')

        detail = await get_goods_detail(line['id'])
        good = goods.loc[line['ids']]
        cate = []
        cate.extend(get_price_category(category, float(good['含税代发价'])))
        cate.extend(get_price_category(category, float(good['市场价'])))
        cate.extend(get_keyword_category(category, good['品牌']))
        cate.extend(get_keyword_category(category, good['商品名称']))
        cate.extend(get_keyword_category(category, good['一级分类']))
        cate.extend(get_keyword_category(category, good['二级分类']))
        cate = list({cat['level']: cat for cat in cate}.values())
        l = sorted([i.get('level') for i in cate])
        fmt_cate = ','.join(l)

        if need_to_reupload(detail):
            detail['goods']['categoryId'] = fmt_cate
            posts_url = await upload_files(list(posts)[:10])
            details_url = await upload_files(details)

            desc_ = fmt_desc(details_url)
            detail['goods']['desc'] = desc_
            detail['goods']['gallery'] = posts_url

            await update(line['id'], detail)
        elif sorted(detail['goods']['categoryId'].split(',')) != l:
            detail['goods']['categoryId'] = fmt_cate
            await update(line['id'], detail)

        # 使用锁保护文件写入
        with file_lock:
            with open('black_list.txt', 'a') as f:
                f.write(f'{line["ids"]}\n')

        return True
    except AssertionError as e:
        tqdm.write(f'{line["id"]} 上传失败: {e}')
        with file_lock:
            with open('notfound.txt', 'a') as f:
                f.write(f'{line["ids"]}\n')
        return False
    except Exception as e:
        # retry 2 times more
        try:
            await process_single_item(line, category)
        except Exception as e:
            try:
                await process_single_item(line, category)
            except Exception as e:
                tqdm.write(f'{line["id"]} 上传失败: {e}')
                return False


async def main():
    category = await get_category()

    rows = list(data.iterrows())

    # 设置并发数
    semaphore = asyncio.Semaphore(8)  # 限制并发数为4，可以根据需要调整

    async def wrapped_process(line):
        async with semaphore:  # 使用信号量控制并发
            return await process_single_item(line, category)

    # 创建任务列表
    tasks = [wrapped_process(line) for _, line in rows]

    # 使用tqdm显示进度
    results = await tqdm.gather(*tasks, desc="处理商品", )

    # 统计结果
    success = sum(1 for r in results if r is True)
    print(f"处理完成: 成功 {success} 个, 失败 {len(results) - success} 个")


black_list = []

if __name__ == "__main__":
    # cache()

    import asyncio

    with open('black_list.txt', 'r') as f:
        black_list = f.read().splitlines()
        black_list = set(black_list)

    with open('notfound.txt', 'r') as f:
        notfound = f.read().splitlines()
        notfound = set(notfound)

    image_folder_list = list(pathlib.Path(
        r'C:\Users\SakuraPuare\Desktop\HongLiTong\data\qiyuehui\上传').iterdir())

    data = pd.read_excel('goods_list_with_ids.xlsx')
    goods = pd.read_excel(
        r'C:\Users\SakuraPuare\Desktop\HongLiTong\data\qiyuehui\职友团上架明细表.xls', dtype={'商品代码': str})
    goods.columns = table_headers
    goods = goods[valid_headers]
    goods['商品代码'].dropna()

    asyncio.run(main())
