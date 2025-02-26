from main import generate
from flask import Flask, request, jsonify, render_template, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
import pytesseract
import csv
import os
import pandas as pd
from datetime import datetime
import io
import pdfkit

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crime_reports.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# CrimeReport model
class CrimeReport(db.Model):
    firNo = db.Column(db.String, primary_key=True)
    district = db.Column(db.String)
    date = db.Column(db.Date)
    day = db.Column(db.String)
    dateOfOccurrence = db.Column(db.Date)
    placeOfOccurrence = db.Column(db.String)
    name = db.Column(db.String)
    dob = db.Column(db.Date)
    nationality = db.Column(db.String)
    occupation = db.Column(db.String)
    address = db.Column(db.String)
    reportedCrime = db.Column(db.String)
    propertiesInvolved = db.Column(db.String)
    modelOutput = db.Column(db.String)

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/report-crime")
def reportCrime():
    return render_template("report-crime.html")

@app.route('/process_reported_crime', methods=['POST'])
def process_reported_crime():
    try:
        data = request.get_json()

        # Extract and process reported crime
        reported_crime = data.get('reportedCrime', '')
        ipc_sections = generate(reported_crime)

        # Extract data from request and save to database
        new_report = CrimeReport(
            firNo=data.get('firNo'),
            district=data.get('district'),
            date=datetime.strptime(data.get('date'), '%Y-%m-%d'),
            day=data.get('day'),
            dateOfOccurrence=datetime.strptime(data.get('dateOfOccurrence'), '%Y-%m-%d'),
            placeOfOccurrence=data.get('placeOfOccurrence'),
            name=data.get('name'),
            dob=datetime.strptime(data.get('dob'), '%Y-%m-%d'),
            nationality=data.get('nationality'),
            occupation=data.get('occupation'),
            address=data.get('address'),
            reportedCrime=reported_crime,
            propertiesInvolved=data.get('propertiesInvolved'),
            modelOutput=ipc_sections
        )

        db.session.add(new_report)
        db.session.commit()

        return jsonify({'result': ipc_sections, 'status': 'success'})
    except Exception as e:
        print(f"Error processing crime report: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/submit_ipc_sections', methods=['POST'])
def submit_ipc_sections():
    data = request.get_json()
    fir_no = data.get('firNo')
    ipc_sections = data.get('ipcSections')

    # Update the IPC sections
    report = CrimeReport.query.filter_by(firNo=fir_no).first()
    if report:
        report.modelOutput = ipc_sections
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'IPC sections updated successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Report not found'}), 404

@app.route('/ipc-dataset')
def ipcDataset():
    csv_file_path = 'static/resources/ipc_ds.csv'
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            headers = next(csv_reader)
            data = list(csv_reader)
    except FileNotFoundError:
        return "CSV file not found."
    return render_template('ipc-dataset.html', headers=headers, data=data)

@app.route("/ocr-analysis")
def ocrCrimeAnalysis():
    return render_template("ocr-recognition.html")

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"})
        file = request.files['file']
        file_type = request.form['fileType']
        if file.filename == '':
            return jsonify({"error": "No selected file"})

        if file_type == 'image':
            temp_path = os.path.join('uploads', file.filename)
            file.save(temp_path)
            image = Image.open(temp_path)
            extracted_text = pytesseract.image_to_string(image, lang='hin+eng')
            generated_output = generate(extracted_text)
            return jsonify({"message": extracted_text, "generated_output": generated_output})
        return jsonify({"message": "File uploaded but not processed"})
    except Exception as e:
        print(f"Error uploading file: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/fir-form")
def firForm():
    return render_template("fir-form.html")

@app.route('/display_fir/<fir_no>')
def display_fir(fir_no):
    report = CrimeReport.query.filter_by(firNo=fir_no).first()
    if report:
        return render_template('display-report.html', report=report)
    else:
        return 'Report not found', 404

path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

@app.route('/download_fir_pdf/<fir_no>')
def download_fir_pdf(fir_no):
    report = CrimeReport.query.filter_by(firNo=fir_no).first()
    if report:
        rendered_html = render_template('display-report.html', report=report)
        pdf_content = pdfkit.from_string(rendered_html, False, options={"enable-local-file-access": ""}, configuration=config)
        pdf_file = io.BytesIO(pdf_content)
        response = make_response(pdf_file.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=FIR_Report_{fir_no}.pdf'
        return response
    else:
        return 'Report not found', 404

# Ensure tables are created
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
