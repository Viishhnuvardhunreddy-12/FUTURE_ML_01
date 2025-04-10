from flask import Flask, render_template, request, send_file, jsonify
import os
import pandas as pd
from werkzeug.utils import secure_filename
from models.forecast_model import generate_forecast
import json
import traceback
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        print("\n=== Starting new upload ===")
        if 'file' not in request.files:
            print("No file in request")
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        print(f"File received: {file.filename}")
        
        if file.filename == '':
            print("Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            print(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Only CSV files are allowed'}), 400

        try:
            # Read the file content and decode it properly
            content = file.read()
            # Try different encodings
            encodings = ['utf-8', 'latin1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    # Convert bytes to string using the current encoding
                    str_content = content.decode(encoding)
                    # Create a string buffer
                    buffer = io.StringIO(str_content)
                    # Try to read as CSV
                    df = pd.read_csv(buffer)
                    print(f"Successfully read CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"Error with {encoding} encoding: {str(e)}")
                    continue

            if df is None:
                raise ValueError("Could not read the CSV file with any supported encoding")

            print(f"CSV read successfully. Columns found: {df.columns.tolist()}")
            
            # Save file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, 'wb') as f:
                f.write(content)
            print(f"File saved to: {filepath}")
            
            # Check required columns
            required_columns = ['ORDERDATE', 'SALES']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Clean column names and data
            df = df.copy()
            df['ORDERDATE'] = df['ORDERDATE'].astype(str).str.strip()
            df['SALES'] = df['SALES'].astype(str).str.strip()
            
            # Preview the data
            print("\nData preview:")
            print(df[['ORDERDATE', 'SALES']].head())
            
            # Generate forecast
            print("\nGenerating forecast...")
            # The generate_forecast function now returns a complete result dictionary
            result = generate_forecast(df)
            print("Forecast generated successfully")
            
            return jsonify(result)
            
        except pd.errors.EmptyDataError:
            print("Empty CSV file")
            return jsonify({'error': 'The uploaded CSV file is empty'}), 400
        except pd.errors.ParserError as e:
            print(f"CSV parsing error: {str(e)}")
            return jsonify({'error': 'Invalid CSV format. Please check your file.'}), 400
        except ValueError as e:
            print(f"Validation error: {str(e)}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            print(f"Processing error: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/download_forecast', methods=['GET'])
def download_forecast():
    try:
        forecast_file = os.path.join(app.config['UPLOAD_FOLDER'], 'forecast.csv')
        if not os.path.exists(forecast_file):
            return jsonify({'error': 'No forecast file available'}), 404
        return send_file(forecast_file, as_attachment=True, download_name='forecast_results.csv')
    except Exception as e:
        print(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/forecast_details', methods=['GET'])
def get_forecast_details():
    try:
        details_file = os.path.join(app.config['UPLOAD_FOLDER'], 'forecast_details.json')
        if not os.path.exists(details_file):
            return jsonify({'error': 'No forecast details available'}), 404
        with open(details_file, 'r') as f:
            details = json.load(f)
        return jsonify(details)
    except Exception as e:
        print(f"Error reading forecast details: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 