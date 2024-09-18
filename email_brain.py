import smtplib
from datetime import datetime
import pandas as pd


class EmailBrain:
    def send_report(self, message):
        # Email configuration
        sender_email = "swadeepbuchadi@gmail.com"
        receiver_email = "ppbuchadi@gmail.com"
        password = "kvmldwneihwlmuih"
        subject = f'Trading Bot update : {datetime.now()}'

        # Compose the email
        email_message = f"From: {sender_email}\nTo: {receiver_email}\nSubject: {subject}\n\n{message}"

        # Send the email using SMTP
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, email_message)
            server.quit()
            print("Email sent successfully!")
        except Exception as e:
            print("Error sending email:", e)

    def day_end_report(self):

        # Read the data from the CSV file into a pandas DataFrame
        data = pd.read_csv('Result/results.csv')

        # Convert the 'entry_time' and 'exit_time' columns to datetime objects
        data['entry_time'] = pd.to_datetime(data['entry_time'])
        data['exit_time'] = pd.to_datetime(data['exit_time'])

        # Filter the trades for today
        today = pd.to_datetime('today').strftime('%Y-%m-%d')
        todays_trades = data[data['entry_time'].dt.strftime('%Y-%m-%d') == today]

        # Calculate the total number of trades
        total_trades = len(todays_trades)

        # Calculate the number of trades with SL hit and without SL hit
        sl_hit_count = todays_trades['sl_hit'].eq('YES').sum()
        not_sl_hit_count = todays_trades['sl_hit'].eq('NO').sum()

        # Create a table with the information
        table = pd.DataFrame({
            'Total Trades': [total_trades],
            'SL Hit': [sl_hit_count],
            'Not SL Hit': [not_sl_hit_count]
        })
        table_string = table.to_string(index=False)

        self.send_report(message=table_string)






