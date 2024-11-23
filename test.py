import pathlib

if __name__ == "__main__":
    import upload.qiyuehui.apis as apis

    apis.login()

    import upload.qiyuehui.cos as cos

    ret = cos.upload_file(pathlib.Path('verify.jpg'))

    print(ret)
