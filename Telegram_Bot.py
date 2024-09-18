import openai
import requests
import os
import pandas as pd



class Bot:
    def __init__(self):
        self.previous_msg = None

    def send_notification(self, text):
        bot_token = "6626794292:AAHWlh7fpEFHXjzpy9WX_ZM-ywgYkY89ZyI"
        my_id = '6132583742'
        base_url = f'https://api.telegram.org/bot{bot_token}/'
        url = base_url + 'sendMessage'
        params = {'chat_id': my_id, 'text': text}
        response = requests.post(url, params=params)
        return response.json()

    def day_end_report(self):
        # Read the data from the CSV file into a pandas DataFrame
        data = pd.read_csv('Result/results.csv')

        # Convert the 'entry_time' and 'exit_time' columns to datetime objects
        try:
            data['entry_time'] = pd.to_datetime(data['entry_time'], format='%Y-%m-%d %H:%M:%S.%f')
            data['exit_time'] = pd.to_datetime(data['exit_time'], format='%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            # Handle the case where the format doesn't match
            data['entry_time'] = pd.to_datetime(data['entry_time'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
            data['exit_time'] = pd.to_datetime(data['exit_time'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')

        # Filter the trades for today
        today = pd.to_datetime('today').strftime('%Y-%m-%d')
        todays_trades = data[data['entry_time'].dt.strftime('%Y-%m-%d') == today]

        # Calculate the total number of trades
        total_trades = len(todays_trades)

        # Calculate the number of trades with SL hit and without SL hit
        sl_hit_count = todays_trades['sl_hit'].eq('YES').sum()
        not_sl_hit_count = todays_trades['sl_hit'].eq('NO').sum()
        profit = todays_trades['profit'].sum()

        # Create a table with the information
        msg = f'Total trade: {total_trades} \n' \
              f'SL Trades: {sl_hit_count}\n' \
              f'Target Trades: {not_sl_hit_count}\n' \
              f'Total Profit for the Day: {profit}'
        self.send_notification(msg)

    def kill(self):
        bot_token = "6626794292:AAHWlh7fpEFHXjzpy9WX_ZM-ywgYkY89ZyI"
        my_id = '6132583742'
        base_url = f'https://api.telegram.org/bot{bot_token}/'
        url = base_url + 'getUpdates'
        res = requests.get(url=url)
        message = res.json()['result'][-1]['message']['text']
        if message == "kill":
            self.send_notification("Termination on way")
            # Brain().close_app_by_name("Resso")
            # os.system("shutdown /s /f /t 1")






    def chat(self):
        bot_token = "6626794292:AAHWlh7fpEFHXjzpy9WX_ZM-ywgYkY89ZyI"
        my_id = '6132583742'
        base_url = f'https://api.telegram.org/bot{bot_token}/'
        url = base_url + 'getUpdates'
        res = requests.get(url=url)
        text = res.json()['result'][-1]['message']['text']

        print("texts are same")
        print(text)
        return text

    def gpt(self, question):
        API_KEY = "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"

        openai.api_key = API_KEY

        # Define the prompt for GPT-3 to rewrite the input text
        prompt = (f"Answer the below below line and reply :\n"
                  f"{question}\n\n")

        # Call the GPT-3 API to generate a rewritten text
        response = openai.Completion.create(
            engine="davinci",
            prompt=question,
            temperature=0.7,
            max_tokens=200
        )

        # Extract the rewritten text from the API response
        reply = response.choices[0].text.strip()
        print(reply)

        self.send_notification(reply)

    def on_demand_report(self):
        bot_token = "6626794292:AAHWlh7fpEFHXjzpy9WX_ZM-ywgYkY89ZyI"
        my_id = '6132583742'
        base_url = f'https://api.telegram.org/bot{bot_token}/'
        url = base_url + 'getUpdates'
        res = requests.get(url=url)
        text = res.json()['result'][-1]['message']['text']
        if text == "Hi":
            self.day_end_report()

        print("texts are same")
        print(text)
