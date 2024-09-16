import pandas as pd
import requests
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import os
import json
import argparse
import calendar

def fetch_worklogs(account_id, start_date, end_date, tempo_token):
    headers = {
        'Authorization': f'Bearer {tempo_token}',
        'Content-Type': 'application/json'
    }
    base_url = f'https://api.us.tempo.io/4/worklogs/user/{account_id}'
    
    current_date = start_date
    workdays = {}

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        params = {
            'from': date_str,
            'to': date_str,
            'limit': 1000,
        }

        response = requests.get(base_url, headers=headers, params=params)
        
        if response.status_code == 200:
            response_json = response.json()
            total_seconds = sum(log['timeSpentSeconds'] for log in response_json.get('results', []))
            hours_worked = total_seconds / 3600
            workdays[date_str] = hours_worked
        else:
            print(f"Failed to fetch work logs for account {account_id} on {date_str}. Status code: {response.status_code}")

        current_date += timedelta(days=1)

    return workdays

def get_account_name(account_id):
    try:
        with open('account_info.json', 'r') as f:
            account_info = json.load(f)
        return account_info.get(account_id, account_id)
    except FileNotFoundError:
        print("account_info.json not found. Using account ID as name.")
        return account_id

def get_all_accounts():
    try:
        with open('account_info.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("account_info.json not found.")
        return {}

def is_weekend(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return date_obj.weekday() >= 5  # 5 = Saturday, 6 = Sunday

def calculate_overtime(hours, date_str):
    if is_weekend(date_str):
        return hours  # All hours on weekend are overtime
    elif hours == 0:
        return 0  # No work, no overtime (e.g., day off)
    else:
        standard_hours = 8
        overtime_threshold = 8.5  # Overtime starts after 8.5 hours on weekdays
        if hours > overtime_threshold:
            return round(hours - overtime_threshold, 2)
        else:
            return 0  # No overtime if worked 8.5 hours or less

def create_excel_report(account_id, account_name, workdays, start_date, end_date):
    df = pd.DataFrame(list(workdays.items()), columns=['Date', 'Total Hours'])
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    df['Total Hours'] = df['Total Hours'].round(2)
    df['Overtime'] = df.apply(lambda row: calculate_overtime(row['Total Hours'], row['Date']), axis=1).round(2)

    # Calculate totals
    total_hours = df['Total Hours'].sum().round(2)
    total_overtime = df['Overtime'].sum().round(2)

    filename = f"{account_name}_{start_date.strftime('%Y-%m')}.xlsx"
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Daily Totals', index=False)

        worksheet = writer.sheets['Daily Totals']
        
        # Add totals row
        last_row = len(df) + 2  # +2 because Excel is 1-indexed and we have a header row
        worksheet.cell(row=last_row, column=1, value='Total')
        worksheet.cell(row=last_row, column=2, value=total_hours)
        worksheet.cell(row=last_row, column=3, value=total_overtime)

        # Format columns
        for idx, col in enumerate(df):
            series = df[col]
            max_len = max((
                series.astype(str).map(len).max(),
                len(str(series.name))
            )) + 1
            worksheet.column_dimensions[chr(65 + idx)].width = max_len

    return filename

def main():
    parser = argparse.ArgumentParser(description="Fetch Tempo worklogs for specific account(s).")
    parser.add_argument("account_id", nargs='?', help="The account ID to fetch worklogs for. If not provided, fetch for all accounts in account_info.json")
    parser.add_argument("--month", type=int, help="Month to fetch data for (1-12)")
    parser.add_argument("--year", type=int, help="Year to fetch data for")
    args = parser.parse_args()

    load_dotenv()
    TEMPO_TOKEN = os.getenv('TEMPO_TOKEN')

    if not TEMPO_TOKEN:
        print("TEMPO_TOKEN is not set in the .env file.")
        return

    # If month and year are not provided, use current month and year
    if args.month is None or args.year is None:
        today = date.today()
        year = today.year
        month = today.month
    else:
        year = args.year
        month = args.month

    # Calculate start and end dates for the given month
    start_date = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    end_date = date(year, month, last_day)

    if args.account_id:
        accounts = {args.account_id: get_account_name(args.account_id)}
    else:
        accounts = get_all_accounts()

    for account_id, account_name in accounts.items():
        print(f"\nFetching work logs for {account_name} (Account ID: {account_id})...")
        workdays = fetch_worklogs(account_id, start_date, end_date, TEMPO_TOKEN)

        if workdays:
            filename = create_excel_report(account_id, account_name, workdays, start_date, end_date)
            print(f"Excel report generated: {filename}")
        else:
            print(f"No worklogs found for {account_name} (Account ID: {account_id}).")

if __name__ == "__main__":
    main()