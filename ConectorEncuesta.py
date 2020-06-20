import sqlite3
import json

class ConexionEncuesta:
    def __init__(self, db='billeteras.db'):
        self.conexion = sqlite3.connect(db)

    def crearTablaEncuestaGrupal(self):
        c = self.conexion.cursor()
        c.execute('''CREATE TABLE Encuesta
                     (idEncuesta integer primary key autoincrement,idTelegramChat real,pregunta text,estado integer default 1,
                      respuesta text default  '{"likes": [], "dislike": []}' )''')


    def crearEncuesta(self,chatID,pregunta):
        c = self.conexion.cursor()
        valores = [(chatID,pregunta)]
        c.executemany('Insert into Encuesta (idTelegramChat,pregunta) values (?,?)',valores)
        self.conexion.commit()

    def actualizarLike(self,idEncuesta,datos):
        c = self.conexion.cursor()
        valores = [(datos,idEncuesta)]
        c.executemany('Update Encuesta set Respuesta = ? where idEncuesta=?',valores)
        self.conexion.commit()



    def terminarEncuesta(self,chatID):
        c = self.conexion.cursor()
        valores =[(0,chatID)]
        c.executemany("update Encuesta set estado=? where idTelegramChat=?",valores)
        self.conexion.commit()


    def EncuestaActiva(self,chatId):
        c = self.conexion.cursor()
        query = "select * from Encuesta where idTelegramChat=" + str(chatId) +" and estado = 1"
        p = c.execute(query)
        lista = list()
        for i in p:
            for e in i:
                lista.append(e)
        return lista

    def miembrosGrupo(self,chatId):
        c = self.conexion.cursor()
        query = "Select * from billeteraUsuarioGrupo where fkGrupo="+str(chatId)
        p = c.execute(query)
        lista = list()
        for i in p:
            lista.append(i)
        return lista


def verificarVoto(votosEncuesta,user):
    if user in votosEncuesta['likes'] or user in votosEncuesta['dislike']:
        return True
    else:
        return False

def jsonDireccionPregunta(direccion,Pregunta,Monto):
    data_set = {"Direccion": direccion,
                "Pregunta": Pregunta,
                "Monto": Monto}
    informacion = json.dumps(data_set)
    return informacion

#c = ConexionEncuesta()

