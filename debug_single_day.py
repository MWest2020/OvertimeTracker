import requests
from dotenv import load_dotenv
import os
from datetime import datetime
import json

def fetch_single_day_worklogs(account_id, date, tempo_token):
    headers = {
        'Authorization': f'Bearer {tempo_token}',
        'Content-Type': 'application/json'
    }
    url = 'https://api.tempo.io/core/3/worklogs'
    params = {
        'worker': account_id,
        'from': date,
        'to': date,
        'limit': 1000
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch work logs. Status code: {response.status_code}")
        print(response.text)
        return None

def process_worklogs(worklogs):
    total_seconds = 0
    print("Individual Worklogs:")
    for log in worklogs.get('results', []):
        seconds = log['timeSpentSeconds']
        hours = seconds / 3600
        total_seconds += seconds
        print(f"- Start Time: {log['startTime']}, Hours: {hours:.2f}, Description: {log['description']}")
    
    total_hours = total_seconds / 3600
    print(f"\nTotal timeSpentSeconds: {total_seconds}")
    print(f"Total Hours for the day: {total_hours:.2f}")

def main():
    load_dotenv()
    TEMPO_TOKEN = os.getenv('TEMPO_TOKEN')

    if not TEMPO_TOKEN:
        print("TEMPO_TOKEN is not set in the .env file.")
        return

    # Replace with the actual account ID you want to test
    account_id = '5f02b8549d9a120029f652b1'  # Example account ID
    date = '2024-08-31'  # Changed to match the date in the provided data

    print(f"Fetching worklogs for account {account_id} on {date}")
    worklogs = fetch_single_day_worklogs(account_id, date, TEMPO_TOKEN)

    if worklogs:
        print("\nRaw API Response:")
        print(json.dumps(worklogs, indent=2))
        print("\nProcessed Worklogs:")
        process_worklogs(worklogs)
    else:
        print("No worklogs retrieved.")

if __name__ == "__main__":
    main()