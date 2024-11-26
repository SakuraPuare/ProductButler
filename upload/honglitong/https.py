import time
from json import JSONDecodeError

import httpx
import loguru

from https import get as base_get
from https import post as base_post
from utils import load_cookies

base_headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'DNT': '1',
    'Origin': 'http://hlt-admin.honglitong.cn',
    'Pragma': 'no-cache',
    'Referer': 'http://hlt-admin.honglitong.cn/goods/add/page',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}

cookies = load_cookies()


async def post(url, data, headers: dict = None, *args, **kwargs) -> httpx.Response:
    new_header = headers
    if headers is not None:
        new_header.update(headers)
    try:
        response = await base_post(url, data, headers, cookies=cookies, *args, **kwargs)
        if '登录' in response.text:
            loguru.logger.error(f'需要登录！')
            raise Exception(f'需要登录！')
        response.json()
        return response
    except JSONDecodeError as e:
        raise Exception(f'JSONDecodeError: {e} {response.text}')
    except Exception as e:
        loguru.logger.error(str(type(e)), e)
        time.sleep(1)
        return await base_post(url, data, headers, cookies=cookies, *args, **kwargs)


async def get(url, params: dict = None, headers: dict = None, *args, **kwargs) -> httpx.Response:
    new_headers = base_headers
    if headers is not None:
        new_headers.update(headers)

    try:
        response = await base_get(url, params=params, headers=new_headers, cookies=cookies, *args, **kwargs)

        assert '登录' not in response.text, '需要登录！'
        return response
    except AssertionError as e:
        loguru.logger.error(e)
        raise Exception(e)
    except Exception as e:
        loguru.logger.error(e)
        time.sleep(1)
        return await base_get(url, params, cookies=cookies, *args, **kwargs)


def reload_cookies():
    global cookies
    cookies = load_cookies()
