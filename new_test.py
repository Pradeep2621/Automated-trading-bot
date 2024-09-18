import signal
from functions import Brain
import time

b = Brain()


while True:
    print("its working")
    time.sleep(1)
    print("still working")
    time.sleep(2)
    print("OMG still working")
    time.sleep(1)
    print("terminating now")
    b.terminate()

