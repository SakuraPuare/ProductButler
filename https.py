import asyncio

import httpx
import loguru

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

limit = asyncio.Semaphore(5)

timeout = httpx.Timeout(10, connect=10, read=20)


async def post(url, data, headers: dict = None, *args, **kwargs) -> httpx.Response:
    global limit
    async with limit:
        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=timeout) as client:
            response = await client.post(url, data=data, headers=headers, *args, **kwargs)
            loguru.logger.info(f'[POST] {url} {str(data)[:15]} {
            response.status_code}')
            response.json()
            return response


async def get(url, params: dict = None, headers: dict = None, *args, **kwargs) -> httpx.Response:
    async with limit:
        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=timeout) as client:
            response = await client.get(url, params=params, headers=headers, *args, **kwargs)
            loguru.logger.info(f'[GET] {url} {response.status_code}')
            return response


async def put(url, headers: dict = None, *args, **kwargs) -> httpx.Response:
    async with limit:
        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=timeout) as client:
            response = await client.put(url, headers=headers, *args, **kwargs)
            loguru.logger.info(f'[PUT] {url} {response.status_code}')
            return response
