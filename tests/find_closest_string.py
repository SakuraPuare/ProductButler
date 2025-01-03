import sys
import os
import tqdm
from tqdm.contrib.concurrent import process_map

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from utils import find_closest_string

goods = pd.read_excel(r'C:\Users\SakuraPuare\Desktop\HongLiTong\data\2025年1月3日\职友团上架明细表.xls', header=0)
goods_name_list = goods['商品名称'].tolist()
goods_name_map = goods.set_index('商品名称')['序号'].to_dict()

def proc(name):
    global goods_name_list, goods_name_map

    result = []
    idx = find_closest_string(name, goods_name_list)
    find_goods_id = goods_name_map.get(goods_name_list[idx], None)
    if find_goods_id:
        result.append({
            '商品名称': name,
            'closest_idx': idx,
            'find_goods_id': find_goods_id,
        })
    # tqdm.tqdm.write(f'{name}: {find_goods_id} {idx}')
    return result

if __name__ == '__main__':

    converted = pd.read_excel(r'C:\Users\SakuraPuare\Desktop\HongLiTong\goods_list.xlsx', header=0)
    names = converted['name'].tolist()
    result = process_map(proc, names, max_workers=15, chunksize=10)
    
    from itertools import chain
    result = list(chain(*result))

    pd.DataFrame(result).to_excel('./result.xlsx', index=False)
