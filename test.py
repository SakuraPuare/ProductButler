import httpx as requests

cookies = {
}

headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundary',
    'DNT': '1',
    'Origin': 'http://hlt-admin.honglitong.cn',
    'Pragma': 'no-cache',
    'Referer': 'http://hlt-admin.honglitong.cn/goods/add/page',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}

files = {
    'file': ('内衣专用洗衣液300ml-v4_15.jpg', open(
        '企悦汇选品1038-1197 (2)/未命名文件夹 2/1038.儿童内衣专用洗衣液300ml/主图/81688faeabc9cbd0a1d92ddd3df1887.jpg',
        'rb').read(), 'image/jpeg'),
    'service': (None, 'goods/gys/detail'),
}

response = requests.post(
    'http://hlt-admin.honglitong.cn/util/open/layui/UploadImg',
    data={},
    cookies=cookies,
    headers=headers,
    files=files,
    verify=False,
)

pass
