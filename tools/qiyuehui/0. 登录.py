import asyncio
import pathlib
import sys

sys.path.append(
    str(pathlib.Path(__file__).parent.parent.parent)
)

from upload.qiyuehui.apis import login


async def main():
    await login()


if __name__ == "__main__":
    asyncio.run(main())
