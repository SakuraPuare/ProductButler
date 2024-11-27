import time
from json import JSONDecodeError

import httpx
import loguru

from files import managed_exists, managed_open
from https import get as base_get
from https import post as base_post


def update_token() -> str:
    if not managed_exists('x-token.token'):
        return ''

    global base_headers
    with managed_open('x-token.token', 'r') as f:
        token = f.read().strip()
    base_headers.update({'X-Token': token})
    return token


base_headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json;charset=UTF-8',
    'DNT': '1',
    'Origin': 'https://mall.zlqiyuehui.com',
    'Referer': 'https://mall.zlqiyuehui.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'X-Token': ''
}
update_token()


async def post(url, headers: dict = None, *args, **kwargs) -> httpx.Response:
    new_headers = base_headers
    if headers is not None:
        new_headers.update(headers)

    try:
        response = await base_post(url, headers=new_headers, *args, **kwargs)

        json = response.json()

        assert json.get('errno') == 0, json.get('errmsg')
        return response
    except JSONDecodeError as e:
        raise Exception(f'JSONDecodeError: {e} {response.text}')
    except AssertionError as e:
        loguru.logger.error(e)
        raise Exception(e)
    except Exception as e:
        loguru.logger.error(e)
        time.sleep(1)
        return await base_post(url, headers=new_headers, *args, **kwargs)


async def get(url, params: dict = None, headers: dict = None, *args, **kwargs) -> httpx.Response:
    new_headers = base_headers
    if headers is not None:
        new_headers.update(headers)

    try:
        response = await base_get(url, params=params, headers=new_headers, *args, **kwargs)

        json = response.json()

        assert json.get('errno') == 0, json.get('errmsg')
        return response
    except AssertionError as e:
        loguru.logger.error(e)
        raise Exception(e)
    except Exception as e:
        loguru.logger.error(e)
        time.sleep(1)
        return await base_get(url, params, *args, **kwargs)
