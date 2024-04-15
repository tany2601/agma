from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime
from flask_cors import CORS
import json
from datetime import datetime, timedelta
from twilio.rest import Client
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
CORS(app)

service_account_key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")

# Get Firebase database URL from environment variable
database_url = os.getenv("FIREBASE_DATABASE_URL")

# Initialize Firebase app with service account credentials
cred = credentials.Certificate(service_account_key_path)
firebase_admin.initialize_app(cred, {
    'databaseURL': database_url
})

# Reference to the Firebase Realtime Database
ref = db.reference('/user')

# Decode timestamp ID into date
def decode_timestamp(timestamp_id):
    timestamp_str = str(timestamp_id)
    year = int(timestamp_str[:4])
    month = int(timestamp_str[4:6])
    day = int(timestamp_str[6:8])
    hour = int(timestamp_str[8:10])
    minute = int(timestamp_str[10:12])
    second = int(timestamp_str[12:14])
    return datetime(year, month, day, hour, minute, second)
    

# API endpoint to get all table names
@app.route('/api/users', methods=['GET'])
def get_tables():
    data = ref.get()
    table_names = list(data.keys()) # Get all table names
    return jsonify(table_names)

@app.route('/api/machines', methods=['POST'])
def get_tables_inside():
    data = request.get_json()  # Get JSON data from request body
    if 'username' not in data:
        return jsonify({"error": "Please provide a 'table_name' in the request body"}), 400

    table_name = data['username']
    table_ref = ref.child(table_name)
    table_data = table_ref.get()

    if not table_data:
        return jsonify({"error": f"Table '{table_name}' not found"}), 404

    if not isinstance(table_data, dict):
        return jsonify({"error": f"Table '{table_name}' does not contain sub-tables"}), 400

    sub_tables = list(table_data.keys())  # Get sub-table names
    return jsonify(sub_tables)

# API endpoint to get the last values of Vibration, Water_level, and temperature_value
@app.route('/api/machine_data', methods=['POST'])
def get_last_values():
    data = request.get_json()  # Get JSON data from request body
    if 'username' not in data or 'machine_name' not in data:
        return jsonify({"error": "Please provide 'username' and 'machine_name' in the request body"}), 400

    username = data['username']
    machine_name = data['machine_name']
    user_ref = ref.child(username)
    
    if not user_ref.get():
        return jsonify({"error": f"User '{username}' not found"}), 404
    
    machine_ref = user_ref.child(machine_name)
    
    if not machine_ref.get():
        return jsonify({"error": f"Machine '{machine_name}' not found for user '{username}'"}), 404

    last_values = {}

    for data_type in ['Vibration', 'Water_level', 'temperature_value']:
        data_ref = machine_ref.child(data_type)
        data_values = data_ref.get()

        if data_values:
            last_value_key = list(data_values.keys())[-1]
            last_value = data_values[last_value_key]
            last_value['timestamp'] = decode_timestamp(last_value['id']).strftime("%Y-%m-%d %H:%M:%S")
            last_values[data_type] = last_value

    return jsonify(last_values)


@app.route('/api/fetch_service', methods=['POST'])
def fetch_service_document():
    data = request.get_json()  # Get JSON data from request body
    if 'username' not in data or 'machine_name' not in data:
        return jsonify({"error": "Please provide 'username' and 'machine_name' in the request body"}), 400

    username = data['username']
    machine_name = data['machine_name']
    
    user_ref = ref.child(username)
    
    if not user_ref.get():
        return jsonify({"error": f"User '{username}' not found"}), 404
    
    machine_ref = user_ref.child(machine_name)
    
    if not machine_ref.get():
        return jsonify({"error": f"Machine '{machine_name}' not found for user '{username}'"}), 404

    service_ref = machine_ref.child('service_document')
    service_document = service_ref.get()

    if not service_document:
        return jsonify({"error": f"No service document found for machine '{machine_name}'"}), 404
    
    return jsonify(service_document)

@app.route('/api/push_service', methods=['POST'])
def push_service_document():
    data = request.get_json()  # Get JSON data from request body
    if 'username' not in data or 'machine_name' not in data:
        return jsonify({"error": "Please provide 'username' and 'machine_name' in the request body"}), 400

    username = data['username']
    machine_name = data['machine_name']
    
    user_ref = ref.child(username)
    
    if not user_ref.get():
        return jsonify({"error": f"User '{username}' not found"}), 404
    
    machine_ref = user_ref.child(machine_name)
    
    if not machine_ref.get():
        return jsonify({"error": f"Machine '{machine_name}' not found for user '{username}'"}), 404

    service_ref = machine_ref.child('service_document')
    
    # Generate unique ID for the new service entry
    new_service_id = service_ref.push().key

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update service document with new service entry
    new_service_data = {
        "status": "pending",  # Example new service data
        "timestamp": date,  # Example new service data
        "additional_info": "Additional information here"  # Example additional information
    }
    service_ref.child(new_service_id).set(new_service_data)
    
    # Update last service date
    service_document = service_ref.get()
    if not service_document:
        service_document = {
            "last_service_date": ""  # Initialize last service date
        }
    service_document["last_service_date"] = date
    service_ref.update(service_document)
    
    return jsonify({"message": "New service entry added successfully"})

    
@app.route('/api/get_last_service_date', methods=['POST'])
def get_last_service_date():
    data = request.get_json()  # Get JSON data from request body
    if 'username' not in data or 'machine_name' not in data:
        return jsonify({"error": "Please provide 'username' and 'machine_name' in the request body"}), 400

    username = data['username']
    machine_name = data['machine_name']
    
    user_ref = ref.child(username)
    
    if not user_ref.get():
        return jsonify({"error": f"User '{username}' not found"}), 404
    
    machine_ref = user_ref.child(machine_name)
    
    if not machine_ref.get():
        return jsonify({"error": f"Machine '{machine_name}' not found for user '{username}'"}), 404

    service_ref = machine_ref.child('service_document')
    service_document = service_ref.get()

    if not service_document or 'last_service_date' not in service_document:
        return jsonify({"error": "Last service date not found"}), 404
    
    last_service_date = service_document['last_service_date']
    
    return jsonify({"last_service_date": last_service_date})



# Initialize Twilio client
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
recipient_phone_number = os.getenv("RECIPIENT_PHONE_NUMBER")
client = Client(account_sid, auth_token)

# Function to send SMS notification
def send_notification(username, machine_name):
    message = client.messages.create(
        body=f"The last service date for machine '{machine_name}' of user '{username}' has exceeded 30 days.",
        from_=twilio_phone_number,
        to=recipient_phone_number
    )
    print(f"Notification sent: {message.sid}")

@app.route('/api/check_last_service_notification', methods=['GET'])
def check_last_service_notification():
    all_usernames = ref.get()  # Get all usernames

    for username, user_data in all_usernames.items():
        for machine_name, machine_data in user_data.items():
            service_document = machine_data.get('service_document', {})
            last_service_date_str = service_document.get('last_service_date')

            if last_service_date_str:
                last_service_date = datetime.strptime(last_service_date_str, '%Y-%m-%d %H:%M:%S')
                current_date = datetime.now()
                difference = current_date - last_service_date
                if difference.days > 30:
                    send_notification(username, machine_name)
                # else:
                #     send_notification(username, machine_name)
    return jsonify({"message": "Notification check completed."})


if __name__ == '__main__':
    app.run(debug=True)
