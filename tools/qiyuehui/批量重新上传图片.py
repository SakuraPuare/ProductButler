import pathlib
import sys

import pandas as pd

sys.path.append(
    str(pathlib.Path(__file__).parent.parent.parent)
)

import threading
import concurrent.futures
from tqdm.auto import tqdm
from loguru import logger
import loguru

logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)

from upload.qiyuehui.utils import fmt_desc, get_keyword_category, get_price_category
from utils import find_closest_string, get_folder_actual_name, glob_file_in_folder
from upload.qiyuehui.cos import upload_files
from upload.qiyuehui.apis import get_category, get_goods_detail, update
from upload.qiyuehui.headers import table_headers, valid_headers


def is_need_to_reupload(detail):
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


# 创建一个文件写入锁
file_lock = threading.Lock()
image_folder_list = list(pathlib.Path(r'C:\Users\SakuraPuare\Desktop\上传').iterdir())
folder_name_list = [get_folder_actual_name(i) for i in image_folder_list]


def find_image_folder(line):
    """查找商品对应的图片文件夹"""
    try:
        image_folder = [i for i in folder_name_list if i.startswith(str(line['ids']))]

        if len(image_folder) == 0:
            raise AssertionError(f'{line["ids"]} 没有找到对应的图片文件夹')
        elif len(image_folder) > 1:
            image_folder = image_folder[find_closest_string(line['name'], [i for i in image_folder])]
        else:
            image_folder = image_folder[0]

        return image_folder_list[folder_name_list.index(image_folder)]
    except Exception as e:
        with file_lock:
            with open('notfound.txt', 'a') as f:
                f.write(f'{line["ids"]}\n')


async def process_single_item(line, category, image_folder):
    """处理单个商品的函数"""

    # if str(line['ids']) in black_list or str(line['ids']) in notfound:
    #     return False

    try:
        detail = await get_goods_detail(line['id'])
        good = goods.loc[line['ids']]
        cate = []
        cate.extend(get_price_category(category, float(good['含税代发价'])))
        cate.extend(get_price_category(category, float(good['市场价'])))
        cate.extend(get_keyword_category(category, f"{good['品牌']} {good['商品名称']} {good['一级分类']} {good['二级分类']} "))
        cate = list({cat['level']: cat for cat in cate}.values())
        l = [i.get('level') for i in cate]
        n = [i.get('name') for i in cate]

        fmt_cate = ','.join(l)
        fmt_name = ','.join(n)

        changed = True

        # if is_need_to_reupload(detail):
        #     if image_folder is None:
        #         raise TypeError(f'{line["ids"]} 没有找到对应的图片文件夹')
        #     posts, details = glob_file_in_folder(image_folder)
        #     if len(posts) == 0 or len(details) == 0:
        #         raise AssertionError(f'{line["ids"]} 没有找到对应的图片文件夹')

        #     detail['goods']['categoryId'] = fmt_cate
        #     detail['goods']['categoryName'] = fmt_name
            
        #     posts_url = await upload_files(list(posts)[:10])
        #     details_url = await upload_files(details)

        #     desc_ = fmt_desc(details_url)
        #     detail['goods']['desc'] = desc_
        #     detail['goods']['gallery'] = posts_url
        #     logger.info(f'{line["ids"]} 图片更新成功')
        if sorted(detail['goods']['categoryId'].split(',')) != sorted(l):
            detail['goods']['categoryId'] = fmt_cate
            detail['goods']['categoryName'] = fmt_name
            logger.info(f'{line["ids"]} 分类更新成功')
            if detail['goods']['goodsSn'] == 'nan':
                detail['goods']['goodsSn'] = ''
                logger.info(f'{line["ids"]} 商品编码更新成功')
        else:
            changed = False

        if changed:
            # 单独处理update的重试逻辑
            for retry in range(3):  # 最多重试2次
                try:
                    await update(detail)
                    break
                except Exception as e:
                    if retry == 2:  # 最后一次重试也失败
                        raise e
                    logger.warning(f'更新失败,第{retry + 1}次重试: {e}')
                    continue

        # 使用锁保护文件写入
        with file_lock:
            with open('black_list.txt', 'a') as f:
                f.write(f'{line["ids"]}\n')

        return True

    except (AssertionError, TypeError) as e:
        logger.error(f'{line["id"]} 上传失败: {e}')
        with file_lock:
            with open('notfound.txt', 'a') as f:
                f.write(f'{line["ids"]}\n')
        return False
    except Exception as e:
        logger.error(f'{line["id"]} 上传失败: {e}')
        with file_lock:
            with open('error.txt', 'a') as f:
                f.write(f'{detail}\n')
        tqdm.write(f'{line["id"]} 上传失败: {e}')
        return False


async def main():
    category = await get_category()
    rows = list(data.iterrows())

    # 先用多线程处理所有图片文件夹查找
    image_data = []
    for line in rows:
        image_folder = find_image_folder(line[1])
        image_data.append((line[1], image_folder))
    # with concurrent.futures.ProcessPoolExecutor(max_workers=16) as executor:
    #     futures = [executor.submit(find_image_folder, line[1]) for line in rows]
    #     with tqdm(total=len(futures), desc="查找图片") as pbar:
    #         for f, row in zip(concurrent.futures.as_completed(futures), rows):
    #             try:
    #                 image_folder = f.result()
    #                 image_data.append((row[1], image_folder))
    #             except Exception as e:
    #                 logger.error(f"查找图片失败: {e}")
    #             finally:
    #                 pbar.update(1)

    # 使用批量方式并行处理商品更新
    results = []
    for i in tqdm(range(0, len(image_data), 10), desc="处理商品"):
        batch = image_data[i:i + 10]
        batch_results = await asyncio.gather(*[
            process_single_item(line, category, image_folder)
            for line, image_folder in batch
        ])
        results.extend(batch_results)

    # 统计结果
    success = sum(1 for r in results if r is True)
    print(f"处理完成: 成功 {success} 个, 失败 {len(results) - success} 个")


black_list = []

if __name__ == "__main__":
    # cache()
    data = pd.read_excel('goods_list_with_ids.xlsx')

    import asyncio

    # with open('black_list.txt', 'r') as f:
    #     black_list = [i for i in f.read().splitlines() if i]
    #     black_list = set(black_list)

    # with open('notfound.txt', 'r') as f:
    #     notfound = [i for i in f.read().splitlines() if i]
    #     notfound = set(notfound)

    with open('need_to_reupload.txt', 'r') as f:
        need_to_reupload = [int(i) for i in f.read().splitlines() if i]
        need_to_reupload = set(need_to_reupload)
    
    # filter ids in black_list
    data = data[data['ids'].isin(need_to_reupload)]
    # data = data[~data['ids'].isin(map(int, black_list))]
    # data = data[~data['ids'].isin(map(int, notfound))]

    # drop sharePic column
    data.drop(columns=['sharePic'], inplace=True)

    # drop ids nan
    data.dropna(subset=['ids'], inplace=True)
    data['ids'] = data['ids'].astype(int)


    goods = pd.read_excel(
        r'C:\Users\SakuraPuare\Desktop\HongLiTong\data\qiyuehui\职友团上架明细表.xls', dtype={'商品代码': str})
    goods.columns = table_headers
    goods = goods[valid_headers]
    asyncio.run(main())
