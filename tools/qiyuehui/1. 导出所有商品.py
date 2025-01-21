import pathlib
import sys

import pandas as pd

sys.path.append(
    str(pathlib.Path(__file__).parent.parent.parent)
)

from upload.qiyuehui.apis import get_goods_list


async def main():
    goods_list = []

    flag = True
    page = 1
    size = 2000
    while flag:
        resp = await get_goods_list(page, size)
        goods_list.extend(resp)
        if len(resp) < size:
            flag = False
        page += 1

    df = pd.DataFrame(goods_list)
    df.to_excel('goods_list.xlsx', index=False)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
