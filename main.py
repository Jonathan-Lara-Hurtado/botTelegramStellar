
#region configuracion


#region configEncuesta
from BaseDatos import BaseDatos
from ConectorEncuesta import verificarVoto,ConexionEncuesta,jsonDireccionPregunta
from ConectorAssets import ConexionAssets
from Encriptacion import Seguridad
from aiogram.utils.callback_data import CallbackData
from aiogram.utils import executor
from aiogram.types import ParseMode
from aiogram.dispatcher.filters import Text
import json
#endregion



import logging
from aiogram import Bot, Dispatcher, executor, types, md
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode
from aiogram.types import ContentType

import os


#libreria de tipos de chat

from aiogram.types import ChatType

#libreriaMia
from Conector import Conexion, Stellar,validarLlavePublica,validarLlaveSecreta
from ConectorGrupo import ConexionGrupo,darQrBuffer
#librerias para trabajar qr
import qrcode

#librerias para trabajar binariamente
from io import BytesIO,StringIO


#librerias para decodificar qr
from pyzbar.pyzbar import decode
from PIL import Image


#libreriasTraduccion
from pathlib import Path

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.i18n import I18nMiddleware
#archivo traduccion
I18N_DOMAIN = 'traduccionesbot'

#configuracion traduccion

BASE_DIR = Path(__file__).parent
LOCALES_DIR = BASE_DIR / 'locales'

# Setup i18n middleware
i18n = I18nMiddleware(I18N_DOMAIN, LOCALES_DIR)


# Alias for gettext method
_ = i18n.gettext

#metodosMios
def decodeQr(buf):
    byteImg = buf.read()
    return decode(Image.open(BytesIO(byteImg)))


API_TOKEN = ''
RedStellar = False

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN,parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(i18n)

#endregion

#region FormularioEncriptacion

class FormularioEncriptacion(StatesGroup):
    GuadarContrasena = State()
    Aceptacion = State()

#endregion

#region FormularioDesencriptarLlave
class FormularioDesencriptarLlave(StatesGroup):
    GuardarLlaveEncriptada = State()
    Desencriptar = State()
#endregion

#region FormularioCrearEncuesta

class FormularioEncuesta(StatesGroup):
    DireccionaPagar = State()
    Pregunta = State()
    montoEncuesta = State()

#endregion


#region CuerpoEncuesta
posts_cb = CallbackData('post', 'id', 'action')  # post:<id>:<action>

def formatoEncusta(post_id : int,estado : str) -> (str , types.InlineKeyboardMarkup):
    c = ConexionEncuesta()
    resultado = c.EncuestaActiva(post_id)
    Titulo = ""
    if resultado:
        Dictado = json.loads(resultado[2])
        Titulo = Dictado['Pregunta']
        Direccion =Dictado['Direccion']
        Monto = Dictado['Monto']
        post_id2 = resultado[0]
        votosEncuesta = json.loads(resultado[4])
        like = len(votosEncuesta['likes'])
        dislike = len(votosEncuesta['dislike'])
    else:
        post_id2 = -1
        like = 0
        dislike = 0


    text = md.text(
        md.hbold(Titulo),
        '',
        f"Address to pay:{md.hpre(Direccion)}",
        '',
        f"Amount to pay (XLM):{md.hpre(Monto)}",
        '',
        f"👍 = {like}",
        '',
        f"👎 = {dislike}",
        '',
        f"Status:{estado}",
        sep = '\n',
    )


    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton('👍', callback_data=posts_cb.new(id=post_id2, action='like')),
        types.InlineKeyboardButton('👎', callback_data=posts_cb.new(id=post_id2, action='dislike')),
        types.InlineKeyboardButton('Pay', callback_data=posts_cb.new(id=post_id2, action='Pago')),
        types.InlineKeyboardButton('Cancel', callback_data=posts_cb.new(id=post_id2, action='CancelarPago'))
    )

#    markup.add(types.InlineKeyboardButton('<< Back', callback_data=posts_cb.new(id='-', action='list')))
    return text, markup

#endregion


#region FormulariosPrivado


class Form(StatesGroup):
    direccion = State()
    monto = State()
    memo = State()
    memoAceptacion = State()
    aceptacion = State()
    procesoPagoPass=State()


class Ajustes(StatesGroup):
    exportar = State()
#endregion


#region FormularioGrupalMultisignature
class FormularioMultignature(StatesGroup):
    multisingAceptacion = State()
    umbralAlto =State()
    umbralMedio =State()
    confirmacion = State()

#endregion

#region FormularioAssets
class FormularioAssetsMenu(StatesGroup):
    seleccionMenuAssets= State()

class FormularioAgregarAssets(StatesGroup):
    aceptacionTerminos = State()
    codigoAssets = State()
    direccionEmisor = State()

class FormularioCrearAssets(StatesGroup):
    aceptacionTerminos = State()
    nombreAssets = State()
    cantidadAssets = State()


class FormularioPagoAssets(StatesGroup):
    direcion = State()
    codigoAssets = State()
    montoAssets = State()
    aceptacionAssets =State ()
#    precesoPagoAssets = ()

#endregion


#region TecladosChatGrupal
def dar_keyboardPrincipalGrupo() -> types.ReplyKeyboardMarkup:
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=2)
    btn_texto = ('Receive', 'Pay','Balance', 'Multisignature Configuration')
    keyboard_markup.add(*(types.KeyboardButton(text) for text in btn_texto))
    return keyboard_markup

def dar_keyboardSiguienteCancelar() -> types.ReplyKeyboardMarkup:
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=2)
    btn_texto = ('Accept','Cancel')
    keyboard_markup.add(*(types.KeyboardButton(text) for text in btn_texto))
    return keyboard_markup

def dar_keyboardCancelarMaquina() -> types.ReplyKeyboardMarkup:
    keyboard_markup = types.ReplyKeyboardMarkup()
    keyboard_markup.add(types.KeyboardButton('Cancel'))
    return keyboard_markup

#endregion


#region TecladosChatPrivado
def dar_keyboardSettings() -> types.ReplyKeyboardMarkup:
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=2)
    btn_texto = ('Back','Export','Decrypt Wallet')
    keyboard_markup.add(*(types.KeyboardButton(text) for text in btn_texto))
    return keyboard_markup


def dar_keyboardMenuPrincipal() -> types.ReplyKeyboardMarkup:
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=2)
    btn_texto = (_('⬇️Receive'), _('⬆️Pay'), _('📊 Balance'), _('🛠 Settings'),('💵 Assets'))
    keyboard_markup.add(*(types.KeyboardButton(text) for text in btn_texto))
    return keyboard_markup


def dar_keyboardSiNo() -> types.ReplyKeyboardMarkup:
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=2)
    btn_texto = ('Yes', 'No')
    keyboard_markup.add(*(types.KeyboardButton(text) for text in btn_texto))
    return keyboard_markup


def dar_keyboardPago() -> types.ReplyKeyboardMarkup:
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=2)
    btn_texto = ('Atras', 'Comerzar')
    keyboard_markup.add(*(types.KeyboardButton(text) for text in btn_texto))
    return keyboard_markup


def dar_keyboardAceptacionPago() -> types.ReplyKeyboardMarkup:
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=2)
    btn_texto = ('Accept', 'Cancel')
    keyboard_markup.add(*(types.KeyboardButton(text) for text in btn_texto))
    return keyboard_markup


def dar_keyboardCancelacion() -> types.ReplyKeyboardMarkup:
    keyboard_markup = types.ReplyKeyboardMarkup()
    keyboard_markup.add(types.KeyboardButton('Cancel'))
    return keyboard_markup


def dar_keyboardAssets()-> types.ReplyKeyboardMarkup:
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=2)
    btn_texto = ('back','⏬ Add Assets' ,'📄 Create Assets','⏫ Pay Assets','🗒 List of assets created')
    keyboard_markup.add(*(types.KeyboardButton(text) for text in btn_texto))
    return keyboard_markup

#endregion


#region comandosInicio

@dp.message_handler(commands=['start', 'inicio', 'debut'])
async def inicioAplicacion(message: types.Message):
    #region Privado

    if message.chat.type == ChatType.PRIVATE:
        conexion = Conexion()
        resultado = conexion.misDatos(message.from_user.id)
        if resultado:
            buf = BytesIO()
            qr = qrcode.QRCode(version=1,
                               error_correction=qrcode.constants.ERROR_CORRECT_L,
                               box_size=6,
                               border=2)
            qr.add_data(resultado[1])
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(buf, "PNG")
            textoFinal = "Direccion Lumen: " + resultado[1]
            await message.reply_photo(buf.getvalue(), caption=textoFinal, reply_markup=dar_keyboardMenuPrincipal())
        else:
            conexion.insertarUsuario(message.from_user.id)
            tmpResultado = conexion.misDatos(message.from_user.id)
            buf = BytesIO()
            qr = qrcode.QRCode(version=1,
                               error_correction=qrcode.constants.ERROR_CORRECT_L,
                               box_size=6,
                               border=2)
            qr.add_data(tmpResultado[1])
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(buf, "PNG")
            textoFinal = "Direccion Lumen: " + tmpResultado[1]
            await message.reply_photo(buf.getvalue(), caption=textoFinal, reply_markup=dar_keyboardMenuPrincipal())
    #endregion
    elif message.chat.type == ChatType.GROUP or message.chat.type == ChatType.SUPER_GROUP:
        c = ConexionGrupo()
        resultado = c.misDatosGrupo(message.chat.id)
        if resultado:
            imgQr = darQrBuffer(resultado[1])
            await message.answer_photo(imgQr.getvalue(),caption="Address:"+resultado[1],reply_markup=dar_keyboardPrincipalGrupo())
        else:
            c.insertarLlavesGrupo(message.chat.id)
            tmpResultado = c.misDatosGrupo(message.chat.id)
            imgQr = darQrBuffer(tmpResultado[1])
            await message.answer_photo(imgQr.getvalue(), caption="Address:" + tmpResultado[1],
                                       reply_markup=dar_keyboardPrincipalGrupo())
    else:
        await message.answer("Coming soon",reply_markup=types.ReplyKeyboardRemove())
#endregion



def isAdminChat(listaAdmin,user):
    respuesta = False
    for i in listaAdmin:
        if i.user.id == user:
            respuesta= True
    return respuesta

#region Eco

@dp.message_handler()
async def eco(message: types.Message):
    #region Privado

    if message.chat.type == ChatType.PRIVATE:
        #aqui pregunto si antes de utilizar si su llaveSecreta se encuentra encriptada
        tmpConexion= Conexion()
        if tmpConexion.cuentaEncriptada(message.from_user.id):
            if message.text == "⬆️Pay" or message.text == "Pago":
                tmpConexion = Conexion()
                resultado = tmpConexion.misDatos(message.from_user.id)
                tmpStellar = Stellar(pLlave=resultado[1], sLlave=resultado[2], horizon=RedStellar)
                balance = tmpStellar.balance()
                if balance[0]:
                    await Form.direccion.set()
                    await message.answer("Enter the address to pay (Qr Photo or text):",reply_markup=dar_keyboardCancelacion())
                else:
                    await message.answer("Unverfied account or insufficient balance")
            elif message.text == "📊 Balance" or message.text == "Saldo":
                tmpConexion = Conexion()
                resultado = tmpConexion.misDatos(message.from_user.id)
                tmpStellar = Stellar(pLlave=resultado[1], sLlave=resultado[2],horizon=RedStellar)
                balance = tmpStellar.balance()
                if balance[0]:
                    await message.answer(balance[1])
                else:
                    await message.answer("Your address does not have the required minimum lumens \ n Deposit 1 lumen")

            elif message.text == "⬇️Receive" or message.text == "Recibir":
                tmpConexion = Conexion()
                resultado = tmpConexion.misDatos(message.from_user.id)
                buf = BytesIO()
                qr = qrcode.QRCode(version=1,
                                   error_correction=qrcode.constants.ERROR_CORRECT_L,
                                   box_size=6,
                                   border=2)
                qr.add_data(resultado[1])
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                img.save(buf, "PNG")
                textoFinal = resultado[1]
                await message.reply_photo(buf.getvalue(), caption=textoFinal)
            elif message.text == "🛠 Settings":
                await Ajustes.exportar.set()
                await message.answer("🕒",reply_markup=dar_keyboardSettings())

            elif message.text == "💵 Assets":
                await FormularioAssetsMenu.seleccionMenuAssets.set()
                await message.answer("🕒",reply_markup=dar_keyboardAssets())
            else:
                await message.reply("❌ invalid command",reply_markup=dar_keyboardMenuPrincipal())
        else:
            await FormularioEncriptacion.GuadarContrasena.set()
            await message.reply("Welcome, this is the encryption process of your secret key !!\n"
                                "This process is used to encrypt your secret key\n"
                                "at the end of this process only you will have access to it try not to forget it\n"
                                "then enter a password to start encryption:\n", reply_markup=dar_keyboardCancelacion())

    # endregion
    elif message.chat.type == ChatType.GROUP or message.chat.type == ChatType.SUPER_GROUP:
        lista = await message.chat.get_administrators()
        admin = isAdminChat(lista,message.from_user.id)
        if admin:
            c = ConexionGrupo()
            tmpResultado = c.misDatosGrupo(message.chat.id)
            s = Stellar('','',False)
            activo = s.verificarCuentaActivada(tmpResultado[1])
            if activo[0]:
                if message.text == "Receive":
                    imgQr = darQrBuffer(tmpResultado[1])
                    await message.answer_photo(imgQr.getvalue(), caption="Address:" + tmpResultado[1],
                                                   reply_markup=dar_keyboardPrincipalGrupo())
                elif message.text == "Multisignature Configuration":
                    texto ="📍Welcome to the group\n" \
                           "address settings:\n" \
                           "In this process the signers of the group\n" \
                           "wallet must have the role of group\n" \
                           "administrators, if you have already\n" \
                           " added all the participants press the\n" \
                           "accept button, if not then cancel\n" \
                           "the operation ‼️"
                    await FormularioMultignature.multisingAceptacion.set()
                    await message.reply(texto,reply_markup=dar_keyboardSiguienteCancelar())

                elif message.text == "Pay":
                    c = ConexionEncuesta()
                    r = c.EncuestaActiva(message.chat.id)
                    if r:
                        text, markup = formatoEncusta(message.chat.id,"Pending")
                        await message.reply("This chat has an active survey")
                        await message.reply(text, reply_markup=markup)
                    else:
                        await FormularioEncuesta.DireccionaPagar.set()
                        await message.reply("Welcome to a payment survey\n"
                                            "Enter the address to make payment(Text or Photo)",reply_markup=dar_keyboardCancelarMaquina())
                elif message.text == "Balance":
                    tmpStellar = Stellar(pLlave=tmpResultado[1], sLlave=tmpResultado[2], horizon=RedStellar)
                    balance = tmpStellar.balance()
                    if balance[0]:
                        await message.answer(balance[1])
                    else:
                        await message.answer("Your address does not have the required minimum lumens \ n Deposit 1 lumen")
                else:
                    await message.reply("Error command Invalid",reply_markup=dar_keyboardPrincipalGrupo())
            elif message.text =="Receive":
                imgQr = darQrBuffer(tmpResultado[1])
                await message.answer_photo(imgQr.getvalue(), caption="Address:" + tmpResultado[1],
                                           reply_markup=dar_keyboardPrincipalGrupo())
            elif message.text == "Pay" or message.text == "Balance" or message.text =="Multisignature Configuration":
                await message.answer("Your address does not have the required minimum lumens \ n Deposit 1 lumen")
            else:
                await message.reply("Error command Invalid",reply_markup=dar_keyboardPrincipalGrupo())
        else:
            await message.answer("Sorry commands only for group admins")
    else:
        await message.answer("Coming soon", reply_markup=dar_keyboardPrincipalGrupo())
#endregion

@dp.message_handler(Text(equals='Cancel', ignore_case=True), state=Form)
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer("Payment canceled ‼️", reply_markup=dar_keyboardMenuPrincipal())

#region MaquinaAjustes

@dp.message_handler(content_types=ContentType.TEXT,state=Ajustes.exportar)
async def process_exportar(message: types.Message, state: FSMContext):
    if message.text == "Export":
        tmpConexion = Conexion()
        datos = tmpConexion.misDatos(message.from_user.id)
        nombre = "/tmp/Llaves"+str(message.from_user.id)+".txt"
        with open(nombre,"w") as f:
            f.write("Public Key:"+datos[1])
            f.write("\nSecret Key:"+datos[2])
        archivo = types.InputFile(nombre)
        archivo.filename="RespaldoLlaves.txt"
        await message.reply_document(archivo)
        os.remove(nombre)
        await message.answer("🕒",reply_markup=dar_keyboardMenuPrincipal())
        await state.finish()
    elif message.text == "Decrypt Wallet":
        await FormularioDesencriptarLlave.GuardarLlaveEncriptada.set()
        await message.answer("Enter your encrypted Secret key:",reply_markup=dar_keyboardCancelarMaquina())
    elif message.text == "Back":
        await state.finish()
        await message.answer("🕒",reply_markup=dar_keyboardMenuPrincipal())
    else:
        await message.answer("Wrong decision Please select through the keyboard.")

#endregion

#region MaquinaPago

@dp.message_handler(content_types=ContentType.ANY,state=Form.direccion)
async def process_direccion(message: types.Message, state: FSMContext):
    if message.content_type == ContentType.PHOTO:
        file_id = message.photo[0].file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        buf = await bot.download_file(file_path)
        dataQr = decodeQr(buf)
        if dataQr:
            texto = dataQr[0][0].decode('utf-8')
            if validarLlavePublica(texto):
                async with state.proxy() as data:
                    data['direccion'] = texto
                buf.close()
                await Form.next()
                await message.answer("Enter Amount:")
            else:
                await message.answer("Invalid stellar address\n Try again or cancel")
#            await state.finish()
        else:
            buf.close()
            await Form.direccion.set()
            await message.reply("Invalid QR Try again or Cancel")
    elif message.content_type == ContentType.TEXT:
        if validarLlavePublica(message.text):
            async with state.proxy() as data:
                data['direccion'] = message.text
            await Form.next()
            await message.answer("Enter Amount:")
        else:
            await message.answer("Invalid stellar address\n Try again or cancel")



@dp.message_handler(state=Form.monto)
async def process_monto(message: types.Message, state: FSMContext):
    try:
        monto = float(message.text)
        async with state.proxy() as data:
            data['monto'] = monto
        await Form.next()
        await message.answer("Add Memo?",reply_markup=dar_keyboardSiNo())
    except ValueError:
        await message.answer("Please write a numerical number, not a string.!!")

@dp.message_handler(lambda message: message.text not in ["Yes", "No"], state=Form.memo)
async def process_memo_invalid(message: types.Message):
    return await message.reply("Wrong decision Please select through the keyboard.")


@dp.message_handler(state=Form.memo)
async def process_memo(message: types.Message, state: FSMContext):
    if message.text == "Yes":
        await Form.next()
        await message.answer("Enter Memo:",reply_markup=dar_keyboardCancelacion())
    elif message.text == "No":
        async with state.proxy() as data:
            data['memoAceptacion'] = 'NULO'
        await Form.aceptacion.set()
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('You want to make this payment!!'),
                md.text('Payment address:', md.bold(data['direccion'])),
                md.text('Amount:', md.code(data['monto'])),
                sep='\n',
            ),
            reply_markup=dar_keyboardAceptacionPago(),
            parse_mode=ParseMode.MARKDOWN,
        )



@dp.message_handler(state=Form.memoAceptacion)
async def process_memoAceptacion(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['memoAceptacion'] = message.text
    await Form.next()
    await bot.send_message(
        message.chat.id,
        md.text(
            md.text('You want to make this payment!!'),
            md.text('Payment address:', md.bold(data['direccion'])),
            md.text('Amount:', md.code(data['monto'])),
            md.text('Memo:',md.code(data['memoAceptacion'])),
            sep='\n',
        ),
        reply_markup=dar_keyboardAceptacionPago(),
        parse_mode=ParseMode.MARKDOWN,
    )




@dp.message_handler(lambda message: message.text not in ["Accept", "Cancel"], state=Form.aceptacion)
async def process_aceptacion_invalid(message: types.Message):
    return await message.reply("Wrong decision Please select through the keyboard.")



@dp.message_handler(state=Form.aceptacion)
async def process_aceptacion(message: types.Message, state: FSMContext):
    if message.text == "Accept":
        await message.answer("Enter your password to unlock your wallet:",reply_markup=types.ReplyKeyboardRemove())
        await Form.next()


@dp.message_handler(state=Form.procesoPagoPass)
async def process_procesoPagoPass(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['contrasena'] = message.text
    await message.delete()
    usuario = Conexion()
    resultado = usuario.misDatos(message.from_user.id)
    s = Seguridad()
    if data['memoAceptacion'] == "NULO":
        sllave = s.desEncriptarLlaveSecreta(data['contrasena'],resultado[2].encode())
        if sllave != False:
            tmpStellar = Stellar(pLlave=resultado[1], sLlave=sllave.decode(), horizon=RedStellar)
            pago = tmpStellar.pagoSinMemo(Destino=data['direccion'], monto=data['monto'])
            if pago[0]:
                await message.answer("Successful Payment 🚀", reply_markup=dar_keyboardMenuPrincipal())
                await state.finish()
            else:
                await message.answer("Failed Payment ‼️", reply_markup=dar_keyboardMenuPrincipal())
                await message.answer("📍 Possible mistakes:"
                                     "\n📌 without internet connection"
                                     "\n📌 Amount less than your balance")
                await state.finish()
        else:
            await state.finish()
            await message.answer("Invalid password error !!",reply_markup=dar_keyboardMenuPrincipal())
    else:
        sllave = s.desEncriptarLlaveSecreta(data['contrasena'], resultado[2].encode())
        if sllave != False:
            tmpStellar  = Stellar(pLlave=resultado[1],sLlave=sllave.decode(),horizon=RedStellar)
            pago = tmpStellar.pagoConMemo(Destino=data['direccion'],monto=data['monto'],memo=data['memoAceptacion'])
            if pago[0]:
                await message.answer("Successful Payment 🚀",reply_markup=dar_keyboardMenuPrincipal())
                await state.finish()
            else:
                await message.answer("Failed Payment ‼️",reply_markup=dar_keyboardMenuPrincipal())
                await message.answer("📍 Possible mistakes:"
                                     "\n📌 without internet connection"
                                     "\n📌 Amount less than your balance")
                await state.finish()
        else:
            await state.finish()
            await message.answer("Invalid password error !!", reply_markup=dar_keyboardMenuPrincipal())


#endregion


#regionMaquinaConfigMultisiganture

@dp.message_handler(Text(equals='Cancel', ignore_case=True), state=FormularioMultignature)
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer("Multisignature Configuration canceled ‼️", reply_markup=dar_keyboardPrincipalGrupo())

@dp.message_handler(content_types=ContentType.TEXT,state=FormularioMultignature.multisingAceptacion)
async def process_multisingAceptacion(message: types.Message, state: FSMContext):
    if message.text == "Accept":
        texto = "How many people does it take to modify the wallet?\n" \
                "(High Threshold)?"
        await FormularioMultignature.next()
        await message.reply(texto,reply_markup=dar_keyboardCancelarMaquina())

@dp.message_handler(content_types=ContentType.TEXT,state=FormularioMultignature.umbralAlto)
async def process_multisingumbralAlto(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['umbralAlto'] = message.text
    texto = "How many people does it take to approve a payment?" \
            "(Medium Threshold)?"
    await FormularioMultignature.next()
    await message.reply(texto,reply_markup=dar_keyboardCancelarMaquina())


@dp.message_handler(content_types=ContentType.TEXT,state=FormularioMultignature.umbralMedio)
async def process_multisingumbralMedio(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['umbralMedio'] = message.text
    texto = "You accept the following configuration:\n" \
            "High Threshold ="+data['umbralAlto']+"\n Medium Threshold ="+data['umbralMedio']
    await FormularioMultignature.next()
    await message.reply(texto,reply_markup=dar_keyboardSiNo())

@dp.message_handler(content_types=ContentType.TEXT,state=FormularioMultignature.confirmacion)
async def process_confirmacion(message: types.Message, state: FSMContext):
    decicion = message.text
    if decicion == "Yes":
        async with state.proxy() as data:
            pass
        datosUmbral =[]
        datosUmbral.append(data['umbralAlto'])
        datosUmbral.append(data['umbralMedio'])
        c = ConexionGrupo()
        cEncuesta = ConexionEncuesta()
        miembros = cEncuesta.miembrosGrupo(message.chat.id)
        lista = await message.chat.get_administrators()
        if miembros:
            pass
        else:
            c.insertarIntegrantesBilletera(lista, message.chat.id)
        misDatos = c.misDatosGrupo(message.chat.id)
        usuariosAdmin = c.obtenerListaIntegrantesGrupo(message.chat.id)
        s = Stellar(misDatos[1],misDatos[2],False)
        resultadoFinal = s.configurarBilleteraPrimeraVez(usuariosAdmin,datosUmbral)
        if resultadoFinal[0]:
            await state.finish()
            await message.answer("Your group wallet is set up", reply_markup=dar_keyboardPrincipalGrupo())
        else:
            await state.finish()
            await message.answer("Error your group wallet could not be configured", reply_markup=dar_keyboardPrincipalGrupo())
    elif decicion == "No":
        await state.finish()
        await message.answer("Multisignature Configuracion canceled ‼️", reply_markup=dar_keyboardPrincipalGrupo())
    else:
        await message.answer("Select any keyboard option",reply_markup=dar_keyboardSiNo())



#endregion


#region EstadosFormularioEncuesta


@dp.message_handler(Text(equals='Cancel', ignore_case=True), state=FormularioEncuesta)
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer("Poll Payment canceled ‼️", reply_markup=dar_keyboardPrincipalGrupo())


@dp.message_handler(content_types=ContentType.ANY,state=FormularioEncuesta.DireccionaPagar)
async def process_DireccionaPagar(message: types.Message, state: FSMContext):
    """
    Process user name
    """
    if message.content_type == ContentType.PHOTO:
        file_id = message.photo[0].file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        buf = await bot.download_file(file_path)
        dataQr = decodeQr(buf)
        if dataQr:
            texto = dataQr[0][0].decode('utf-8')
            if validarLlavePublica(texto):
                async with state.proxy() as data:
                    data['direccion'] = texto
                await FormularioEncuesta.next()
                await message.reply("Enter your question", reply_markup=dar_keyboardCancelarMaquina())
            else:
                await message.reply("Invalid address\n Try again (Text or Photo) or Cancel",
                                    reply_markup=dar_keyboardCancelarMaquina())
        else:
            buf.close()
            await message.reply("Invalid QR Try again or Cancel",
                                reply_markup=dar_keyboardCancelarMaquina())
    else:
        if validarLlavePublica(message.text):
            async with state.proxy() as data:
                data['direccion'] = message.text
            await FormularioEncuesta.next()
            await message.reply("Enter your question",reply_markup=dar_keyboardCancelarMaquina())
        else:
            await message.reply("Invalid address\n Try again (Text or Photo) or Cancel",reply_markup=dar_keyboardCancelarMaquina())

@dp.message_handler(state=FormularioEncuesta.Pregunta)
async def process_Pregunta(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['pregunta'] = message.text
    await FormularioEncuesta.next()
    await message.reply("Enter the amount:",reply_markup=dar_keyboardCancelarMaquina())

@dp.message_handler(state=FormularioEncuesta.montoEncuesta)
async def process_Pregunta(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        pass
    direccion = data['direccion']
    pregunta = data['pregunta']
    c = ConexionEncuesta()
    c.crearEncuesta(message.chat.id, jsonDireccionPregunta(direccion, str(pregunta), message.text))
    await message.answer("Survey Created",reply_markup=dar_keyboardPrincipalGrupo())
    text, markup = formatoEncusta(message.chat.id,"Pending")
    await message.reply(text, reply_markup=markup)
    await state.finish()



#endregion


#region eventosEncuesta



@dp.callback_query_handler(posts_cb.filter(action=['like', 'dislike']))
async def query_post_vote(query: types.CallbackQuery, callback_data: dict):
    try:
        await dp.throttle('vote',rate=1)
    except Throttled:
        return await query.answer('Too many requests.')

    c = ConexionEncuesta()
    resultado = c.EncuestaActiva(query.message.chat.id)
    idEncuesta = callback_data['id']
    usuario = query.from_user.id
    accion = callback_data['action']

    if resultado:
        if resultado[0] == int(idEncuesta):
            votosEncuesta = json.loads(resultado[4])
            if verificarVoto(votosEncuesta,usuario):
                await query.answer('You have already voted')
            else:
                if accion == "like":
                    votosEncuesta['likes'].append(usuario)
                    c.actualizarLike(resultado[0],json.dumps(votosEncuesta))
                    await query.answer("Adding Vote")
                    text, markup = formatoEncusta(resultado[1],"Pending")
                    await query.message.edit_text(text, reply_markup=markup)
                else:
                    votosEncuesta['dislike'].append(usuario)
                    c.actualizarLike(resultado[0],json.dumps(votosEncuesta))
                    await query.answer("Adding Vote")
                    text, markup = formatoEncusta(resultado[1],"Pending")
                    await query.message.edit_text(text, reply_markup=markup)
        else:
            await query.answer('This survey is already canceled')
    else:
        await query.answer('This survey is already canceled')




@dp.callback_query_handler(posts_cb.filter(action=['Pago']))
async def query_post_vote(query: types.CallbackQuery, callback_data: dict):
    try:
        await dp.throttle('Paying',rate=1)
    except Throttled:
        return await query.answer('Too many requests.')
    c = ConexionEncuesta()
    r = c.EncuestaActiva(query.message.chat.id)
    idEncuesta = callback_data['id']
    if r:
        if r[0] == int(idEncuesta):
            c2 = ConexionGrupo()
            grupo = c2.misDatosGrupo(query.message.chat.id)
            miembros = c.miembrosGrupo(query.message.chat.id)
            tmp = []

            Dictado1 = json.loads(r[2])
            Dictado2 = json.loads(r[4])
            for i in miembros:
                for e in Dictado2['likes']:
                    if i[1] == e:
                        tmp.append(i[4])

            s = Stellar(grupo[1], grupo[2], False)
            resPago = s.pagoEncuesta(Destino=Dictado1['Direccion'],monto=Dictado1['Monto'],firmantes=tmp)
            if resPago[0]:
                text, markup = formatoEncusta(r[1], "Paid")
                await query.answer("Payment made")
                await query.message.edit_text(text, reply_markup=markup)
                c.terminarEncuesta(query.message.chat.id)
            else:
                await query.answer("Payment error")
        else:
            await query.answer('This survey is already canceled or paid')
    else:
        await query.answer('This survey is already canceled or paid')




@dp.callback_query_handler(posts_cb.filter(action=['CancelarPago']))
async def query_post_vote(query: types.CallbackQuery, callback_data: dict):
    try:
        await dp.throttle('Cancelando',rate=1)
    except Throttled:
        return await query.answer('Too many requests.')
    c = ConexionEncuesta()
    r = c.EncuestaActiva(query.message.chat.id)
    idEncuesta = callback_data['id']
    if r:
        if r[0] == int(idEncuesta):
            text, markup = formatoEncusta(r[1], "Cancelled")
            await query.answer('Canceling Survey')
            await query.message.edit_text(text, reply_markup=markup)
            c.terminarEncuesta(query.message.chat.id)
        else:
            await query.answer('This survey is already canceled')
    else:
        await query.answer('This survey is already canceled')


#endregion


#region maquinaSeleccionAssets

@dp.message_handler(Text(equals='Back', ignore_case=True), state=FormularioAssetsMenu)
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer("⬅ Back", reply_markup=dar_keyboardMenuPrincipal())


@dp.message_handler(state=FormularioAssetsMenu.seleccionMenuAssets)
async def seleccion_Menu(message: types.Message, state: FSMContext):
    if message.text == "📄 Create Assets":
        await message.reply("Do you want to create an asset?",reply_markup=dar_keyboardSiNo())
        await FormularioCrearAssets.aceptacionTerminos.set()
    elif message.text == "⏬ Add Assets":
        await message.reply("Do you want to add an asset to your main wallet?",reply_markup=dar_keyboardSiNo())
        await FormularioAgregarAssets.aceptacionTerminos.set()
    elif message.text == "⏫ Pay Assets":
        await message.reply("Enter the address to be paid the Asset (Photo or Text)",reply_markup=dar_keyboardCancelarMaquina())
        await FormularioPagoAssets.direcion.set()
    elif message.text == "🗒 List of assets created":
        tmpAssets = ConexionAssets()
        datosAssets = tmpAssets.misDatos(message.from_user.id)
        if datosAssets:
            tmpStellar = Stellar(datosAssets[1],datosAssets[2],False)
            resultado = tmpStellar.informacionAssets()
            await message.answer(resultado, reply_markup=dar_keyboardAssets())
        else:
            await message.answer("Sorry you have not created any assets, please click the button (Create Assets)")
    else:
        await message.answer("Select a keyboard option",reply_markup=dar_keyboardAssets())
#endregion


#region maquinaAddAssets

@dp.message_handler(Text(equals='Cancel', ignore_case=True), state=FormularioAgregarAssets)
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.reset_data()
    await FormularioAssetsMenu.seleccionMenuAssets.set()
    await message.answer("Cancel Add Assets",reply_markup=dar_keyboardAssets())


@dp.message_handler(state=FormularioAgregarAssets.aceptacionTerminos)
async def paso_Aceptacion(message: types.Message, state: FSMContext):
    if message.text == "Yes":
        await FormularioAgregarAssets.next()
        await message.reply("Enter the Asset Code",reply_markup=dar_keyboardCancelarMaquina())
    elif message.text == "No":
        await FormularioAssetsMenu.seleccionMenuAssets.set()
        await message.answer("🕒", reply_markup=dar_keyboardAssets())

    else:
        pass


@dp.message_handler(state=FormularioAgregarAssets.codigoAssets)
async def paso_CodigoAssets(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['codigoAssets'] = message.text
    await FormularioAgregarAssets.next()
    await message.reply("Enter the issuer address of the asset(Photo or Text)",reply_markup=dar_keyboardCancelarMaquina())


@dp.message_handler(content_types=ContentType.ANY, state=FormularioAgregarAssets.direccionEmisor)
async def paso_direccionEmisorAssets(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        pass
    codigoAsset = data['codigoAssets']

    if message.content_type == ContentType.PHOTO:
        file_id = message.photo[0].file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        buf = await bot.download_file(file_path)
        dataQr = decodeQr(buf)
        if dataQr:
            texto = dataQr[0][0].decode('utf-8')
            if validarLlavePublica(texto):
                tmpConexion = Conexion()
                resultado = tmpConexion.misDatos(message.from_user.id)
                tmpStellar = Stellar(resultado[1], resultado[2], False)
                tieneAssets = tmpStellar.assetsActivo(texto,codigoAsset)
                if tieneAssets:
                    await message.answer("Your account already has that asset !!", reply_markup=dar_keyboardAssets())
                    await state.reset_data()
                    await FormularioAssetsMenu.seleccionMenuAssets.set()
                else:
                    respuesta = tmpStellar.agregarEmisorToken(texto, codigoAsset)
                    if respuesta[0]:
                        await message.answer("Asset added", reply_markup=dar_keyboardAssets())
                        await state.reset_data()
                        await FormularioAssetsMenu.seleccionMenuAssets.set()
                    else:
                        await message.answer("Failed to add your asset", reply_markup=dar_keyboardAssets())
                        await state.reset_data()
                        await FormularioAssetsMenu.seleccionMenuAssets.set()
            else:
                await message.answer("Invalid stellar address\n Try again or cancel")
        else:
            buf.close()
            await Form.direccion.set()
            await message.reply("Invalid QR Try again or Cancel")
    elif message.content_type == ContentType.TEXT:
        if validarLlavePublica(message.text):
            tmpConexion = Conexion()
            resultado = tmpConexion.misDatos(message.from_user.id)
            tmpStellar = Stellar(resultado[1],resultado[2],False)
            tieneAssets = tmpStellar.assetsActivo(codigoAsset)
            if tieneAssets:
                await message.answer("Your account already has that asset !!", reply_markup=dar_keyboardAssets())
                await state.reset_data()
                await FormularioAssetsMenu.seleccionMenuAssets.set()
            else:
                respuesta = tmpStellar.agregarEmisorToken(message.text,codigoAsset)
                if respuesta[0]:
                    await message.answer("Asset added", reply_markup=dar_keyboardAssets())
                    await state.reset_data()
                    await FormularioAssetsMenu.seleccionMenuAssets.set()
                else:
                    await message.answer("Failed to add your asset", reply_markup=dar_keyboardAssets())
                    await state.reset_data()
                    await FormularioAssetsMenu.seleccionMenuAssets.set()
        else:
            await message.answer("Invalid stellar address\n Try again or cancel")
    else:
        pass



#endregion

#region maquinaCrearAssets

@dp.message_handler(Text(equals='Cancel', ignore_case=True), state=FormularioCrearAssets)
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.reset_data()
    await FormularioAssetsMenu.seleccionMenuAssets.set()
    await message.answer("Creation of Canceled Asset !!",reply_markup=dar_keyboardAssets())



@dp.message_handler(content_types=ContentType.ANY, state=FormularioCrearAssets.aceptacionTerminos)
async def paso_Aceptacion(message: types.Message, state: FSMContext):
    if message.text == "Yes":
        tmpConexion = ConexionAssets()
        datos = tmpConexion.misDatos(message.from_user.id)
        if datos:
            tmpStellar = Stellar(datos[1], datos[2], horizon=RedStellar)
            balance = tmpStellar.balance()
            if balance[0]:
                await FormularioCrearAssets.next()
                await message.reply("Enter the asset code", reply_markup=dar_keyboardCancelarMaquina())
            else:
                await FormularioAssetsMenu.seleccionMenuAssets.set()
                imgQr = darQrBuffer(datos[1])
                await FormularioAssetsMenu.seleccionMenuAssets.set()
                await message.answer_photo(imgQr.getvalue(), "Enter balance into your asset creation wallet to continue the process",
                                           reply_markup=dar_keyboardAssets())
        else:
            tmpConexion.insertarUsuario(message.from_user.id)
            direccion = tmpConexion.misDatos(message.from_user.id)
            imgQr = darQrBuffer(direccion[1])
            await FormularioAssetsMenu.seleccionMenuAssets.set()
            await message.answer_photo(imgQr.getvalue(), "Enter balance into your asset creation wallet to continue the process.",
                                       reply_markup=dar_keyboardAssets())
    elif message.text == "No":
        await FormularioAssetsMenu.seleccionMenuAssets.set()
        await message.answer("🕒", reply_markup=dar_keyboardAssets())
    else:
        await message.answer("Select a keyboard option",reply_markup=dar_keyboardSiNo())


@dp.message_handler(content_types=ContentType.ANY, state=FormularioCrearAssets.nombreAssets)
async def paso_nombreAssets(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['codigoAssets'] = message.text
    await FormularioCrearAssets.next()
    await message.answer("Enter the amount of assets to create",reply_markup=dar_keyboardCancelarMaquina())

@dp.message_handler(content_types=ContentType.ANY, state=FormularioCrearAssets.cantidadAssets)
async def paso_cantidadAssets(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        pass
    codigoAssets = data['codigoAssets']
    tmpConAssets = ConexionAssets()
    tmpConNormal = Conexion()
    datosEmisor = tmpConNormal.misDatos(message.from_user.id)
    datosAssets = tmpConAssets.misDatos(message.from_user.id)
    tmpStellar = Stellar(datosAssets[1],datosAssets[2],False)
    resultado = tmpStellar.crearAssets(codigoAssets,message.text,datosEmisor[1])
    if resultado[0]:
        await FormularioAssetsMenu.seleccionMenuAssets.set()
        await state.reset_data()
        await message.answer("Asset create",reply_markup=dar_keyboardAssets())
    else:
        await FormularioAssetsMenu.seleccionMenuAssets.set()
        await state.reset_data()
        await message.answer("Sorry Asset not created", reply_markup=dar_keyboardAssets())


#endregion


#region maquinaPagoAssets
@dp.message_handler(Text(equals='Cancel', ignore_case=True), state=FormularioPagoAssets)
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.reset_data()
    await FormularioAssetsMenu.seleccionMenuAssets.set()
    await message.answer("Cancel Pay Assets",reply_markup=dar_keyboardAssets())

@dp.message_handler(content_types=ContentType.ANY,state=FormularioPagoAssets.direcion)
async def paso_Direccion(message: types.Message, state: FSMContext):
    if message.content_type == ContentType.PHOTO:
        file_id = message.photo[0].file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        buf = await bot.download_file(file_path)
        dataQr = decodeQr(buf)
        if dataQr:
            texto = dataQr[0][0].decode('utf-8')
            if validarLlavePublica(texto):
                async with state.proxy() as data:
                    data['direccion'] = texto
                buf.close()
                tmpConexion = Conexion()
                datos = tmpConexion.misDatos(message.from_user.id)
                tmpStellar = Stellar(datos[1], datos[2], False)
                resultados = tmpStellar.assetsPosibles()
                async with state.proxy() as data:
                    data['resultados'] = resultados
                await FormularioPagoAssets.next()
                await message.answer(resultados[0], reply_markup=dar_keyboardCancelarMaquina(),
                                     parse_mode=ParseMode.MARKDOWN)
            else:
                await message.answer("Invalid stellar address\n Try again or cancel")
        #            await state.finish()
        else:
            buf.close()
            await message.reply("Invalid QR Try again or Cancel")
    elif message.content_type == ContentType.TEXT:
        if validarLlavePublica(message.text):
            tmpConexion = Conexion()
            datos = tmpConexion.misDatos(message.from_user.id)
            tmpStellar = Stellar(datos[1],datos[2],False)
            resultados = tmpStellar.assetsPosibles()
            async with state.proxy() as data:
                data['direccion'] = message.text
                data['resultados'] = resultados
            await FormularioPagoAssets.next()
            await message.answer(resultados[0],reply_markup=dar_keyboardCancelarMaquina(),parse_mode=ParseMode.MARKDOWN)
        else:
            await message.answer("Invalid stellar address\n Try again or cancel")

@dp.message_handler(state=FormularioPagoAssets.codigoAssets)
async def paso_codigoAssets(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            pass
        numero = int(message.text)
        if numero < int(data['resultados'][2]):
            async with state.proxy() as data:
                data["indiceAssets"]= numero
                await FormularioPagoAssets.next()
                await message.answer("Enter Amount:")
        else:
            await message.answer("Select a number from the list of the asset to pay")
    except:
        await message.answer("Select a number from the list of the asset to pay")


@dp.message_handler(state=FormularioPagoAssets.montoAssets)
async def paso_montoAssets(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['monto'] = message.text
    await FormularioPagoAssets.next()
    index = int(data['indiceAssets'])
    await bot.send_message(
            message.chat.id,
            md.text(
                md.text('You want to make this payment!!'),
                md.text('Payment address:', md.bold(data['direccion'])),
                md.text('Asset Code:', md.code(data['resultados'][1][index][0])),
                md.text('Asset Issuer:', md.code(data['resultados'][1][index][1])),
                md.text('Amount:',md.code(data['monto'])),
                sep='\n',
            ),
            reply_markup=dar_keyboardSiNo(),
            parse_mode=ParseMode.MARKDOWN,
        )

@dp.message_handler(state=FormularioPagoAssets.aceptacionAssets)
async def paso_aceptacionAssets(message: types.Message, state: FSMContext):
    if message.text == "Yes":
        async with state.proxy() as data:
            pass
        tmpConexion = Conexion()
        datos = tmpConexion.misDatos(message.from_user.id)
        tmpStellar = Stellar(datos[1],datos[2],False)
        index = int(data['indiceAssets'])
        estadoPago = tmpStellar.pagoAssets(data['direccion'],data['monto'],data['resultados'][1][index][0],data['resultados'][1][index][1])
        if estadoPago[0]:
            await state.reset_data()
            await FormularioAssetsMenu.seleccionMenuAssets.set()
            await message.answer("Successful Pay Assets", reply_markup=dar_keyboardAssets())
        else:
            await state.reset_data()
            await FormularioAssetsMenu.seleccionMenuAssets.set()
            await message.answer("Error Pay Assets", reply_markup=dar_keyboardAssets())
    elif message.text == "No":
        await state.reset_data()
        await FormularioAssetsMenu.seleccionMenuAssets.set()
        await message.answer("Cancel Pay Assets", reply_markup=dar_keyboardAssets())



#endregion


#region MaquinaEncriptarLlaveSecreta
@dp.message_handler(Text(equals='Cancel', ignore_case=True), state=FormularioEncriptacion)
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer("Canceling encryption process secret key",reply_markup=dar_keyboardMenuPrincipal())

@dp.message_handler(content_types=ContentType.TEXT,state=FormularioEncriptacion.GuadarContrasena)
async def paso_GuardarContrasena(message: types.Message, state: FSMContext):
    async  with state.proxy() as data:
        data['contrasena']= message.text
    await message.delete()
    await message.answer("Do you want to use this password?",reply_markup=dar_keyboardSiNo())
    await FormularioEncriptacion.next()

@dp.message_handler(content_types=ContentType.TEXT,state=FormularioEncriptacion.Aceptacion)
async def paso_Aceptacion(message: types.Message, state: FSMContext):
    if message.text == "Yes":
        async with state.proxy() as data:
            pass
        c = Conexion()
        c.encriptarSecretKeyCuentaBD(message.from_user.id,data['contrasena'])
        await state.finish()
        await message.answer("Congratulations, your secret key is already encrypted !!",reply_markup=dar_keyboardMenuPrincipal())
    elif message.text == "No":
        await FormularioEncriptacion.GuadarContrasena.set()
        await message.answer("Enter another password:",reply_markup=dar_keyboardCancelarMaquina())
    else:
        await message.answer("Select a keyboard option")


#endregion

#Region MaquinaDesEncriptarLlaveSecreta

@dp.message_handler(Text(equals='Cancel', ignore_case=True), state=FormularioDesencriptarLlave)
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer("Canceling the secret Wallet decryption process",reply_markup=dar_keyboardMenuPrincipal())

@dp.message_handler(content_types=ContentType.TEXT,state=FormularioDesencriptarLlave.GuardarLlaveEncriptada)
async def paso_GuardarLlave(message: types.Message, state: FSMContext):
    async  with state.proxy() as data:
        data['sLlave']= message.text
    await FormularioDesencriptarLlave.next()
    await message.answer("Enter your password")

@dp.message_handler(content_types=ContentType.TEXT,state=FormularioDesencriptarLlave.Desencriptar)
async def paso_Descriptar(message: types.Message, state: FSMContext):
    async  with state.proxy() as data:
        data['clave']= message.text
    await message.delete()
    s = Seguridad()
    resultado = s.desEncriptarLlaveSecreta(data['clave'],data['sLlave'].encode())
    if resultado:
        await state.finish()
        await message.answer(resultado.decode()+"\nNote: We recommend deleting this message !!",reply_markup=dar_keyboardMenuPrincipal())
    else:
        await state.finish()
        await message.answer("Invalid password error !!",reply_markup=dar_keyboardMenuPrincipal())



#endregion

if __name__ == '__main__':
    c = BaseDatos()
    c.actualizaciones()
    executor.start_polling(dp, skip_updates=True)