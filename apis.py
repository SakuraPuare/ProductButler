import mimetypes
import pathlib
import time

import aiofiles
from bs4 import BeautifulSoup

from https import get, post, reload_cookies
from typehint import Category
from utils import load_cookies, parse_html_options, save_cookies

default_data = {
    "buyNotice": "<p>购买须知</p>",
    "detail": "",
    "specPic2": "",
    "specPic3": "",
    "specPic4": "",
    "specPic5": "",
    "specPic6": "",
    "videoId": "",
    "area": "310100,320000,330000,340000,360000,370000,110100,120100,130000,140000,440000,450000,460000,350000,530000,410000,420000,430000,230000,220000,210000,610000,620000,630000,500100,510000,520000,",
    "expressCompany": "顺丰快递,京东快递,邮政EMS,圆通快递,中通快递,申通快递,百世快递,韵达快递,德邦物流",
    "select": "顺丰快递,京东快递,邮政EMS,中通快递,圆通快递,申通快递,百世快递,韵达快递,德邦物流",
    "brandAbstract": "",
    "name2": "",
    "marketPrice2": "",
    "bidPrice2": "",
    "weight2": "",
    "name3": "",
    "marketPrice3": "",
    "bidPrice3": "",
    "weight3": "",
    "name4": "",
    "marketPrice4": "",
    "bidPrice4": "",
    "weight4": "",
    "name5": "",
    "marketPrice5": "",
    "bidPrice5": "",
    "weight5": "",
    'count': '99999',
    'salesReturn': '是',
}


async def add_goods(
        poster_url: list[str],
        detail_url: list[str],
        brand: str,
        goods_name: str,
        market_price: str,
        bid_price: str,
        weight: str,
        level_1: str,
        level_2: str,
        bar_code: str,
) -> dict:
    data = {
        "poster": ",".join(poster_url) + ",",
        "detailPic": ",".join(detail_url) + ",",
        "brand": brand,
        "ebkGoodsName": goods_name,
        "level1": level_1,
        "level2": level_2,
        "name1": goods_name,
        "marketPrice1": market_price,
        "bidPrice1": bid_price,
        "weight1": weight,
        "specPic1": poster_url[0] + ",",
        "barCode": bar_code,
    }
    data.update(default_data)

    response = await post("http://hlt-admin.honglitong.cn/goods/add/form", data=data)

    return response.json()


async def upload_file(types: str, path: pathlib.Path) -> str:
    # byte = path.read_bytes()
    mime_type, _ = mimetypes.guess_type(path)
    async with aiofiles.open(path, "rb") as f:
        byte = await f.read()
    files = {
        # 'file': ('驱蚊酯驱蚊液65ml_18.jpg', '', 'image/jpeg'),
        "file": (path.name, byte, mime_type),
        "service": (None, f"goods/gys/{types}"),
    }

    response = await post(
        "http://hlt-admin.honglitong.cn/util/open/layui/UploadImg",
        data={},
        headers={
            "Content-Type": "multipart/form-data; boundary=----WebKitFormBoundary"
        },
        files=files,
    )

    return "https://hlt-cdn.cyscience.cn/" + response.json().get("url")


async def get_captcha_image():
    import httpx
    response = httpx.get(
        "http://hlt-admin.honglitong.cn/login/verify.html", params={"t": time.time()})
    with open("verify.jpg", "wb") as f:
        f.write(response.content)
    save_cookies(response.cookies)


async def login(account: str, password: str, captcha: str):
    import httpx
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Referer': 'http://hlt-admin.honglitong.cn/login',
    }
    cookies = load_cookies()

    data = {
        'username': account,
        'pwd': password,
        'pcode': captcha,
    }

    response = httpx.post('http://hlt-admin.honglitong.cn/login/ajax/auth',
                          cookies=cookies, headers=headers, data=data, verify=False)
    cookies.update(response.cookies)

    if response.text:
        response = response.json()
        assert response.get('success'), response.get('msg')

    response = httpx.get(
        'http://hlt-admin.honglitong.cn/login/doLogin', cookies=cookies, headers=headers)
    cookies.update(response.cookies)
    save_cookies(cookies)
    reload_cookies()


async def test_login():
    await get("http://hlt-admin.honglitong.cn/goods/add/page")


async def get_category() -> Category:
    response = await get("http://hlt-admin.honglitong.cn/goods/add/page")

    category_list = {}
    level_1_soup = BeautifulSoup(response.text, 'html.parser')
    level_1_options = level_1_soup.find_all('option')
    for option_1 in level_1_options:
        value_l1 = option_1.get('value')
        if not value_l1:
            continue

        child = {}
        params = {
            "level": "2",
            "pId": value_l1,
        }
        response = await get(
            "http://hlt-admin.honglitong.cn/goods/ajax/load-category",
            params=params,
        )

        level_2_soup = BeautifulSoup(response.text, 'lxml')
        level_2_options = level_2_soup.find_all('option')
        for option_l2 in level_2_options:
            value_l2 = option_l2.get('value')
            if not value_l2:
                continue

            child[option_l2.text.strip()] = {
                'level': value_l2,
                'children': {}
            }

        category_list[option_1.text.strip()] = {
            'level': value_l1,
            'children': child
        }

    with open("category.json", "w", encoding='u8') as f:
        import json
        json.dump(category_list, f, ensure_ascii=False, indent=4)

    return category_list


if __name__ == "__main__":
    import asyncio

    asyncio.run(get_captcha_image())

    # import json

    # cat = asyncio.run(get_category())
    # with open("category.json", "w", encoding='u8') as f:
    #     json.dump(cat, f, ensure_ascii=False, indent=4)

    # resp = asyncio.run(upload_file('poster', pathlib.Path('企悦汇选品1038-1197 (2)/未命名文件夹 2/1038.儿童内衣专用洗衣液300ml/主图/81688faeabc9cbd0a1d92ddd3df1887.jpg')))
    # pass
