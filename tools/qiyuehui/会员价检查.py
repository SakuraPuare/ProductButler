import pathlib
import sys

import loguru

sys.path.append(
    str(pathlib.Path(__file__).parent.parent.parent)
)

import pandas as pd
import numpy

from upload.qiyuehui.headers import table_headers, valid_headers

data = pd.read_excel(r'C:\Users\SakuraPuare\Desktop\HongLiTong\data\qiyuehui\职友团上架明细表.xls', header=0,
                     dtype={'商品代码': str})
data.columns = table_headers
data = data[valid_headers]


async def main():
    # 获取所有未录入会员价的商品
    from upload.qiyuehui.apis import get_vip_goods_list, get_goods_detail, set_vip_price
    from upload.qiyuehui.utils import get_price_by_goods_detail

    flag = True
    page = 0
    size = 100
    while flag:
        vip_goods_list = await get_vip_goods_list(page=page, size=size, status=True)
        for i in vip_goods_list:
            detail = await get_goods_detail(i.get('Id'))
            price = [detail.get('products', [])[0].get(
                f'vip{j}Price', 0) for j in range(1, 4 + 1)]

            name = detail.get('goods', {}).get('name', '')

            for j in detail.get('products', []):
                ids = j.get('id', '')
                bar_code = j.get('specificationCode', '')
                price_ = get_price_by_goods_detail(data, name, bar_code)

                if price_ is None:
                    continue
                # compare price and price_
                is_equal = numpy.isclose(price, price_.tolist(), atol=15e-3)
                if is_equal.all():
                    continue

                # save the price to the goods
                await set_vip_price(ids, *price_)
                loguru.logger.info(f'{name} {ids}: \n{price} \n{price_}')

        page += 1

        if len(vip_goods_list) < size:
            flag = False

    pass


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
