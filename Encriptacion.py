from cryptography.fernet import Fernet
import base64
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC



class Seguridad:
    def contrasenaLlave(self, contrasena):
        tmoContrasena = str(contrasena)
        contrasenaBinario = tmoContrasena.encode()
        salto = b'Ju@n1:1'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salto,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(contrasenaBinario))

    def encriptarLlaveSecreta(self, contrasena, llaveSecreta):
        f = Fernet(self.contrasenaLlave(contrasena))
        llaveEncriptada = f.encrypt(llaveSecreta.encode())
        return llaveEncriptada

    def desEncriptarLlaveSecreta(self, contrasena, llaveSecretaEncriptada):
        f = Fernet(self.contrasenaLlave(contrasena))
        try:
            llaveDesEncriptada = f.decrypt(llaveSecretaEncriptada)
            return llaveDesEncriptada
        except:
            return False