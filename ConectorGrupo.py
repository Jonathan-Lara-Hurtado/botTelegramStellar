import sqlite3
from stellar_sdk import Keypair, Server, exceptions,Account,TransactionBuilder,Network
import qrcode

#librerias para trabajar binariamente
from io import BytesIO,StringIO

class ConexionGrupo:
    def __init__(self,db='billeteras.db'):
        self.conexion = sqlite3.connect(db)

    def crearTablabilleteraGrupo(self):
        c = self.conexion.cursor()
        c.execute('''CREATE TABLE billeteraGrupo
                     (idGrupo real,pllave text,sllave text,integrantes real,primary key("idGrupo"))''')

    def crearTablabilleteraUsuarioGrupo(self):
        c = self.conexion.cursor()
        c.execute('''CREATE TABLE billeteraUsuarioGrupo
                            (id integer primary key autoincrement,idTelegram real,fkGrupo real,pllave text,sllave text,integrantes real)''')

    def generarPar(self):
        keypair = Keypair.random()
        return [keypair.public_key,keypair.secret]

    def insertarLlavesGrupo(self,idGrupo):
        llaves = self.generarPar()
        c = self.conexion.cursor()
        valores = [(idGrupo,llaves[0],llaves[1],1)]
        c.executemany('Insert Into billeteraGrupo values (?,?,?,?)',valores)
        self.conexion.commit()

    def modificarNumeroIntegranteGrupo(self,idGrupo,numero):
        c = self.conexion.cursor()
        query = """Update billeteraGrupo set integrantes = ? where idGrupo = ?"""
        data = (numero,idGrupo)
        c.execute(query,data)
        self.conexion.commit()

    def misDatosGrupo(self,idGrupo):
        c = self.conexion.cursor()
        query = "select * from billeteraGrupo where idGrupo="+str(idGrupo)
        p = c.execute(query)
        lista = list()
        for i in p:
            for e in i:
                lista.append(e)
        return lista

    def insertarIntegrantesBilletera(self,usuarios,grupo):
        c = self.conexion.cursor()
        datos = []
        for i in usuarios:
            llaves = self.generarPar()
            datos.append((i.user.id,grupo,llaves[0],llaves[1]))
        c.executemany('Insert into billeteraUsuarioGrupo (idTelegram,fkGrupo,pllave,sllave) values (?,?,?,?);',datos)
        self.conexion.commit()

    def obtenerListaIntegrantesGrupo(self,grupo):
        c = self.conexion.cursor()
        query = "select * from billeteraUsuarioGrupo where fkGrupo=" + str(grupo)
        p = c.execute(query)
        lista = list()
        for i in p:
            lista.append(i)

        return lista



def darQrBuffer(texto):
    buf = BytesIO()
    qr = qrcode.QRCode(version=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_L,
                       box_size=6,
                       border=2)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(buf, "PNG")
    return buf

