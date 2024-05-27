from flask import Flask, render_template
from pymongo import MongoClient
app = Flask(__name__)

try:
    client = MongoClient('mongodb+srv://teemo:Op6QSSZUUfXZe6Lf@teemo.ck7qain.mongodb.net/')
    database = client['TeemoDB']
    collection = database['País']
    documents = collection.find()

    for document in documents:
        print(document)

except Exception as ex:
    print("error: {}".format(ex))

finally:
    client.close()
    print("finalizada")

@app.route('/')
def home():
    return render_template('mongo.html')

if __name__ == '__main__':
    app.run()