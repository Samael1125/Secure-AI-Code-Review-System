from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

import models

@app.route("/")
def home():
    return "<h1>AI Code Review Assistant is Running 🚀</h1>"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)