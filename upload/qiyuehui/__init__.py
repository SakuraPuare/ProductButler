import asyncio
import time


async def login():
    from .browser import launch_browser

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
            # 打印请求头
            if 'x-token' in request.headers:
                token.add(request.headers['x-token'])

    if not token:
        return
    token = token.pop()

    with open('x-token.token', 'w') as f:
        f.write(token)


if __name__ != "__main__":
    asyncio.run(login())
    pass
