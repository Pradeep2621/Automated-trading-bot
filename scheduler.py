import schedule
import threading
import time
import subprocess


sec = 47
schedule_time = "09:10"


def run_main_project():
    # Replace 'main_project.py' with the filename of your main project file
    global sec
    subprocess.run(["python", "main.py"])


def schedule_task():
    # Schedule the execution of the main project function at specific times
    schedule.every().day.at(schedule_time).do(run_main_project)

    # Keep the schedule running in the background
    while True:
        schedule.run_pending()
        time.sleep(1)
        print("running")


if __name__ == "__main__":
    # Start the scheduling task in a separate thread
    threading.Thread(target=schedule_task).start()

    # The rest of your code for the small program can go here
    # This part will be executed while the scheduling task is running in the background
    # You can add other functionalities or loops here as needed
