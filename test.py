from Telegram_Bot import Bot
from instrument import INSTRU
from functions import Brain
# from webSocketTest import place_order

inntru = INSTRU()

bot = Bot()


print(Brain().calculate_quantity(21))
