import pandas as pd

if __name__ == '__main__':
    data = pd.read_excel(r'tests\get_loc_by_goods_detail.xls', header=0)
    print(data['商品名称'].str.contains('美厨304不锈钢圆形三层饭盒\xa0 MCFT629(樱花粉）', regex=False).map(bool))
