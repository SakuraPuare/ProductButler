import requests

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json;charset=UTF-8',
    'DNT': '1',
    'Origin': 'https://mall.zlqiyuehui.com',
    'Referer': 'https://mall.zlqiyuehui.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}


base_headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json;charset=UTF-8',
    'DNT': '1',
    'Origin': 'https://mall.zlqiyuehui.com',
    'Referer': 'https://mall.zlqiyuehui.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'X-Token': '',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}
json_data = {
    'goods': {
        'clearCustom': None,
        'gallery': [
            'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611855035.jpg', 
'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611854780.png', 
'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611854565.jpg', 
'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611853500.jpg', 
'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611854249.jpg', 
'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611856843.jpg', 
'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611856039.jpg', 
'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611856352.jpg', 
'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611856585.jpg', 
'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611855841.jpg'
],
        'categoryId': '8bee89d1-927f-11ee-b3e4-525400154120',
        'retailPrice': '234.50',
        'counterPrice': '478.00',
        'costPrice': '129.00',
        'desc': '<p><img src="https://cdn.zlqiyuehui.com/20004/1732611160692399.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732611160681877.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732611160681670.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732611161092440.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732611161111490.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732611161170414.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732611161646827.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732611161596157.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732611161640348.jpg" style=""/></p><p><img src="https://cdn.zlqiyuehui.com/20004/1732611161962910.jpg" style=""/></p><p><br/></p>',
        'goodsNum': 10000,
        'speciType': True,
        'unit': '件',
        'wlTemplateId': '7a10debc-b76e-11ee-b3e4-525400154120',
        'wlTemplateType': 1,
        'name': '法国啄木鸟 云归棉涤磨毛四件套-克妮',
        'goodsSn': '6972830135433',
        'weight': '1.00',
        'isOnSale': True,
    },
    'products': [],
    'specifications': [],
    'attributes': [],
}

response = requests.post('https://api.zlqiyuehui.com/vender/goods/create', headers=headers, json=json_data)

['https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611855035.jpg', 'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611854780.png', 'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611854565.jpg', 'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611853500.jpg', 'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611854249.jpg', 'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611856843.jpg', 'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611856039.jpg', 'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611856352.jpg', 'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611856585.jpg', 'https://qiyuehui-1300221291.cos.ap-guangzhou.myqcloud.com/20004/gallery/1732611855841.jpg']