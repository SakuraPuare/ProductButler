import asyncio
import json
import pathlib

import loguru
import pandas

from apis import add_goods, upload_file
from utils import glob_file_in_folder
from .typehints import Category
from .utils import get_category_level_1, get_category_level_2


async def main():
    for _, row in data.iterrows():
        try:
            # 序号	一级分类	二级分类	品牌	品名	规格	对广行达结算价 	含税运一件代发价	状态

            ids = row["序号"]
            category1 = row["一级分类"]
            category2 = row["二级分类"]
            brand = row["品牌"]
            goods_name = row["品名"]
            level_1_name, level_1 = get_category_level_1(category1)
            level_2_name, level_2 = get_category_level_2(
                level_1_name, category2)
            market_price = row["含税运一件代发价"]
            bid_price = row["对广行达结算价"]
            weight = row["规格"]
            loguru.logger.info(
                f"[{ids}] {category1} {category2} {brand} {
                goods_name} {market_price} {bid_price} {weight}"
            )

            # get image
            image_folder = [
                i for i in image_folder_list if i.name.startswith(str(ids))][-1]

            # find all image in image folder and get path
            posts, details = glob_file_in_folder(image_folder)

            # check the info
            loguru.logger.warning(
                f'\nposts_url: {
                '\n'.join(['/'.join(i.parts[2:]) for i in posts])}\n\n'
                + f'details: {'\n'.join(['/'.join(i.parts[2:])
                                         for i in details])}'
            )
            loguru.logger.warning(
                f"\nori: {category1} {category2}\n" +
                f"pro: {level_1_name} {level_2_name}"
            )
            ipt = input().split()
            if "c" in ipt:
                loguru.logger.warning(f"Continue")
                continue

            loguru.logger.warning(f"{goods_name} {weight}")
            weight = input("weight: ").strip()
            if not weight:
                weight = 1
            loguru.logger.warning(f"weight: {weight}")

            posts_url = await asyncio.gather(
                *[asyncio.create_task(upload_file("title", i)) for i in posts]
            )
            details_url = await asyncio.gather(
                *[asyncio.create_task(upload_file("detail", i)) for i in details]
            )

            resp = await add_goods(
                poster_url=posts_url,
                detail_url=details_url,
                brand=brand,
                goods_name=goods_name,
                market_price=market_price,
                bid_price=bid_price,
                weight=weight,
                level_1=level_1,
                level_2=level_2,
            )

            if not resp.get("success"):
                loguru.logger.error(f'[{ids}] {resp.get("msg")}')
            else:
                loguru.logger.info(f"[{ids}] success")

        except Exception as e:
            loguru.logger.error(str(type(e)), e)
        finally:
            with open("black_list.txt", "a", encoding='u8') as f:
                f.write(f"{ids}\n")


if __name__ == "__main__":
    file_name = "标品目录表-企悦汇2024-10.18（更新至1961种选品）.xlsx"
    image_path = "企悦汇选品1869-1961/企悦汇选品1869-1961"
    image_folder_list = [i for i in pathlib.Path(
        image_path).iterdir() if i.is_dir()]
    data = pandas.read_excel(file_name)

    ranges = 1869, 1961
    with open("black_list.txt", "r", encoding='u8') as f:
        black_list: list[int] = list(map(int, f.readlines()))

    with open("category.json", "r", encoding='u8') as f:
        category: Category = json.load(f)
    # find data id in ranges
    data = data.loc[(data["序号"] >= ranges[0]) & (data["序号"] <= ranges[1])]
    data = data.loc[data["状态"] != "无需上线"]
    data = data.loc[~data["序号"].isin(black_list)]
    data = data.loc[data["二级分类"] != "面部护肤"]

    asyncio.run(main())
    pass
