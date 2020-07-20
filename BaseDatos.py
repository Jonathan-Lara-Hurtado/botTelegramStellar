import sqlite3
class BaseDatos:
    def __init__(self,db='billeteras.db'):
        self.conexion = sqlite3.connect(db)

    def crearTablaUsuarios(self):
        c = self.conexion.cursor()
        c.execute('''CREATE TABLE billeteras
                     (idTelegram real,pllave text,sllave text,CuentaEncriptada INTEGER default 0)''')

    def crearTablaUsuariosAssets(self):
        c = self.conexion.cursor()
        c.execute('''CREATE TABLE billeterasAssets
                     (idTelegram real,pllave text,sllave text)''')

    def crearTablaEncuestaGrupal(self):
        c = self.conexion.cursor()
        c.execute('''CREATE TABLE Encuesta
                     (idEncuesta integer primary key autoincrement,idTelegramChat real,pregunta text,estado integer default 1,
                      respuesta text default  '{"likes": [], "dislike": []}' )''')


    def crearTablabilleteraUsuarioGrupo(self):
        c = self.conexion.cursor()
        c.execute('''CREATE TABLE billeteraUsuarioGrupo
                              (id integer primary key autoincrement,idTelegram real,fkGrupo real,pllave text,sllave text)''')

    def crearTablabilleteraGrupo(self):
        c = self.conexion.cursor()
        c.execute('''CREATE TABLE billeteraGrupo
                     (idGrupo real,pllave text,sllave text,integrantes real,primary key("idGrupo"))''')


    def actualizaciones(self):
        try:
            self.crearTablaUsuarios()
        except sqlite3.OperationalError as e:
            pass
        try:
            self.crearTablaUsuariosAssets()
        except sqlite3.OperationalError as e:
            pass
        try:
            self.crearTablaEncuestaGrupal()
        except sqlite3.OperationalError as e:
            pass
        try:
            self.crearTablabilleteraUsuarioGrupo()
        except sqlite3.OperationalError as e:
            pass
        try:
            self.crearTablabilleteraGrupo()
        except sqlite3.OperationalError as e:
            pass

