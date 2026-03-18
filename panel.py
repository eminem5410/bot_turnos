import sqlite3
from flask import Flask

app = Flask(__name__)

def obtener_turnos():

    conn = sqlite3.connect("turnos.db")
    cursor = conn.cursor()

    cursor.execute("SELECT servicio, fecha, hora, nombre FROM turnos")

    turnos = cursor.fetchall()

    conn.close()

    return turnos


@app.route("/")
def inicio():

    turnos = obtener_turnos()

    html = """
    <h1>Panel de Turnos</h1>

    <table border="1" cellpadding="10">
    <tr>
    <th>Fecha</th>
    <th>Hora</th>
    <th>Cliente</th>
    <th>Servicio</th>
    </tr>
    """

    for t in turnos:

        html += f"""
        <tr>
        <td>{t[1]}</td>
        <td>{t[2]}</td>
        <td>{t[3]}</td>
        <td>{t[0]}</td>
        </tr>
        """

    html += "</table>"

    return html


app.run(host="0.0.0.0", port=5000)