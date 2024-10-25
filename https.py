import asyncio
import httpx
import loguru
import time

limit = asyncio.Semaphore(5)

cookies = {
}

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


async def post(url, data, headers: dict = None, *args, **kwargs) -> httpx.Response:
    new_header = headers
    if headers is not None:
        new_header.update(headers)

    async with limit:
        async with httpx.AsyncClient(verify=False, follow_redirects=True) as client:
            try:
                response = await client.post(url, data=data, cookies=cookies, headers=new_header, *args, **kwargs)
                loguru.logger.info(f'[POST] {url} {str(data)[:15]} {
                response.status_code}')
                response.json()
                return response
            except Exception as e:
                loguru.logger.error(e)
                time.sleep(1)
                return await post(url, data, headers, *args, **kwargs)


async def get(url, params, *args, **kwargs) -> httpx.Response:
    async with limit:
        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.get(url, params=params, cookies=cookies, headers=base_headers, *args, **kwargs)
                loguru.logger.info(f'[GET] {url}?{'&'.join(
                    [f"{k}={v}" for k, v in params.items()])} {response.status_code}')
                return response
            except Exception as e:
                loguru.logger.error(e)
                time.sleep(1)
                return await get(url, params, *args, **kwargs)
