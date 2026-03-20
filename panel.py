from flask import Flask, render_template_string, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "8748793286:AAGakkDbCaGE2dVh8XXOx7FzXzpTNdjR0Zs"

# 🔐 credenciales (después lo mejoramos)
USER = "admin"
PASS = "1234"

def get_turnos():
    conn = sqlite3.connect("turnos.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, servicio, fecha, hora, nombre FROM turnos")
    data = cursor.fetchall()
    conn.close()
    return data

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("user")
        password = request.form.get("password")

        if user == USER and password == PASS:
            session["login"] = True
            return redirect("/panel")

    return """
    <h2>Login Admin</h2>
    <form method="post">
        Usuario: <input name="user"><br>
        Password: <input name="password" type="password"><br>
        <button>Entrar</button>
    </form>
    """

@app.route("/panel")
def panel():
    if not session.get("login"):
        return redirect("/")

    turnos = get_turnos()

    html = "<h2>Turnos</h2><ul>"
    for t in turnos:
        html += f"<li>{t[1]} - {t[2]} {t[3]} - {t[4]}</li>"
    html += "</ul><a href='/logout'>Cerrar sesión</a>"

    return html

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)