import threading
from datetime import datetime, timedelta, time as dt_time
import pandas as pd
import pyotp
import time
from playsound import playsound
from functions import Brain
from smartapi import SmartConnect
from config import *
from SmartWebsocketv2 import SmartWebSocketV2
from Telegram_Bot import Bot
import os
from instrument import INSTRU

CANDLE_TIME = 1
SYMBOL_TOKEN = "55317"  # For bank nifty it is

got_trade = False
brain = Brain()
bot = Bot()
day_end = False

df = pd.DataFrame()
ohlc_df = pd.DataFrame()

obj = SmartConnect(api_key=apikey)
data = obj.generateSession(username, pwd, pyotp.TOTP(token).now())
print(data)
AUTH_TOKEN = data['data']['jwtToken']
refreshToken = data['data']['refreshToken']
FEED_TOKEN = obj.getfeedToken()
res = obj.getProfile(refreshToken)
bank_nifty_ltp = obj.ltpData("NSE", 'Nifty Bank', "99926009")['data']['ltp']
INSTRU().create_instru_list()
# token_num, symbol = INSTRU().get_token_symbol(bank_nifty_ltp)

# SYMBOL_TOKEN = token_num  # for Buying actual options.

# ------- Websocket code


correlation_id = "dft_test1"
action = 1
mode = 3

token_list = [{"exchangeType": 2, "tokens": [SYMBOL_TOKEN]}]  # ,

sws = SmartWebSocketV2(AUTH_TOKEN, apikey, username, FEED_TOKEN)


def on_data(wsapp, msg):
    try:
        # print("Ticks: {}".format(msg))
        LIVE_FEED_JSON[msg['token']] = {'token': msg['token'], 'ltp': msg['last_traded_price'] / 100,
                                        'exchange_timestamp': datetime.fromtimestamp(
                                            msg['exchange_timestamp'] / 1000).isoformat(), 'oi': msg['open_interest']}

    except Exception as e:
        print(e)


def on_open(wsapp):
    print("on open")
    sws.subscribe(correlation_id, mode, token_list)


def on_error(wsapp, error):
    print(error)


def on_close(wsapp):
    print("Close")


def update_tick_in_file():
    while True:
        message = LIVE_FEED_JSON
        print(message)

        ltp = message[SYMBOL_TOKEN]['ltp']
        timestamp = message[SYMBOL_TOKEN]['exchange_timestamp']
        instrumnet = message[SYMBOL_TOKEN]['token']
        global df
        currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        new_row = pd.DataFrame({'symbol': [instrumnet], 'timestamp': [timestamp],
                                'ltp': [ltp], })
        df = df._append(new_row, ignore_index=True)
        #
        # print(f"time : {timestamp} : {ltp}")
        df.to_csv('output_file.csv', index=False)


def convert_to_ohlc():
    time.sleep(1)
    global ohlc_df, candle_start_time, start_time

    # Convert the ISO timestamp to a pandas Timestamp object
    timestamp = pd.Timestamp(candle_start_time)

    # Calculate the end timestamp by adding one minute to the target timestamp
    end_timestamp = timestamp + pd.DateOffset(minutes=CANDLE_TIME)

    if not end_timestamp in pd.to_datetime(df['timestamp']):
        time.sleep(1)
    codf = df
    # Copying the data frame df to codf so that there will not be any interruption while running the function
    # as df is continuously updated in Background

    codf['timestamp'] = pd.to_datetime(codf['timestamp'])

    # Filter the DataFrame based on the timestamp range
    subset_df = codf[(codf['timestamp'] >= timestamp) & (codf['timestamp'] < end_timestamp)]
    if subset_df.empty:
        if datetime.now().time().strftime("%H:%M:%S") == '15:30:00':
            sws.close_connection()
            bot.send_notification("Connection Closed")
            bot.day_end_report()
            os.system("shutdown /s /f /t 1")
            brain.terminate()
        else:
            print("Subset is empty waiting for 1 sec \n calling convert function again")
            time.sleep(1)
            convert_to_ohlc()
    else:
        # Group the data by a N-minute interval and calculate OHLC values
        subset_ohlc_df = subset_df.groupby(pd.Grouper(key='timestamp', freq=f'{CANDLE_TIME}Min')).agg(
            {'ltp': ['first', 'max', 'min', 'last']})

        # Flatten the multi-level column index
        subset_ohlc_df.columns = ['Open', 'High', 'Low', 'Close']

        # Append the subset OHLC data to the main OHLC DataFrame
        ohlc_df = ohlc_df._append(subset_ohlc_df)

        # Increment the candle starting time by N minutes
        candle_start_time = (timestamp + pd.Timedelta(minutes=CANDLE_TIME)).strftime("%Y-%m-%dT%H:%M:%S")

        # Increment the loop starting time by N minutes
        ohlc_df.to_csv('ohlc.csv', index=False)

        # Asigne values

        df_1 = pd.read_csv('ohlc.csv')
        closing_price = df_1['Close'].iloc[-1]
        high = df_1['High'].iloc[-1]
        low = df_1['Low'].iloc[-1]

        brain.create_EMA(closing_price)
        if not brain.in_trade:
            global got_trade
            got_trade = brain.find_setup(high, low, )
        print(ohlc_df)
        print(f'next call will be at {start_time}')
        print(f'next candle Start at {candle_start_time}')


def execute_trade():
    global target, symbol, token_num
    loop_end = start_time

    entered = False

    while True:
        price = LIVE_FEED_JSON[SYMBOL_TOKEN]['ltp']
        current_time = datetime.now().strftime("%H:%M:%S")
        if loop_end != current_time:
            if not entered:
                if price > brain.entry_price:
                    brain.candle_size = brain.entry_price - brain.sl
                    brain.quantity = brain.calculate_quantity(brain.candle_size)
                    entered = True
                    loop_end = '15:25'

                    # TODO Buy at Market price here
                    # place_order("BUY", brain.quantity)

                    threading.Thread(target=lambda: playsound('Entry triggered.mp3')).start()
                    msg = [f'Entry Price: {brain.entry_price},\n Sl price is : {brain.sl},\n Time: {datetime.now()}']
                    threading.Thread(target=lambda: bot.send_notification(msg)).start()
                    print("entry triggered")
                    print(f'Sl price is : {brain.sl}')
                    print(f'Entry price is : {brain.entry_price}')

                    target = brain.entry_price + brain.candle_size
                    print(f'Target price is : {target}')
                    brain.entry_time = str(datetime.now())
            else:
                if price < brain.sl:

                    # TODO Sell at Market price here
                    # place_order("SELL", brain.quantity)

                    threading.Thread(target=lambda: playsound('Sl hit.mp3')).start()
                    threading.Thread(target=lambda: bot.send_notification(
                        f"Exited with SL\n Loss: {brain.sl - brain.entry_price}")).start()
                    print("SL hit, Trade Exited")
                    brain.in_trade = False
                    brain.sl_hit = 'YES'
                    brain.exit_time = str(datetime.now())
                    brain.update_capital("L")
                    brain.record_the_trade(brain.entry_price, brain.entry_time, brain.sl, brain.exit_time,
                                           brain.sl_hit)  # Update the P and L file
                    break
                elif price > target:
                    target = target + (brain.candle_size/2)
                    brain.sl = brain.sl + (brain.candle_size/2)

                    # TODO Sell at Market price here
                    # place_order("SELL", brain.quantity)
                    #
                    # print("Profit Trade Exited")
                    # threading.Thread(target=lambda: playsound('profit.mp3')).start()
                    # threading.Thread(target=lambda: bot.send_notification(
                    #     f"Exited with Profit. \n Profit: {brain.entry_price - brain.sl}")).start()
                    # brain.in_trade = False
                    # brain.sl_hit = 'NO'
                    # brain.exit_time = str(datetime.now())
                    # brain.update_capital("P")
                    # brain.record_the_trade(brain.entry_price, brain.entry_time, brain.sl, brain.exit_time,
                    #                        brain.sl_hit)  # Update the P and L file
                    # break
        else:
            if loop_end == '15:25':

                # TODO Sell at Market price here
                # place_order("SELL", brain.quantity)

                global day_end
                threading.Thread(target=lambda: playsound('exit.mp3')).start()
                threading.Thread(target=lambda: bot.send_notification("Exited at End of Market hours")).start()
                brain.sl_hit = 'DAY END'
                brain.exit_time = datetime.now()
                brain.update_capital("P")
                brain.record_the_trade(brain.entry_price, brain.entry_time, brain.sl, brain.exit_time,
                                       brain.sl_hit)  # Update the P and L file
                time.sleep(302)
                sws.close_connection()
                bot.send_notification("Connection Closed")
                bot.day_end_report()
                day_end = True
                os.system("shutdown /s /f /t 1")
                brain.terminate()
                break
            else:
                print("No entry")
                threading.Thread(target=lambda: playsound('No entry.mp3')).start()
                brain.in_trade = False
                break


def place_order(buy_sell, qty):
    # place order
    try:
        orderparams = {
            "variety": "NORMAL",
            "tradingsymbol": f"{symbol}",
            "symboltoken": f"{SYMBOL_TOKEN}",
            "transactiontype": buy_sell,
            "exchange": "NFO",
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": "0",
            "squareoff": "0",
            "stoploss": "0",
            "quantity": str(qty)
        }
        orderId = obj.placeOrder(orderparams)
        print(orderId)
        print("The order id is: {}".format(orderId))
    except Exception as e:
        print("Order placement failed: {}".format(e))


# Assign the callbacks.
sws.on_open = on_open
sws.on_data = on_data
sws.on_error = on_error
sws.on_close = on_close

threading.Thread(target=sws.connect).start()

print('Control Released')
time.sleep(5)


def start_feed():
    threading.Thread(target=update_tick_in_file).start()
    threading.Thread(target=lambda: bot.send_notification("Feed Started")).start()
    print('Feed Started')


if datetime.now().time() > dt_time(9, 15):
    candle_start_time = brain.calculate_candle_start_time()
else:
    candle_start_time = f'{datetime.now().strftime("%Y-%m-%d")}T09:15'

start_time = brain.increment_start_time(candle_start_time)
print(candle_start_time)
print(start_time)

start_feed()


while True:
    if datetime.now().time().strftime("%H:%M:%S") == start_time:
        if datetime.now().time().strftime("%H:%M:%S") == '15:30:00' or day_end:
            sws.close_connection()
            bot.send_notification("Connection Closed")
            bot.day_end_report()
            os.system("shutdown /s /f /t 1")
            brain.terminate()
            break
        else:
            print("------------------------------------------------------------------------------------")
            time_obj = datetime.strptime(start_time, "%H:%M:%S")
            incremented_time = time_obj + timedelta(minutes=CANDLE_TIME)
            start_time = incremented_time.strftime("%H:%M:%S")
            convert_to_ohlc()
            if got_trade:
                got_trade = False
                threading.Thread(target=execute_trade).start()
            threading.Thread(target=lambda: bot.send_notification(
                f"Bot is online. \nTime: {datetime.now().strftime('%H:%M:%S')}")).start()
            time.sleep(53)

# Update start time of the candle create function to c=increment by 1 min or by whatever time candle you want , s
# that function will be called first at for ex, 5 min candle, @9:20 AM and you update that time to increment by 5 min
# that is 9:25Am so that scheduler will call the function again at 9:25am and repeats the cycle
# Use test file code in create it add exceptions to catch any missing data as sometimes there is 2sec delay in feed
