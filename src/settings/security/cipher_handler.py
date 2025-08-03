from cryptography.fernet import Fernet
from urllib.parse import quote, unquote
from typing import Union
import os


class CipherHandler:

    def __init__(self):
        self.__key = os.getenv('CIPHER_KEY') if os.getenv('CIPHER_KEY') else Fernet.generate_key()
        self.__fernet = Fernet(self.__key)

    def init_key(self):
        os.environ['CIPHER_KEY'] = self.__key

    def encode(self, str2encode: Union[str, bytes]) -> str:
        if not isinstance(str2encode, bytes):
            str2encode = str2encode.encode("utf8")
        return self.__fernet.encrypt(str2encode).decode("utf8")

    def decode(self, str2decode: str) -> str:
        return self.__fernet.decrypt(str2decode).decode("utf8")

    def url_safe_encode(self, str2encode):
        return quote(self.encode(str2encode))

    def decode_from_url(self, str2decode):
        return unquote(self.decode(str2decode))
