from apscheduler.schedulers.background import BackgroundScheduler
from .task import send_reminder_emails 

def start_scheduler():
    
    # Initialize and start the APScheduler.
    
    scheduler = BackgroundScheduler()
   
    scheduler.add_job(send_reminder_emails, 'cron', hour=9, minute=45)  # Runs at 9:00 AM
    # scheduler.add_job(send_reminder_emails, 'interval', minutes=20)
    scheduler.start()
    print("Scheduler started.")
