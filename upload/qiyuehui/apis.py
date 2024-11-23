import asyncio
import base64
import json
import pathlib
import time

from .https import get, post, update_token

token_path = pathlib.Path('x-token.token')

default_data = {
    'goods': {
        'clearCustom': None,
        # 'gallery': [
        #     'https://cdn.zlqiyuehui.com/20004/gallery/1732278082313.jpg',
        #     'https://cdn.zlqiyuehui.com/20004/gallery/1732278082314.jpg',
        #     'https://cdn.zlqiyuehui.com/20004/gallery/1732278082314.jpg',
        #     'https://cdn.zlqiyuehui.com/20004/gallery/1732278082313.jpg',
        #     'https://cdn.zlqiyuehui.com/20004/gallery/1732278082316.jpg',
        #     'https://cdn.zlqiyuehui.com/20004/gallery/1732278082317.jpg',
        #     'https://cdn.zlqiyuehui.com/20004/gallery/1732278082317.jpg',
        #     'https://cdn.zlqiyuehui.com/20004/gallery/1732278082316.jpg',
        #     'https://cdn.zlqiyuehui.com/20004/gallery/1732278082318.jpg',
        #     'https://cdn.zlqiyuehui.com/20004/gallery/1732278082318.jpg',
        # ],
        # 'categoryId': '8b43d1d5-8f47-11ee-b3e4-525400154120',
        # 'retailPrice': '198.20',
        'counterPrice': 0,
        # 'costPrice': '109.00',
        # 'desc': '<p><img src="https://cdn.zlqiyuehui.com/20004/1732278363367842.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732278363354801.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732278363367242.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732278363796926.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732278363829385.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732278364234582.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732278364469276.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732278364528023.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732278364564681.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732278364756285.jpg" style=""/></p><p><br/></p>',
        'goodsNum': 10000,
        'speciType': True,
        'unit': '件',
        'wlTemplateId': '7a10debc-b76e-11ee-b3e4-525400154120',
        'wlTemplateType': 1,
        # 'name': '法国啄木鸟 自由棉涤磨毛四件套-莱尔',
        # 'goodsSn': '6972830135419',
        'weight': '1.00',
        'isOnSale': True,
    },
    'products': [],
    'specifications': [],
    'attributes': [],
}


async def create(
        gallery: list[str],
        categoryId: str,
        retailPrice: str,
        costPrice: str,
        desc: str,
        name: str,
        goodsSn: str,
):
    pass


async def add_vip_goods(goods_id: str):
    params = {
        'goodsId': goods_id,
    }

    await post('https://api.zlqiyuehui.com/vender/goods/addVipGood', params=params)


async def get_vip_goods(page: int = 1, size: int = 10):
    params = {
        'page': page,
        'size': size,
        'status': 'false',
        'name': '',
        'goodsId': '',
    }

    response = await get(
        'https://api.zlqiyuehui.com/vender/goods/vipGoodList', params=params)

    data = response.json()
    return data.get('data', {}).get('goods', [])


async def get_goods_detail(product_id: str):
    params = {
        'id': product_id,
        'type': '1',
    }

    return await get('https://api.zlqiyuehui.com/vender/goods/detail', params=params)


async def set_vip_price(
        product_id: str,
        vendor_id: int,
        goods_id: str,
        price: float,
        number: int,
        add_time: str,
        deleted: bool,
        specification_code: str,
        cost_price: float,
        vip1_price: float,
        vip2_price: float,
        vip3_price: float,
        vip4_price: float
):
    json_data = {
        'products': [
            {
                'id': product_id,
                'venderId': vendor_id,
                'goodsId': goods_id,
                'specifications': [
                    '标准',
                ],
                'price': price,
                'number': number,
                'addTime': add_time,
                'deleted': deleted,
                'specificationCode': specification_code,
                'costPrice': cost_price,
                'vip1Price': vip1_price,
                'vip2Price': vip2_price,
                'vip3Price': vip3_price,
                'vip4Price': vip4_price,
            },
        ],
    }

    await post(
        'https://api.zlqiyuehui.com/vender/goods/saveVipPrice', json=json_data)


coscredential_url_as_base64 = "aHR0cHM6Ly9hcGkuemxxaXl1ZWh1aS5jb20vdmVuZGVyL3VwbG9hZC9DT1NDcmVkZW50aWFs"
coscredential_url = base64.b64decode(
    coscredential_url_as_base64).decode('utf-8')


async def get_cors_credentials() -> dict:
    response = await get(coscredential_url)
    data = response.json().get('data', '')

    if not data:
        return {}

    return json.loads(data)


async def check_login():
    try:
        resp = get('https://api.zlqiyuehui.com/vender/dashboard')
    except Exception as e:
        return False
    return True


def login():
    if token_path.exists():
        update_token()
        return

    if asyncio.run(check_login()):
        return

    from browser import launch_browser

    driver = launch_browser()

    if not driver:
        return

    url = 'https://open.weixin.qq.com/connect/qrconnect?appid=wxce7206f982c36053&redirect_uri=https%3A%2F%2Fmall.zlqiyuehui.com%2Fhome%2Flogin&response_type=code&scope=snsapi_login&state=qiyuehui#wechat_redirect'
    driver.get(url)

    while True:
        if driver.current_url.startswith('https://mall.zlqiyuehui.com'):
            break
        time.sleep(1)

    token = set()
    for request in driver.requests:
        if request.response:
            if 'x-token' in request.headers:
                token.add(request.headers['x-token'])

    if not token:
        return
    token = token.pop()

    with open(token_path, 'w') as f:
        f.write(token)

    update_token()
