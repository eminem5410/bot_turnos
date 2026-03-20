import asyncio
import sqlite3
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

servicios = ["Corte", "Barba", "Corte + Barba"]

# -----------------------
# BASE DE DATOS
# -----------------------

def get_db():
    conn = sqlite3.connect("turnos.db")
    cursor = conn.cursor()
    return conn, cursor

conn, cursor = get_db()

cursor.execute("""
CREATE TABLE IF NOT EXISTS turnos (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
servicio TEXT,
fecha TEXT,
hora TEXT,
nombre TEXT,
recordatorio INTEGER DEFAULT 0
)
""")

conn.commit()
conn.close()

# -----------------------
# GENERADORES
# -----------------------

def generar_horarios():
    return [f"{h:02d}:00" for h in range(9, 20)]

def generar_fechas():
    fechas = []
    hoy = datetime.now()

    for i in range(7):
        dia = hoy + timedelta(days=i)
        fechas.append(dia.strftime("%d/%m"))

    return fechas

horarios = generar_horarios()

def keyboard(lista):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=i)] for i in lista],
        resize_keyboard=True
    )

# -----------------------
# RECORDATORIOS
# -----------------------

async def recordatorios():
    while True:

        conn, cursor = get_db()
        ahora = datetime.now()

        cursor.execute(
            "SELECT id, user_id, servicio, fecha, hora, nombre FROM turnos WHERE recordatorio=0"
        )

        turnos = cursor.fetchall()

        for t in turnos:
            turno_id, user_id, servicio, fecha, hora, nombre = t

            try:
                turno_datetime = datetime.strptime(
                    f"{fecha} {hora}",
                    "%d/%m %H:%M"
                )
            except:
                continue

            diferencia = turno_datetime - ahora

            # entre 5 y 60 minutos antes
            if 0 < diferencia.total_seconds() < 86400:

                texto = f"""
⏰ Recordatorio de turno

Hola {nombre}

Tenés un turno pronto.

Servicio: {servicio}
Hora: {hora}
"""

                try:
                    await bot.send_message(user_id, texto)

                    cursor.execute(
                        "UPDATE turnos SET recordatorio=1 WHERE id=?",
                        (turno_id,)
                    )
                    conn.commit()

                except Exception as e:
                    print("Error enviando recordatorio:", e)

        conn.close()
        await asyncio.sleep(60)

# -----------------------
# COMANDOS
# -----------------------

@dp.message(CommandStart())
async def start(message: types.Message):

    user_data[message.from_user.id] = {}

    await message.answer(
        "💈 *Barbería Demo*\n\nReservá tu turno en segundos.\n\nSelecciona un servicio:",
        parse_mode="Markdown",
        reply_markup=keyboard(servicios)
    )

@dp.message(Command("turnos"))
async def ver_turnos(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    conn, cursor = get_db()
    cursor.execute("SELECT servicio, fecha, hora, nombre FROM turnos")
    turnos = cursor.fetchall()
    conn.close()

    if not turnos:
        await message.answer("No hay turnos registrados.")
        return

    texto = "📅 Turnos reservados:\n\n"

    for t in turnos:
        texto += f"{t[1]} {t[2]} - {t[3]} ({t[0]})\n"

    await message.answer(texto)

@dp.message(Command("cancelar"))
async def cancelar_turnos(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    conn, cursor = get_db()
    cursor.execute("DELETE FROM turnos")
    conn.commit()
    conn.close()

    await message.answer("❌ Todos los turnos eliminados.")

# -----------------------
# FLUJO
# -----------------------

@dp.message()
async def flow(message: types.Message):

    uid = message.from_user.id
    text = message.text

    if uid not in user_data:
        user_data[uid] = {}

    data = user_data[uid]

    if "servicio" not in data:

        data["servicio"] = text

        await message.answer(
            "📅 Selecciona una fecha:",
            reply_markup=keyboard(generar_fechas())
        )
        return

    if "fecha" not in data:

        data["fecha"] = text

        await message.answer(
            "⏰ Selecciona un horario:",
            reply_markup=keyboard(horarios)
        )
        return

    if "hora" not in data:

        conn, cursor = get_db()

        cursor.execute(
            "SELECT * FROM turnos WHERE fecha=? AND hora=?",
            (data["fecha"], text)
        )

        ocupado = cursor.fetchone()
        conn.close()

        if ocupado:
            await message.answer(
                "⚠️ Ese horario ya está reservado.\nElegí otro:",
                reply_markup=keyboard(horarios)
            )
            return

        data["hora"] = text

        await message.answer(
            "👤 Escribe tu nombre para confirmar el turno:"
        )
        return

    if "nombre" not in data:

        data["nombre"] = text

        conn, cursor = get_db()

        cursor.execute(
            "INSERT INTO turnos (user_id, servicio, fecha, hora, nombre) VALUES (?, ?, ?, ?, ?)",
            (uid, data["servicio"], data["fecha"], data["hora"], data["nombre"])
        )

        conn.commit()
        conn.close()

        texto = f"""
✅ *Turno confirmado*

Servicio: {data['servicio']}
Fecha: {data['fecha']}
Hora: {data['hora']}
Cliente: {data['nombre']}
"""

        await message.answer(texto, parse_mode="Markdown")

        await bot.send_message(
            OWNER_ID,
            "📅 Nuevo turno reservado\n" + texto
        )

        user_data.pop(uid)

# -----------------------

async def main():
    asyncio.create_task(recordatorios())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())