import threading
from datetime import datetime, timedelta
import pandas as pd
import json
from playsound import playsound
import csv
import os
import signal
from Telegram_Bot import Bot

bot = Bot()


class Brain:
    def __init__(self):
        self.sound_file = 'Happy Sms.mp3'
        self.in_trade = False
        self.entry_price = None
        self.sl = None
        self.sl_hit = None
        self.entry_time = None
        self.exit_time = None
        self.b = None
        self.s = None
        self.candle_size = None
        self.quantity = None


    def calculate_candle_start_time(self):
        # Get the current time
        current_time = datetime.now().time()

        # Calculate the minutes remaining to the next five-minute interval
        minutes_remaining = 2 - (current_time.minute % 2)

        # Calculate the timedelta to add to the current time
        time_delta = timedelta(minutes=minutes_remaining)

        # Create a datetime object with the current date and time
        current_datetime = datetime.combine(datetime.now().date(), current_time)

        # Add the timedelta to the current datetime
        rounded_datetime = current_datetime + time_delta

        # Format the rounded datetime to the desired format
        formatted_datetime = rounded_datetime.strftime("%Y-%m-%dT%H:%M")

        # Return the rounded time
        return formatted_datetime

    def increment_start_time(self, candle_start_time):
        # Convert the candle_start_time to a datetime object
        candle_start_datetime = datetime.fromisoformat(candle_start_time)

        # Increase the candle start time by 1 minute
        start_datetime = candle_start_datetime + timedelta(minutes=1)

        # Format the start datetime as a string in the desired format
        start_time = start_datetime.strftime("%H:%M:%S")

        # Return the updated start time
        return start_time

    def create_EMA(self, closing_price):
        with open("json_data.json", "r") as file:
            # Load tha data
            data = json.load(file)
        EMAy = data['last_candle_EMA']

        ema_value = 5
        k_multiplire = 2 / (ema_value + 1)
        EMA = (closing_price * k_multiplire) + (EMAy * (1 - k_multiplire))
        json_data = {
            "last_candle_EMA": round(EMA, 2)
        }
        # Open a file in write mode
        with open("json_data.json", "w") as file:
            # Write the dictionary to the file
            json.dump(json_data, file)

    def getOHLC_df(self, df):
        df_final = pd.DataFrame()
        open = df['ltp'].iloc[0]
        close = df['ltp'].iloc[-1]
        high = df['ltp'].max()
        low = df['ltp'].min()
        candel_time = df['timestamp'].iloc[-1]
        data = {
            'open': open,
            'close': close,
            'high': high,
            'low': low,
            'time': candel_time}
        df_final = df_final._append(data, ignore_index=True)
        print(df_final)

    def find_setup(self, high, low):
        with open("json_data.json", "r") as file:
            # Load tha data
            data = json.load(file)
        ema = data['last_candle_EMA']
        if high < ema:
            print('Found trade')
            self.entry_price = high
            self.sl = low
            threading.Thread(target=lambda: playsound(self.sound_file)).start()
            threading.Thread(target=lambda: bot.send_notification("Found trade")).start()
            self.in_trade = True
            return True
        else:
            print('No Trade')
            return False

    def record_the_trade(self, entry, entry_time, exit, exit_time, sl_hit):
        profit = entry - exit
        if sl_hit == "YES":
            profit = profit * (-1)
        pnl = [entry, entry_time, exit, exit_time, sl_hit, profit, self.b, self.s]
        pnl = [pnl]
        output_file = "Result/results.csv"
        # Write the data to the CSV file
        with open(output_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(pnl)

        self.reset_parameters()  # Resets the parameters after appending to the file

        print(f"CSV file '{output_file}' has been created.")

    def reset_parameters(self):
        self.entry_price = None
        self.sl = None
        self.sl_hit = None
        self.entry_time = None
        self.exit_time = None
        self.b = None
        self.s = None
        self.candle_size = None
        self.quantity = None

    def signal_handler(self, sig, frame):
        print("Terminating the program...")
        # Add any cleanup or termination tasks here
        exit(0)

    def terminate(self):
        pid = os.getpid()  # Get the process ID of the current script
        os.kill(pid, signal.SIGTERM)

    def calculate_quantity(self, candle_size):
        with open("capital.json", "r") as file:
            # Load tha data
            data = json.load(file)
        capital = data['Capital Money']
        risk = 0.005
        risk_amount = (risk*capital)
        quantity = risk_amount / candle_size
        lot_size = 15
        lot = round(quantity/lot_size)
        x = lot * lot_size * self.entry_price
        print(x)
        while x > capital:
            lot = lot-1
            x = lot * lot_size * self.entry_price
        quantity = lot * lot_size

        return quantity

    def update_capital(self, PL):
        global capital
        with open("capital.json", "r") as file:
            # Load tha data
            data = json.load(file)
        capital = data['Capital Money']
        if PL == 'P':
            capital = capital + (self.candle_size * self.quantity)
        else:
            capital = capital - (self.candle_size * self.quantity)

        json_data = {
            "Capital Money": capital
        }
        # Open a file in write mode
        with open("capital.json", "w") as file:
            # Write the dictionary to the file
            json.dump(json_data, file)







