import time
from json import JSONDecodeError

import httpx
import loguru

from https import get as base_get
from https import post as base_post

base_headers = {
}


async def post(url, data, headers: dict = None, *args, **kwargs) -> httpx.Response:
    new_header = headers
    if headers is not None:
        new_header.update(headers)
        try:
            response = await base_post(url, data, headers, *args, **kwargs)
            loguru.logger.info(f'[POST] {url} {str(data)[:15]} {
            response.status_code}')
            return response
        except JSONDecodeError as e:
            raise Exception(f'JSONDecodeError: {e} {response.text}')
        except Exception as e:
            loguru.logger.error(str(type(e)), e)
            time.sleep(1)
            return await base_post(url, data, headers, *args, **kwargs)


async def get(url, params: dict = None, headers: dict = None, *args, **kwargs) -> httpx.Response:
    new_headers = base_headers
    if headers is not None:
        new_headers.update(headers)

    try:
        response = await base_get(url, params=params, headers=new_headers, *args, **kwargs)
        loguru.logger.info(f'[GET] {url} {response.status_code}')

        return response
    except AssertionError as e:
        loguru.logger.error(e)
        raise Exception(e)
    except Exception as e:
        loguru.logger.error(e)
        time.sleep(1)
        return await base_get(url, params, *args, **kwargs)
