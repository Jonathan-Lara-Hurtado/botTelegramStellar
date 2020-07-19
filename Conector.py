import sqlite3
from stellar_sdk import Keypair, Server, exceptions,Account,TransactionBuilder,Network,Signer
import qrcode
from aiogram import md
from Encriptacion import Seguridad

class Stellar:
    def __init__(self,pLlave = '', sLlave='',horizon=True):
        self.pLlave = pLlave
        self.sLlave = sLlave
        if horizon:
            self.Horizon_url = "https://horizon.stellar.org"
            self.networkTrabajar = Network.PUBLIC_NETWORK_PASSPHRASE
        else:
            self.Horizon_url = "https://horizon-testnet.stellar.org"
            self.networkTrabajar = Network.TESTNET_NETWORK_PASSPHRASE

    def balance(self):
        pLlave = self.pLlave
        try:
            server = Server(horizon_url=self.Horizon_url)
            cuenta = server.accounts().account_id(pLlave).call()
            resultado = []
            texto = "Balances:\n"
            if len(cuenta['balances']) >1:
                for balance in cuenta['balances']:
                    if balance['asset_type'] == 'native':
                        texto += ("XML = "+str(balance['balance']))
                    else:
                        texto += (str(balance['asset_code'])+" = "+str(balance['balance'])+"\n")
            else:
                texto += "XLM ="+str(cuenta['balances'][0]['balance'])

            resultado.append(True)
            resultado.append(texto)
            return resultado
        except exceptions.NotFoundError:
            texto = "su cuenta no esta activa"
            return [False,texto]

    def informacionAssets(self):
        pLlave = self.pLlave
        try:
            texto = "Assets\n➖➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            #asset_issuer=""
            server = Server(horizon_url=self.Horizon_url)
            cuenta = server.accounts().account_id(pLlave).call()
            for i in cuenta['balances']:
                if i['asset_type'] != "native":
                    asset_issuer = i['asset_issuer']
                    texto += ("Asset Code:"+i['asset_code']+"\n")
                    texto += ("Limit:"+i['limit']+"\n")
                    Assets = server.assets().for_code(i['asset_code']).for_issuer(asset_issuer).call()
                    for e in Assets['_embedded']['records']:
                        texto += ("Amount:"+str(e['amount']))
                        texto += ("\nNum Accounts:"+str(e['num_accounts']))
                        texto +=("\n➖➖➖➖➖➖➖➖➖➖➖➖➖➖\n")
            return texto
        except:
            return "Sorry you have not created any assets, please click the button (Create Assets)"

    def assetsActivo(self,direccionEmisor,codigo):
        pLlave = self.pLlave
        try:
            server = Server(horizon_url=self.Horizon_url)
            cuenta = server.accounts().account_id(pLlave).call()
            resultado = False
            for balance in cuenta['balances']:
                if balance['asset_type'] != 'native':
                    if balance['asset_code'] == codigo and balance['asset_issuer'] == direccionEmisor:
                        resultado = True
        except exceptions.NotFoundError:
            return resultado

        return resultado

    def verificarCuentaActivada(self,destino):
        server = Server(horizon_url=self.Horizon_url)
        try:
            transactions = server.load_account(account_id=destino)
            return [True, transactions]
        except exceptions.NotFoundError as e:
            return [False, e]

    def pagoSinMemo(self,Destino,monto):
        validarCuenta = self.verificarCuentaActivada(destino=Destino)
        if validarCuenta[0]:
            server = Server(horizon_url=self.Horizon_url)
            root_keypair = Keypair.from_secret(self.sLlave)
            root_account = server.load_account(account_id=root_keypair.public_key)
            base_fee = server.fetch_base_fee()
            transaction = TransactionBuilder(
                source_account=root_account,
                network_passphrase=self.networkTrabajar,
                base_fee=base_fee) \
                .append_payment_op(  # add a payment operation to the transaction
                destination=Destino,
                asset_code="XLM",
                amount=str(monto)) \
                .set_timeout(30) \
                .build()  # mark this transaction as valid only for the next 30 seconds
            transaction.sign(root_keypair)
            try:
                response = server.submit_transaction(transaction)
                return [True,response]
            except exceptions.BadRequestError as d:
                #print(d)
                return [False,d]
        else:
            server = Server(horizon_url=self.Horizon_url)
            root_keypair = Keypair.from_secret(self.sLlave)
            root_account = server.load_account(account_id=root_keypair.public_key)
            base_fee = server.fetch_base_fee()
            transaction = TransactionBuilder(
                source_account=root_account,
                network_passphrase=self.networkTrabajar,
                base_fee=base_fee) \
                .append_create_account_op(destination=Destino, starting_balance=str(monto)) \
                .build()  # mark this transaction as valid only for the next 30 seconds

            transaction.sign(root_keypair)
            try:
                response = server.submit_transaction(transaction)
                return [True, response]
            except exceptions.BadRequestError as d:
                return [False, d]

    def configurarBilleteraPrimeraVez(self,listaUsuarios,umbralLista):
        server = Server(horizon_url=self.Horizon_url)
        root_keypair = Keypair.from_secret(self.sLlave)
        root_account = server.load_account(account_id=root_keypair.public_key)
        base_fee = server.fetch_base_fee()

        transaction = TransactionBuilder(
            base_fee=base_fee,
            network_passphrase=self.networkTrabajar,
            source_account=root_account)\
            .append_set_options_op(master_weight=1,
                                low_threshold=int(umbralLista[1])-1,
                                med_threshold=int(umbralLista[1]),
                                high_threshold=int(umbralLista[0]))\
            .set_timeout(30)
        for i in listaUsuarios:
            transaction.append_ed25519_public_key_signer(account_id=i[3],weight=1)

        transaction = transaction.build()
        transaction.sign(root_keypair)
        try:
            response = server.submit_transaction(transaction)
            return [True, response]
        except exceptions.BadRequestError as d:
            return [False, d]
        except exceptions.NotFoundError as n:
            return [False,n]

    def assetsPosibles(self):
        pLlave = self.pLlave
        try:
            AssetsPosibles = []
            server = Server(horizon_url=self.Horizon_url)
            cuenta = server.accounts().account_id(pLlave).call()
            #Assets no creados por el
            for i in cuenta['balances']:
                if i['asset_type'] != 'native':
                    AssetsPosibles.append((i['asset_code'],i['asset_issuer']))
            # Assets no creados por el
            try:
                Assets = server.assets().for_issuer(pLlave).call()

                for e in Assets['_embedded']['records']:
                    if not self.busqueda(AssetsPosibles,e['asset_code'],e['asset_issuer']):
                        AssetsPosibles.append((e['asset_code'],e['asset_issuer']))
            except:
                pass

            texto = md.text(md.bold("Seleccione un numero Assets:")) + "\n➖➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            contador = 0
            for i in AssetsPosibles:
                texto += (md.text(md.bold(str(contador))) + ". Assets Code: " + md.text(
                    md.code(str(i[0]))) + "\n   Asset Issuer:" + md.text(md.code(str(i[1]))) + "\n")
                texto += ("\n➖➖➖➖➖➖➖➖➖➖➖➖➖➖\n")
                contador += 1

            return [texto, AssetsPosibles, contador]
        except:
            print("error")
            return []


    def busqueda(self,l,codigo,asset_issuer):
        existe = False
        for i in l:
            if i[0] == codigo and i[1] == asset_issuer:
                existe = True
        return existe


    def pagoAssets(self,Destino,monto,codigo,asset_usuario):
        server = Server(horizon_url=self.Horizon_url)
        root_keypair = Keypair.from_secret(self.sLlave)
        root_account = server.load_account(account_id=root_keypair.public_key)
        base_fee = server.fetch_base_fee()
        transaction = TransactionBuilder(
            source_account=root_account,
            network_passphrase=self.networkTrabajar,
            base_fee=base_fee) \
            .append_payment_op(  # add a payment operation to the transaction
            destination=Destino,
            asset_code=str(codigo),
            amount=str(monto),
            asset_issuer=asset_usuario) \
            .set_timeout(30) \
            .build()  # mark this transaction as valid only for the next 30 seconds
        transaction.sign(root_keypair)
        try:
            response = server.submit_transaction(transaction)
            return [True, response]
        except exceptions.BadRequestError as d:
            # print(d)
            return [False, d]


    def pagoEncuesta(self,Destino,monto,firmantes):
        validarCuenta = self.verificarCuentaActivada(destino=Destino)
        if validarCuenta[0]:
            server = Server(horizon_url=self.Horizon_url)
            root_keypair = Keypair.from_secret(self.sLlave)
            root_account = server.load_account(account_id=root_keypair.public_key)
            base_fee = server.fetch_base_fee()
            transaction = TransactionBuilder(
                source_account=root_account,
                network_passphrase=self.networkTrabajar,
                base_fee=base_fee) \
                .append_payment_op(  # add a payment operation to the transaction
                destination=Destino,
                asset_code="XLM",
                amount=str(monto)) \
                .set_timeout(30) \
                .build()  # mark this transaction as valid only for the next 30 seconds
#            transaction.sign(root_keypair)
            for i in firmantes:
                transaction.sign(Keypair.from_secret(i))
            try:
                response = server.submit_transaction(transaction)
                return [True, response]
            except exceptions.BadRequestError as d:
                # print(d)
                return [False, d]

        else:
            server = Server(horizon_url=self.Horizon_url)
            root_keypair = Keypair.from_secret(self.sLlave)
            root_account = server.load_account(account_id=root_keypair.public_key)
            base_fee = server.fetch_base_fee()
            transaction = TransactionBuilder(
                source_account=root_account,
                network_passphrase=self.networkTrabajar,
                base_fee=base_fee) \
                .append_create_account_op(destination=Destino,starting_balance=str(monto))\
                .set_timeout(30)\
                .build()
#            transaction.sign(root_keypair)
            for i in firmantes:
                transaction.sign(Keypair.from_secret(i))
            try:
                response = server.submit_transaction(transaction)
                return [True, response]
            except exceptions.BadRequestError as d:
                # print(d)
                return [False, d]

    def crearAssets(self,codigo,monto,emisor):
        server = Server(horizon_url=self.Horizon_url)
        root_keypair = Keypair.from_secret(self.sLlave)
        root_account = server.load_account(account_id=root_keypair.public_key)
        transaction = TransactionBuilder(
            source_account=root_account,
            network_passphrase=self.networkTrabajar,
            base_fee=100).append_change_trust_op(
            limit=monto,
            asset_code=str(codigo),
            asset_issuer=emisor
        ).build()
        transaction.sign(root_keypair)
        try:
            response = server.submit_transaction(transaction)
            return [True, response]
        except exceptions.BadRequestError as d:
            return [False, d]

    def agregarEmisorToken(self,emisor,codigo):
        server = Server(horizon_url=self.Horizon_url)
        root_keypair = Keypair.from_secret(self.sLlave)
        root_account = server.load_account(account_id=root_keypair.public_key)
        transaction = TransactionBuilder(
            source_account=root_account,
            network_passphrase=self.networkTrabajar,
            base_fee=100
        ).append_change_trust_op(
            asset_code=str(codigo),
            asset_issuer=emisor,
        ).build()
        transaction.sign(root_keypair)
        try:
            response = server.submit_transaction(transaction)
            return [True, response]
        except exceptions.BadRequestError as d:
            return [False, d]

    def pagoConMemo(self,Destino,monto,memo):
        validarCuenta = self.verificarCuentaActivada(destino=Destino)
        if validarCuenta[0]:
            server = Server(horizon_url=self.Horizon_url)
            root_keypair = Keypair.from_secret(self.sLlave)
            root_account = server.load_account(account_id=root_keypair.public_key)
            transaction = TransactionBuilder(
                source_account=root_account,
                network_passphrase=self.networkTrabajar,
                base_fee=100) \
                .add_text_memo(memo) \
                .append_payment_op(  # add a payment operation to the transaction
                destination=Destino,
                asset_code="XLM",
                amount=str(monto)) \
                .set_timeout(30) \
                .build()  # mark this transaction as valid only for the next 30 seconds
            transaction.sign(root_keypair)
            try:
                response = server.submit_transaction(transaction)
                return [True,response]
            except exceptions.BadRequestError as d:
                return [False,d]
        else:
            server = Server(horizon_url=self.Horizon_url)
            root_keypair = Keypair.from_secret(self.sLlave)
            root_account = server.load_account(account_id=root_keypair.public_key)
            base_fee = server.fetch_base_fee()
            transaction = TransactionBuilder(
                source_account=root_account,
                network_passphrase=self.networkTrabajar,
                base_fee=base_fee) \
                .add_text_memo(memo) \
                .append_create_account_op(destination=Destino, starting_balance=str(monto)) \
                .build()  # mark this transaction as valid only for the next 30 seconds
            transaction.sign(root_keypair)
            try:
                response = server.submit_transaction(transaction)
                return [True, response]
            except exceptions.BadRequestError as d:
                return [False, d]


class Conexion:
    def __init__(self,db='billeteras.db'):
        self.conexion = sqlite3.connect(db)

    def crearTablaUsuarios(self):
        c = self.conexion.cursor()
        c.execute('''CREATE TABLE billeteras
                     (idTelegram real,pllave text,sllave text,CuentaEncriptada INTEGER default 0)''')

    def addColumnaEncriptacion(self):
        c = self.conexion.cursor()
        c.execute('''ALTER TABLE billeteras ADD CuentaEncriptada INTEGER default 0''')

    def generarPar(self):
        keypair = Keypair.random()
        return [keypair.public_key,keypair.secret]

    def insertarUsuario(self,usuario):
        llaves = self.generarPar()
        c = self.conexion.cursor()
        valores = [(usuario,llaves[0],llaves[1])]
        c.executemany('Insert Into billeteras(idTelegram,pllave,sllave) values (?,?,?)',valores)
        self.conexion.commit()

    def misDatos(self,usuario):
        c = self.conexion.cursor()
        query = "select * from billeteras where idTelegram="+str(usuario)
        p = c.execute(query)
        lista = list()
        for i in p:
            for e in i:
                lista.append(e)
        return lista

    def cuentaEncriptada(self,usuario):
        c = self.conexion.cursor()
        query = "select CuentaEncriptada from billeteras where idTelegram="+str(usuario)
        p = c.execute(query)
        if p.fetchall()[0][0] == 0:
            return False
        else:
            return True

    def encriptarSecretKeyCuentaBD(self,usuario,contrasena):
        tmpDatos = self.misDatos(usuario)
        seguridad = Seguridad()
        llaveEncriptada = seguridad.encriptarLlaveSecreta(str(contrasena),tmpDatos[2])
        c = self.conexion.cursor()
        query = "Update billeteras set sllave = '"+str(llaveEncriptada.decode())+"' , CuentaEncriptada=1" \
                                                                                 " where idTelegram="+str(usuario)
        c.execute(query)
        self.conexion.commit()




def validarLlavePublica(llave):
    try:
        f = Keypair.from_public_key(llave)
        return True
    except exceptions.Ed25519PublicKeyInvalidError:
        return False


def validarLlaveSecreta(llave):
    try:
        f = Keypair.from_secret(llave)
        return True
    except exceptions.Ed25519SecretSeedInvalidError:
        return False
