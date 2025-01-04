import base64
import concurrent.futures
import pathlib
import time
import asyncio

import loguru
from qcloud_cos import CosConfig, CosS3Client

from .apis import get_cors_credentials
from .entity import COSCredential

bucket_as_base64 = "cWl5dWVodWktMTMwMDIyMTI5MQ=="
bucket = base64.b64decode(bucket_as_base64).decode('utf-8')

cors_credential = None
client = None
executor = concurrent.futures.ThreadPoolExecutor()  # 创建线程池

def sync_upload_file(filename: pathlib.Path) -> str:
    """同步上传单个文件"""
    global cors_credential, client
    
    try:
        url_name = str(int(time.time() * 1000)) + filename.suffix

        response = client.upload_file(
            Bucket=bucket,
            LocalFilePath=filename.absolute(),
            Key='20004/gallery/' + url_name,
            PartSize=1,
            MAXThread=10,
            EnableMD5=False
        )

        loguru.logger.debug(f'[UPLOAD] {filename} {response["ETag"]}')
        return 'https://cdn.zlqiyuehui.com/20004/gallery/' + url_name
    except Exception as e:
        loguru.logger.error(f'[UPLOAD ERROR] {filename}: {str(e)}')
        raise e

async def upload_file(filename: pathlib.Path) -> str:
    """异步上传单个文件的包装器"""
    global cors_credential, client

    # check validity of credentials
    if not cors_credential or cors_credential.is_expired:
        # flush
        cors_credential = COSCredential.from_dict(await get_cors_credentials())
        config = CosConfig(
            Region='ap-guangzhou',
            SecretId=cors_credential.tmpSecretId,
            SecretKey=cors_credential.tmpSecretKey,
            Token=cors_credential.sessionToken
        )
        client = CosS3Client(config)

    # 使用线程池执行同步上传
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, sync_upload_file, filename)

async def upload_files(files: list[pathlib.Path]) -> list[str]:
    """批量上传文件"""
    global cors_credential, client

    # check validity of credentials
    if not cors_credential or cors_credential.is_expired:
        # flush
        cors_credential = COSCredential.from_dict(await get_cors_credentials())
        config = CosConfig(
            Region='ap-guangzhou',
            SecretId=cors_credential.tmpSecretId,
            SecretKey=cors_credential.tmpSecretKey,
            Token=cors_credential.sessionToken
        )
        client = CosS3Client(config)

    # 使用线程池并行上传所有文件
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(executor, sync_upload_file, file) for file in files]
    return await asyncio.gather(*tasks)


if __name__ == '__main__':
    test_image = pathlib.Path('verify.jpg')
    print(upload_file(test_image))
