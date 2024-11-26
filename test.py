import asyncio
import pathlib

if __name__ == "__main__":
    import upload.qiyuehui.apis as apis

    apis.login()

    import upload.qiyuehui.cos as cos

    ret = asyncio.run(cos.upload_file(pathlib.Path(r'C:\Users\SakuraPuare\Pictures\wallhaven-g8orp7.png')))

    print(ret)
