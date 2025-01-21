import base64
import json
import pathlib
import time

import loguru

from files import managed_exists, managed_open
from .https import get, get_until_success, post, update_token
from .utils import fmt_desc

token_path = pathlib.Path('x-token.token')


async def create(
        gallery: list[str],
        category_list: list[dict[str, str]],
        retailPrice: str,
        counterPrice: str,
        costPrice: str,
        desc: list[str],
        name: str,
        goodsSn: str,
        weight: str
):
    if str(goodsSn) == 'nan':
        goodsSn = ''

    data = {
        'goods': {
            'clearCustom': None,
            'gallery': gallery[:10],
            'categoryId': ','.join([i.get('level') for i in category_list]),
            'retailPrice': "%.2f" % float(retailPrice),
            'counterPrice': "%.2f" % float(counterPrice),
            'costPrice': "%.2f" % float(costPrice),
            'desc': fmt_desc(desc),
            'goodsNum': 10000,
            'speciType': True,
            'unit': '件',
            'wlTemplateId': '7a10debc-b76e-11ee-b3e4-525400154120',
            'wlTemplateType': 1,
            'name': name.strip(),
            'goodsSn': ''.join(goodsSn.split())[:60],
            'weight': "%.2f" % float(weight),
            'isOnSale': True,
        },
        'products': [],
        'specifications': [],
        'attributes': [],
    }

    resp = await post('https://api.zlqiyuehui.com/vender/goods/create', json=data)

    return resp


async def update(data: dict):
    resp = await post(f'https://api.zlqiyuehui.com/vender/goods/update', json=data)

    return resp


async def add_vip_goods(goods_id: str):
    params = {
        'goodsId': goods_id,
    }

    await post('https://api.zlqiyuehui.com/vender/goods/addVipGood', params=params)


async def search_goods(name: str):
    params = {
        'page': 1,
        'limit': 100,
        'isOnSale': True,
        'goodsNum': '',
        'isVague': 0,
        'name': name.strip(),
    }

    resp = await get('https://api.zlqiyuehui.com/vender/goods/list', params=params)

    return resp.json().get('data', {}).get('items', [])


async def get_vip_goods_list(page: int = 1, size: int = 10, status: bool = False):
    params = {
        'page': page,
        'size': size,
        'status': status,
        'name': '',
        'goodsId': '',
    }

    response = await get(
        'https://api.zlqiyuehui.com/vender/goods/vipGoodList', params=params)

    data = response.json()
    return data.get('data', {}).get('goods', [])


async def get_goods_list(page: int = 1, limit: int = 10):
    params = {
        'page': page,
        'limit': limit,
        'isOnSale': True,
        'goodsNum': '',
        'isVague': 0
    }

    response = await get('https://api.zlqiyuehui.com/vender/goods/list', params=params)

    data = response.json()
    return data.get('data', {}).get('items', [])


async def get_goods_detail(product_id: str):
    params = {
        'id': product_id,
        'type': '1',
    }

    resp = await get('https://api.zlqiyuehui.com/vender/goods/detail', params=params)

    return resp.json().get('data', {})


async def delete_goods(goods_id: str):
    json_data = {
        'id': goods_id,
    }

    await post('https://api.zlqiyuehui.com/vender/goods/delete', json=json_data)


async def set_vip_price(
        product_id: str,
        vip1_price: float,
        vip2_price: float,
        vip3_price: float,
        vip4_price: float
):
    json_data = {
        'products': [
            {
                'id': product_id,
                'vip1Price': "%.2f" % float(vip1_price),
                'vip2Price': "%.2f" % float(vip2_price),
                'vip3Price': "%.2f" % float(vip3_price),
                'vip4Price': "%.2f" % float(vip4_price),
            },
        ],
    }

    await post(
        'https://api.zlqiyuehui.com/vender/goods/saveVipPrice', json=json_data)


async def get_category():
    response = await get_until_success('https://api.zlqiyuehui.com/vender/goods/catAndBrand')

    category_list = response.json().get('data', {}).get(
        'categoryList', [])

    category = {}

    for i in category_list:
        category[i['label']] = {
            'level': i['id'],
            'children': {},
            'name': i['label'],
        }
        for j in i['children']:
            category[i['label']]['children'][j['label']] = {
                'level': j['id'],
                'children': {},
                'name': j['label'],
            }

    with managed_open('category.json', 'w', encoding='u8') as f:
        f.write(json.dumps(category, indent=4, ensure_ascii=False))
    return category


coscredential_url_as_base64 = "aHR0cHM6Ly9hcGkuemxxaXl1ZWh1aS5jb20vdmVuZGVyL3VwbG9hZC9DT1NDcmVkZW50aWFs"
coscredential_url = base64.b64decode(
    coscredential_url_as_base64).decode('utf-8')


async def get_cors_credentials() -> dict:
    response = await get_until_success(coscredential_url)
    data = response.json().get('data', '')

    if not data:
        return {}

    return json.loads(data)


async def check_login():
    try:
        await get('https://api.zlqiyuehui.com/vender/order/getRefundNum')
    except Exception as e:
        return False
    return True


async def login():
    # if token_path.exists():
    if managed_exists('x-token.token'):
        update_token()

    if await check_login():
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
    while True:
        for request in driver.requests:
            if request.response:
                if 'x-token' in request.headers:
                    token.add(request.headers['x-token'])

        if not token:
            loguru.logger.warning('Waiting for token...')
            time.sleep(1)
        else:
            break

    token = token.pop()

    with managed_open(token_path, 'w') as f:
        f.write(token)

    update_token()
    driver.quit()
