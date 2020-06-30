import sqlite3
from stellar_sdk import Keypair, Server, exceptions,Account,TransactionBuilder,Network,Signer

class ConexionAssets:
    def __init__(self,db='billeteras.db'):
        self.conexion = sqlite3.connect(db)

    def crearTablaUsuarios(self):
        c = self.conexion.cursor()
        c.execute('''CREATE TABLE billeterasAssets
                     (idTelegram real,pllave text,sllave text)''')

    def generarPar(self):
        keypair = Keypair.random()
        return [keypair.public_key,keypair.secret]

    def insertarUsuario(self,usuario):
        llaves = self.generarPar()
        c = self.conexion.cursor()
        valores = [(usuario,llaves[0],llaves[1])]
        c.executemany('Insert Into billeterasAssets values (?,?,?)',valores)
        self.conexion.commit()

    def misDatos(self,usuario):
        c = self.conexion.cursor()
        query = "select * from billeterasAssets where idTelegram="+str(usuario)
        p = c.execute(query)
        lista = list()
        for i in p:
            for e in i:
                lista.append(e)
        return lista

