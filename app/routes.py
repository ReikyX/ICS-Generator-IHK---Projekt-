from app import app
from flask import render_template

@app.route('/')
@app.route('/home')
def index_page():
    return render_template('index.html')

@app.route('/smart_text')
def smart_page():
    return render_template('smart.html')