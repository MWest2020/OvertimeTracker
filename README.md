# OvertimeTracker

## Description

OvertimeTracker is a Python application that fetches work log data from the Tempo Timesheets app in Jira and calculates overtime for employees based on predefined rules.

## Features

- Fetches work logs from Tempo Timesheets using the Tempo API.
- Calculates overtime hours considering:
  - Any hours over 8.5 on weekdays.
  - All hours worked on weekends.
- Generates Excel reports for each employee with overtime details.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/OvertimeTracker.git
   cd OvertimeTracker
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**

   - Create a `.env` file in the root directory.
   - Add your Tempo API token:

     ```env
     TEMPO_TOKEN=your_actual_tempo_api_token
     ```

## Usage

1. **Update employee information:**

   - Edit `main.py` to include your employees' names and Jira account IDs.

2. **Adjust date range (optional):**

   - Modify `start_date` and `end_date` in `main.py` as needed.

3. **Run the application:**

   ```bash
   python main.py
   ```

4. **View reports:**

   - Check the generated Excel files in the project directory.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

[MIT License](LICENSE)
