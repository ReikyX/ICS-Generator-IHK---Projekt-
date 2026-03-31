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
    data = request.get_json()
    text = data.get('text', '')

    parser = SmartEventParser()
    events = parser.parse_smart_text(text)

    result = [
        {
            'start_date': e['start_date'].strftime('%d.%m.%Y'),
            'end_date': e['end_date'].strftime('%d.%m.%Y'),
            'raw': e['raw'],
        }
        for e in events
    ]
    return jsonify(result)