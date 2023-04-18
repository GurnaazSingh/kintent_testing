import base64
import json
from typing import Dict
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class ApiEncryption:
    """
    Responsibility For Encryption  / Decryption of the universal request/response
    """
    def __init__(self,i_vector,enc_key):
        

        self.__iv=i_vector.encode('utf-8')
        self.__key=enc_key
    
    def _encrypt(self,data):
        """
        :params data : literal eval string
        """
        data = pad(data.encode(), 16)
        cipher = AES.new(self.__key.encode('utf-8'), AES.MODE_CBC, self.__iv)
        return base64.b64encode(cipher.encrypt(data))

    def _decrypt(self,enc):
        """
        :params enc: encrypted string
        """
        enc = base64.b64decode(enc)
        cipher = AES.new(self.__key.encode('utf-8'), AES.MODE_CBC, self.__iv)
        return unpad(cipher.decrypt(enc), 16)
    
    
    def get_decrypt(self,encrypted_request)->Dict:
        """
        params encrypted_request : encrypted string
        
        Returns :
        value :Dict
        """
        decrypted_value = self._decrypt(enc=encrypted_request)
        value = decrypted_value.decode("utf-8", "ignore")
        value=json.loads(value)
        return value
    
    
    def get_encryption_string(self,**kwargs):...