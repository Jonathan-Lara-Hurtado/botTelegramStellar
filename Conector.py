import sqlite3
from stellar_sdk import Keypair, Server, exceptions,Account,TransactionBuilder,Network,Signer
import qrcode



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
            tmpBalance = 0
            for balance in cuenta['balances']:
                tmpBalance = balance['balance']
        except exceptions.NotFoundError:
            tmpBalance = 0
        return float(tmpBalance)

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
                     (idTelegram real,pllave text,sllave text)''')

    def generarPar(self):
        keypair = Keypair.random()
        return [keypair.public_key,keypair.secret]

    def insertarUsuario(self,usuario):
        llaves = self.generarPar()
        c = self.conexion.cursor()
        valores = [(usuario,llaves[0],llaves[1])]
        c.executemany('Insert Into billeteras values (?,?,?)',valores)
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
