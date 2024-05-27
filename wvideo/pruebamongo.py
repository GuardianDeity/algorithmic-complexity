from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient

app = Flask(__name__)

# Configuración de la conexión a MongoDB
client = MongoClient('mongodb+srv://teemo:Op6QSSZUUfXZe6Lf@teemo.ck7qain.mongodb.net/')
db = client.TeemoDB
collection = db.Rutas

@app.route('/')
def home():
    return render_template('mongo.html')

# Ruta para insertar un documento en MongoDB
@app.route('/add', methods=['POST'])
def add_document():
    data = request.json
    collection.insert_one(data)
    return jsonify({"message": "Documento agregado"}), 201

# Ruta para obtener documentos de MongoDB
@app.route('/documents', methods=['GET'])
def get_documents():
    documents = list(collection.find({}, {"_id": 0}))
    return jsonify(documents), 200

# Ruta para obtener los nombres desde MongoDB
@app.route('/rutas', methods=['GET'])
def get_names():
    names = collection.distinct("Rutas")
    return jsonify(names), 200

if __name__ == '__main__':
    app.run(debug=True)