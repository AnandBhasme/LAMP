from flask import Flask, render_template, jsonify, Response
import cv2
from pyzbar import pyzbar
import time
import pandas as pd
from datetime import datetime
import os
import webbrowser

app = Flask(__name__, static_folder='resources')

# Path to the library database containing the library id and names of students and read it into a DataFrame
library_db_path = 'Database/Library_DB.csv'
library_db = pd.read_csv(library_db_path)

# Path to the Excel file for logging library entries
excel_path = 'Output/library_entries.xlsx'

# Check if the Excel file exists, if not create a new DataFrame with specified columns
if os.path.exists(excel_path):
    df = pd.read_excel(excel_path, index_col=0)
else:
    df = pd.DataFrame(columns=['Date', 'Name', 'Barcode Data', 'Time In', 'Time Out'])

# Dictionary to store barcode data and related information
barcode_data = {
    "last_scanned": None,
    "timestamp": None,
    "pytime": None,
    "pydate": None,
    "last_name": None,
    "last_action": None,
    "current_count": 0
}

# Function to update the current count of people in the library
def update_current_count():
    global dfde
    dfde = pd.read_excel(excel_path, index_col=0)
    time_in_count = int(dfde['Time In'].notna().sum())
    time_out_count = int(dfde['Time Out'].notna().sum())
    barcode_data["current_count"] = int(time_in_count - time_out_count)

# Function to decode barcodes from the video feed
def decode_barcode(camera_index):
    global barcode_data, df, library_db
    camera = cv2.VideoCapture(camera_index)
    
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        barcodes = pyzbar.decode(frame)
        for barcode in barcodes:
            decoded_data = barcode.data.decode("utf-8")
            current_time = datetime.now()
            current_time_antispam = time.time()
            date_str = current_time.strftime("%Y-%m-%d")
            time_str = current_time.strftime("%H:%M:%S")

            # Lookup the name associated with the scanned barcode
            name = library_db.loc[library_db['library_id'] == decoded_data, 'name'].values
            if len(name) > 0:
                name = name[0]
            else:
                barcode_data["last_name"] = "Please Scan again. If problem persists, contact the librarian"
                continue

            # Check if the barcode is scanned for the first time or after a certain interval to avoid spamming of entries by same entry.
            if decoded_data != barcode_data["last_scanned"] or (current_time_antispam - barcode_data.get("timestamp", 0)) > 5:
                barcode_data["last_scanned"] = decoded_data
                barcode_data["timestamp"] = current_time_antispam
                barcode_data["pytime"] = time_str
                barcode_data["pydate"] = date_str
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Found barcode: {decoded_data}")

                # Check if the person is checking out or checking in
                existing_entry = df[(df['Barcode Data'] == decoded_data) & (df['Time Out'].isna())]

                if not existing_entry.empty:
                    df.loc[existing_entry.index[-1], 'Time Out'] = time_str
                    barcode_data["last_action"] = "Checked Out"
                    barcode_data["current_count"] -= 1
                else:
                    new_entry = pd.DataFrame({
                        'Date': [date_str],
                        'Name': [name],
                        'Barcode Data': [decoded_data],
                        'Time In': [time_str],
                        'Time Out': [pd.NA]
                    })
                    df = pd.concat([df, new_entry], ignore_index=True)
                    barcode_data["last_action"] = "Checked In"
                    barcode_data["current_count"] += 1
                barcode_data["last_name"] = name

                # Add the entry to Excel log file
                df.to_excel(excel_path, index=True)

        # Fetch the camera frames to be displayed in the video feed
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n')

    camera.release()

# Route to render the main web page 
@app.route('/')
def index():
    return render_template('index.html')

# Route to provide data for the frontend
@app.route('/data')
def data():
    if barcode_data["last_name"] == "Please Scan again. If problem persists, contact the librarian":
        return jsonify({"message": barcode_data["last_name"],
                        "current_count": barcode_data["current_count"]})
    else:
        return jsonify({
            "last_scanned": barcode_data["last_scanned"],
            "time":barcode_data["pytime"],
            "date":barcode_data["pydate"],
            "timestamp": barcode_data["timestamp"],
            "last_name": barcode_data["last_name"],
            "last_action": barcode_data["last_action"],
            "current_count": barcode_data["current_count"]
        })

# Route to provide the video feed
@app.route('/video_feed')
def video_feed():
    return Response(decode_barcode(1),  
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Main function to start the Flask app
if __name__ == '__main__':
    update_current_count()
    port = 2136 #Can you tell why I chose this port number?
    webbrowser.open(f"http://localhost:{port}")
    app.run(debug=True, use_reloader=False, port=port)