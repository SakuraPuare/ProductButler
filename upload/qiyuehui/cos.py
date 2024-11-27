import base64
import pathlib
import time

import loguru
from qcloud_cos import CosConfig, CosS3Client

from .apis import get_cors_credentials
from .entity import COSCredential

bucket_as_base64 = "cWl5dWVodWktMTMwMDIyMTI5MQ=="
bucket = base64.b64decode(bucket_as_base64).decode('utf-8')

cors_credential = None
client = None


async def upload_file(filename: pathlib.Path) -> str:
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

    url_name = str(int(time.time() * 1000)) + filename.suffix
    
    response = client.upload_file(
        Bucket=bucket,
        LocalFilePath=filename.absolute(),
        Key='20004/gallery/' + url_name,
        PartSize=1,
        MAXThread=10,
        EnableMD5=False
    )

    loguru.logger.info(f'[UPLOAD] {filename} {response["ETag"]}')

    return 'https://cdn.zlqiyuehui.com/20004/gallery/' + url_name


if __name__ == '__main__':
    test_image = pathlib.Path('verify.jpg')
    print(upload_file(test_image))
