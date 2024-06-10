from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://teemo:u202214522@teemo.ck7qain.mongodb.net/TeemoDB"
mongo = PyMongo(app)

@app.before_first_request
def create_db_client():
    try:
        mongo.cx.server_info()
        print("Conectado a la base de datos de MongoDB Atlas")
    except Exception as e:
        print("Error al conectar a la base de datos:", e)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/prueba')
def prueba():
    return render_template('prueba.html')

@app.route('/two')
def about():
    return render_template('layertwo.html')
@app.route('/pagina-principal')
def pagina_principal():
    return 'Bienvenido, usuario autenticado!'

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        correo = request.form['correo']
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']
        mongo.db.usuarios.insert_one({
            'correo': correo,
            'usuario': usuario,
            'contraseña': contraseña
        })
        return 'Usuario registrado con éxito!'
    return render_template('registro.html')

@app.route('/inicio-sesion', methods=['GET', 'POST'])
def inicio_sesion():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']
        usuario_db = mongo.db.usuarios.find_one({'usuario': usuario})
        if usuario_db:
            if usuario_db['contraseña'] == contraseña:
                # Inicio de sesión exitoso, redirigir a la página principal
                return redirect(url_for('pagina_principal'))
            else:
                # Contraseña incorrecta, mostrar mensaje de error
                return 'Contraseña incorrecta'
        else:
            # Usuario no encontrado, mostrar mensaje de error
            return 'Usuario no encontrado'
    return render_template('inicio_sesion.html')