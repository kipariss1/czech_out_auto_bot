from cryptography.fernet import Fernet
from urllib.parse import quote, unquote
from typing import Union


class CipherHandler:

    def __init__(self):
        self.__key = Fernet.generate_key()
        self.__fernet = Fernet(self.__key)

    def encode(self, str2encode: Union[str, bytes]):
        if not isinstance(str2encode, bytes):
            str2encode = str2encode.encode("utf8")
        return self.__fernet.encrypt(str2encode)

    def decode(self, str2decode: str):
        return self.__fernet.decrypt(str2decode)

    def url_safe_encode(self, str2encode):
        return quote(self.encode(str2encode))

    def decode_from_url(self, str2decode):
        return unquote(self.decode(str2decode))
