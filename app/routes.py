from app import app
from app.services.smart_service import SmartEventParser
from flask import render_template, request, jsonify

@app.route('/')
@app.route('/home')
def index_page():
    return render_template('index.html')

@app.route('/smart_text')
def smart_page():
    return render_template('smart.html')

@app.route('/smart_parse', methods=['POST'])
def parse_text():
    data = request.get_json() or {}
    text = data.get('text', '').strip()


    if not text:
        return jsonify({"error": "Kein Text übermittelt."}), 400

    parser = SmartEventParser()
    events = parser.parse_smart_text(text)
    
    return jsonify([e.to_dict() for e in events])