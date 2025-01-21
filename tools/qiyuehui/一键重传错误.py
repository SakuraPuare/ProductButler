import pathlib
import sys
import asyncio
sys.path.append(
    str(pathlib.Path(__file__).parent.parent.parent)
)

from upload.qiyuehui.apis import update


async def main():
    with open('error.txt', 'r', encoding='gbk') as f:
        data = [eval(line.strip()) for line in f.readlines()]
    
    err_list = []
    for line in data:
        resp = await update(line)
        print(resp.text)
        
        json_resp = resp.json()
        if json_resp['errno'] != 0:
            err_list.append(str(line))

    with open('error.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(err_list))

if __name__ == '__main__':
    asyncio.run(main())
