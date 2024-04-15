import schedule
import time
import requests

def call_notification_api():
    url = "http://localhost:5000/api/check_last_service_notification"
    response = requests.get(url)
    if response.status_code == 200:
        print("Notification check completed successfully.")
    else:
        print("Failed to check notifications.")

# Schedule the task to run everyday at 12:30 PM
schedule.every().day.at("12:09").do(call_notification_api)

while True:
    schedule.run_pending()
    time.sleep(1)
