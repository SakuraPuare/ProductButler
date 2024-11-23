import asyncio
import base64
import pathlib
import time

import loguru
from qcloud_cos import CosConfig, CosS3Client

from .apis import get_cors_credentials
from .entity import COSCredential

upload_url_as_base64 = "aHR0cHM6Ly9xaXl1ZWh1aS0xMzAwMjIxMjkxLmNvcy5hcC1ndWFuZ3pob3UubXlxY2xvdWQuY29tLzIwMDA0L2dhbGxlcnkv"
upload_base_url = base64.b64decode(upload_url_as_base64).decode('utf-8')
bucket_as_base64 = "cWl5dWVodWktMTMwMDIyMTI5MQ=="
bucket = base64.b64decode(bucket_as_base64).decode('utf-8')

cors_credential = COSCredential.from_dict(asyncio.run(get_cors_credentials()))

config = CosConfig(
    Region='ap-guangzhou',
    SecretId=cors_credential.tmpSecretId,
    SecretKey=cors_credential.tmpSecretKey,
    Token=cors_credential.sessionToken
)
client = CosS3Client(config)


def upload_file(filename: pathlib.Path) -> str:
    global cors_credential, client

    # check validity of credentials
    if cors_credential.is_expired:
        # flush
        cors_credential = COSCredential.from_dict(asyncio.run(get_cors_credentials()))

    url_name = str(int(time.time() * 1000)) + filename.suffix
    upload_url = upload_base_url + url_name

    response = client.upload_file(
        Bucket=bucket,
        LocalFilePath=filename.absolute(),
        Key='20004/gallery/' + url_name,
        PartSize=1,
        MAXThread=10,
        EnableMD5=False
    )

    loguru.logger.info(f'[UPLOAD] {filename} {response["ETag"]}')

    return upload_url


if __name__ == '__main__':
    test_image = pathlib.Path('verify.jpg')
    print(upload_file(test_image))
