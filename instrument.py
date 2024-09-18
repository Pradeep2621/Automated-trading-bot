import requests
from pprint import pprint
import pandas as pd
import json
from datetime import datetime, timedelta


class INSTRU:

    def create_instru_list(self):
        url = "	https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

        response = requests.get(url=url)

        df = pd.DataFrame(response.json())

        df = df[df['symbol'].str.contains('CE')]

        filtered_df = df[(df['name'] == 'BANKNIFTY') & (df['instrumenttype'] == 'OPTIDX')]

        filtered_df.to_csv('tests/Instruments list.csv', index=False)

        print(filtered_df)

    def get_token_symbol(self, price):
        strike_price = ((price // 100) * 100) * 100
        df = pd.read_csv('tests/Instruments list.csv')
        # Calculate the current Thursday's date
        today = datetime.today()
        weekday = today.weekday()
        days_until_thursday = (3 - weekday) % 7
        current_thursday = today + timedelta(days=days_until_thursday)
        current_thursday_str = current_thursday.strftime('%d%b%Y').upper()  # Format as '17AUG2023'

        # Filter the DataFrame based on the current Thursday's expiry
        filtered_df = df.loc[(df['strike'] == strike_price) & (df['expiry'] == current_thursday_str)]

        # Get the token from the filtered DataFrame
        token = str(filtered_df['token'].values[0])
        symbol = filtered_df['symbol'].values[0]

        print("Token:", token, "\n Symbol", symbol)

        print(type(token), type(symbol))

        return token, symbol
