from app import app
from app.services.smart_service import SmartEventParser
from app.services.ical_service import ICalService
from flask import render_template, request, jsonify, Response


# def index_page():
#     return render_template('index.html')

# @app.route('/smart_text')
@app.route('/')
@app.route('/home')
def smart_page():
    return render_template('smart.html')

@app.route('/smart_parse', methods=['POST'])
def parse_text():
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    custom_title = data.get('custom_title', '').strip()

    if not text:
        return jsonify({"error": "Kein Text übermittelt."}), 400

    parser = SmartEventParser()
    events = parser.parse_smart_text(text, custom_title)

    
    return jsonify([e.to_dict() for e in events])

@app.route('/smart_ical', methods=['POST'])
def export_ical():
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    custom_title = data.get('custom_title', '').strip()

    if not text:
        return jsonify({"error": "Kein Text übermittelt."}), 400
    
    parser = SmartEventParser()
    events = parser.parse_smart_text(text, custom_title)
    ical_service = ICalService()
    ical_data = ical_service.create_icalendar(events)

    return Response(
        ical_data,
        mimetype='text/calendar',
        headers={"Content-Disposition": "attachment; filename=events.ics"}
    )