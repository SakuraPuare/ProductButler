import aiofiles
import magic
import pathlib

from https import get, post
from utils import parse_html_options

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
    }
    data.update(default_data)

    response = await post("http://hlt-admin.honglitong.cn/goods/add/form", data=data)

    return response.json()


async def upload_file(types: str, path: pathlib.Path) -> str:
    # byte = path.read_bytes()
    mime = magic.Magic(mime=True)
    async with aiofiles.open(path, "rb") as f:
        byte = await f.read()
    files = {
        # 'file': ('驱蚊酯驱蚊液65ml_18.jpg', '', 'image/jpeg'),
        "file": (path.name, byte, mime.from_file(path)),
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


async def get_category() -> dict:
    category_list = {
        "米面粮油": {"level": "1", "children": []},
        "食品零食": {"level": "5", "children": []},
        "生鲜水果": {"level": "8", "children": []},
        "精致礼盒": {"level": "10", "children": []},
        "五谷杂粮": {"level": "18", "children": []},
        "滋补保健": {"level": "26", "children": []},
        "个护清洁": {"level": "27", "children": []},
        "日用百货": {"level": "39", "children": []},
        "本地生活": {"level": "51", "children": []},
        "家用电器": {"level": "52", "children": []},
        "厨房小电": {"level": "62", "children": []},
        "手机数码": {"level": "96", "children": []},
        "美妆护肤": {"level": "138", "children": []},
        "母婴亲子": {"level": "243", "children": []},
        "酒水饮料": {"level": "300221", "children": []},
        "运动户外": {"level": "300230", "children": []},
        "文具用品": {"level": "300246", "children": []},
        "测试二级分类": {"level": "300258", "children": []},
        "1234": {"level": "300259", "children": []},
        "面粉挂面": {"level": "300266", "children": []},
        "水饮冲调": {"level": "300270", "children": []},
    }
    data = {}
    for category, v in category_list.items():
        ids = v.get("level")

        params = {
            "level": "2",
            "pId": ids,
        }

        response = await get(
            "http://hlt-admin.honglitong.cn/goods/ajax/load-category",
            params=params,
        )

        parse = parse_html_options(response.text)

        vv = {"level": ids, "children": parse}
        data[category] = vv
    return data


if __name__ == "__main__":
    import asyncio
    import json

    cat = asyncio.run(get_category())
    with open("category.json", "w") as f:
        json.dump(cat, f, ensure_ascii=False, indent=4)

    # resp = asyncio.run(upload_file('poster', pathlib.Path('企悦汇选品1038-1197 (2)/未命名文件夹 2/1038.儿童内衣专用洗衣液300ml/主图/81688faeabc9cbd0a1d92ddd3df1887.jpg')))
    # pass
