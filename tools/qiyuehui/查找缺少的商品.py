import asyncio
import pathlib
import sys

import pandas as pd
from tqdm import tqdm

sys.path.append(
    str(pathlib.Path(__file__).parent.parent.parent)
)

from loguru import logger
from tqdm.auto import tqdm

from utils import until_success

logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)

from upload.qiyuehui.apis import search_goods


async def main():
    data = pd.read_excel('goods_list_with_ids.xlsx')
    data = data.dropna(subset=['ids'])

    ids = data['ids'].unique().astype(int)
    not_found = [i for i in range(ids.min(), ids.max()) if i not in ids]

    goods = pd.read_excel(
        r'C:\Users\SakuraPuare\Desktop\HongLiTong\data\qiyuehui\职友团上架明细表.xls', dtype={'商品代码': str})

    batch_size = 10
    for i in tqdm(range(0, len(not_found), batch_size)):
        batch = not_found[i:i + batch_size]
        tasks = []
        missing = []

        for id_ in batch:
            info = goods.loc[goods['序号'] == id_, '商品名称']
            if info.empty:
                continue
            name = info.values[0]
            tasks.append(
                until_success(search_goods, name.strip())
            )

        results = await asyncio.gather(*tasks)

        for id_, result in zip(batch, results):
            if not result:
                missing.append(id_)

        if missing:
            with open('missing_goods.txt', 'a') as f:
                for id_ in missing:
                    f.write(f"{id_}\n")


if __name__ == '__main__':
    asyncio.run(main())
