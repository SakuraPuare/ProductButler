import sys
import pathlib
import loguru

sys.path.append(
    str(pathlib.Path(__file__).parent.parent.parent)
)

import pandas as pd
import numpy


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


data = pd.read_excel(r'C:\Users\SakuraPuare\Desktop\HongLiTong\data\2025年1月3日\职友团上架明细表.xls', header=0, dtype={'商品代码': str})
data.columns = table_headers
data = data[valid_headers]

def get_price_by_goods_detail(good_name, good_code):
    # find the index of the goods in data
    # Check for both name and code matches
    code = data["商品代码"].str.contains(good_code, regex=False).map(bool)
    name = data["商品名称"].str.contains(good_name, regex=False).map(bool)
    
    # both matches
    matched = data[code & name]
    if matched.empty or len(matched) > 1:
        matched = data[code]
        if matched.empty or len(matched) > 1:
            matched = data[name]
            if matched.empty or len(matched) > 1:
                return None
    return data.loc[matched.index[0]][[
        "普通会员价格",
        "高级会员价",
        "VIP会员价",
        "至尊VIP会员价",
    ]]

async def main():
    # 获取所有未录入会员价的商品
    from upload.qiyuehui.apis import get_vip_goods_list, get_goods_detail, set_vip_price

    flag = True
    page = 26
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
                price_ = get_price_by_goods_detail(name, bar_code)

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


