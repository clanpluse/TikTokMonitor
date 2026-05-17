import time
import schedule
from monitor import main as run_monitor

def job():
    print("Running monitor...")
    try:
        run_monitor()
    except Exception as e:
        print(f"Error: {e}")

# Run immediately on start
job()

# Schedule every 5 minutes
schedule.every(5).minutes.do(job)

print("Scheduler started. Running every 5 minutes...")
while True:
    schedule.run_pending()
    time.sleep(30)
