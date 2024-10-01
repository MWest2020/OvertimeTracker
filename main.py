import pandas as pd
import requests
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import os
import json
import argparse
import calendar
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import psutil

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
            print(f"API Response for {date_str}:")
            print(json.dumps(response_json, indent=2))
            
            total_seconds = sum(log['timeSpentSeconds'] for log in response_json.get('results', []))
            hours_worked = total_seconds / 3600
            
            verlof_hours = 0
            verzuim_hours = 0
            
            for log in response_json.get('results', []):
                log_hours = log['timeSpentSeconds'] / 3600
                attributes = log.get('attributes', {}).get('values', [])
                for attr in attributes:
                    if attr.get('key') == '_Acount_':
                        if attr.get('value') == 'VERLOF':
                            verlof_hours += log_hours
                            print(f"VERLOF detected: {log_hours} hours")
                        elif attr.get('value') == 'CONDUCTION':
                            verzuim_hours += log_hours
                            print(f"VERZUIM detected: {log_hours} hours")
            
            print(f"Total hours: {hours_worked}, VERLOF: {verlof_hours}, VERZUIM: {verzuim_hours}")
            
            workdays[date_str] = {
                'hours': hours_worked,
                'verlof': verlof_hours,
                'verzuim': verzuim_hours
            }
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
    df = pd.DataFrame.from_dict(workdays, orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df.index = df.index.strftime('%Y-%m-%d')
    df.reset_index(inplace=True)
    df.columns = ['Date', 'Total Hours', 'VERLOF', 'VERZUIM']
    df['Total Hours'] = df['Total Hours'].round(2)
    df['Overtime'] = df.apply(lambda row: calculate_overtime(row['Total Hours'], row['Date']), axis=1).round(2)
    
    # Round VERLOF and VERZUIM hours to 2 decimal places
    df['VERLOF'] = df['VERLOF'].round(2)
    df['VERZUIM'] = df['VERZUIM'].round(2)

    # Replace 0 with empty string for VERLOF and VERZUIM
    df['VERLOF'] = df['VERLOF'].replace(0, '')
    df['VERZUIM'] = df['VERZUIM'].replace(0, '')

    # Reorder columns
    df = df[['Date', 'Total Hours', 'Overtime', 'VERLOF', 'VERZUIM']]

    print("DataFrame before writing to Excel:")
    print(df)

    # Calculate totals
    total_hours = df['Total Hours'].sum().round(2)
    total_overtime = df['Overtime'].sum().round(2)
    total_verlof = df['VERLOF'].apply(lambda x: float(x) if x != '' else 0).sum().round(2)
    total_verzuim = df['VERZUIM'].apply(lambda x: float(x) if x != '' else 0).sum().round(2)

    print(f"Totals: Hours={total_hours}, Overtime={total_overtime}, VERLOF={total_verlof}, VERZUIM={total_verzuim}")

    filename = f"{account_name}_{start_date.strftime('%Y-%m-%d')}.xlsx"
    if start_date != end_date:
        filename = f"{account_name}_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}.xlsx"

    sheet_name = start_date.strftime('%Y-%m-%d')
    if start_date != end_date:
        sheet_name = f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

        worksheet = writer.sheets[sheet_name]
        
        # Add totals row
        last_row = len(df) + 2  # +2 because Excel is 1-indexed and we have a header row
        worksheet.cell(row=last_row, column=1, value='Total')
        worksheet.cell(row=last_row, column=2, value=total_hours)
        worksheet.cell(row=last_row, column=3, value=total_overtime)
        worksheet.cell(row=last_row, column=4, value=total_verlof)
        worksheet.cell(row=last_row, column=5, value=total_verzuim)

        # Format columns
        for idx, col in enumerate(df.columns):
            series = df[col]
            max_len = max((
                series.astype(str).map(len).max(),
                len(str(col))
            )) + 1
            worksheet.column_dimensions[chr(65 + idx)].width = max_len

    return filename

email_sent = False

def send_email(subject, body, attachment_paths):
    global email_sent
    if email_sent:
        print("Debug: Email already sent, skipping")
        return False

    sender_email = os.getenv('GMAIL_USER')
    sender_password = os.getenv('GMAIL_PASSWORD')
    recipient_email = os.getenv('RECIPIENT_EMAIL')

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject

    message.attach(MIMEText(body, 'plain'))

    for attachment_path in attachment_paths:
        with open(attachment_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {os.path.basename(attachment_path)}',
        )

        message.attach(part)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
        print(f"Email sent successfully with {len(attachment_paths)} attachments")
        email_sent = True
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Fetch Tempo worklogs for specific account(s).")
    parser.add_argument("account_id", nargs='?', help="The account ID to fetch worklogs for. If not provided, fetch for all accounts in account_info.json")
    parser.add_argument("--date", help="Specific date to fetch data for (YYYY-MM-DD)")
    parser.add_argument("--month", type=int, help="Month to fetch data for (1-12)")
    parser.add_argument("--year", type=int, help="Year to fetch data for")
    parser.add_argument("--email", action="store_true", help="Send the report via email")
    args = parser.parse_args()

    load_dotenv()
    TEMPO_TOKEN = os.getenv('TEMPO_TOKEN')

    if not TEMPO_TOKEN:
        print("TEMPO_TOKEN is not set in the .env file.")
        return

    if args.date:
        start_date = end_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    elif args.month and args.year:
        start_date = date(args.year, args.month, 1)
        _, last_day = calendar.monthrange(args.year, args.month)
        end_date = date(args.year, args.month, last_day)
    else:
        today = date.today()
        start_date = date(today.year, today.month, 1)
        end_date = today

    if args.account_id:
        accounts = {args.account_id: get_account_name(args.account_id)}
    else:
        accounts = get_all_accounts()

    print("Debug: Starting report generation")
    generated_files = []

    for account_id, account_name in accounts.items():
        print(f"\nFetching work logs for {account_name} (Account ID: {account_id})...")
        workdays = fetch_worklogs(account_id, start_date, end_date, TEMPO_TOKEN)

        if workdays:
            filename = create_excel_report(account_id, account_name, workdays, start_date, end_date)
            print(f"Excel report generated: {filename}")
            generated_files.append(filename)
        else:
            print(f"No worklogs found for {account_name} (Account ID: {account_id}).")

    print(f"Debug: {len(generated_files)} reports generated")

    # Send email only once, after all reports have been generated
    if args.email and generated_files:
        print("Debug: Preparing to send email")
        subject = f"Worklog Reports - {start_date.strftime('%Y-%m')}"
        body = f"Please find attached the worklog reports for all accounts from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}."
        success = send_email(subject, body, generated_files)
        if success:
            print("Debug: Email sent successfully")
        else:
            print("Debug: Failed to send email")

    print("Debug: Main function completed")

def is_script_already_running():
    current_process = psutil.Process(os.getpid())
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        if process.info['name'] == current_process.name() and \
           process.info['cmdline'] == current_process.cmdline() and \
           process.info['pid'] != current_process.pid:
            return True
    return False

if __name__ == "__main__":
    if is_script_already_running():
        print("Another instance of this script is already running. Exiting.")
    else:
        main()