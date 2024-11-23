import datetime
import time
from dataclasses import dataclass


@dataclass
class COSCredential:
    tmpSecretId: str
    tmpSecretKey: str
    sessionToken: str
    expiration: datetime.datetime
    startTime: int
    expiredTime: int

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            tmpSecretId=data.get('credentials', {}).get('tmpSecretId', ''),
            tmpSecretKey=data.get('credentials', {}).get('tmpSecretKey', ''),
            sessionToken=data.get('credentials', {}).get('sessionToken', ''),
            expiration=datetime.datetime.fromisoformat(
                data.get('expiration', '')),
            startTime=data.get('startTime', 0),
            expiredTime=data.get('expiredTime', 0),
        )

    @property
    def is_expired(self):
        return self.expiredTime and self.expiredTime < int(time.time())
