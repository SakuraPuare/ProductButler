import asyncio
import concurrent.futures
import random
import threading
import time

lock = threading.Lock()
executor = concurrent.futures.ThreadPoolExecutor()  # 创建线程池

name_set = set()


def sync_upload_file(filename: str) -> str:
    """同步上传单个文件"""
    global name_set

    with lock:
        url_name = str(int(time.time() * 1000)) + ("%02d" % random.randint(1, 99))
        while url_name in name_set:
            url_name = str(int(time.time() * 1000)) + ("%02d" % random.randint(1, 99))
        name_set.add(url_name)

        with open('test_url.txt', 'a') as f:
            f.write(url_name + '\n')


def test_url():
    with open('test_url.txt', 'r') as f:
        url = [i for i in f.read().splitlines() if i.strip()]

    url_set = set(url)

    if len(url) != len(url_set):
        print(f'{len(url)} != {len(url_set)}')
        for i in url_set:
            if url.count(i) > 1:
                print(i)
    else:
        print(f'{len(url)} == {len(url_set)}')


async def upload_files() -> list[str]:
    """批量上传文件"""

    l = [i for i in range(int(1e4))]

    # 使用线程池并行上传所有文件
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(executor, sync_upload_file, file) for file in l]
    return await asyncio.gather(*tasks)


if __name__ == '__main__':
    import os

    os.remove('test_url.txt')
    asyncio.run(upload_files())
    test_url()
