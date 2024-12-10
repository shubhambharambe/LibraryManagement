from apscheduler.schedulers.background import BackgroundScheduler
from django.utils.timezone import now,timedelta
from django.core.mail import send_mail
from django.conf import settings
from.models import BookTransaction, User 


def send_reminder_emails():
    """
    Scheduled task to send book return reminders.
    """
    print("Checking for return reminders...")

    reminder_date = now().date() + timedelta(days=1)
    print(reminder_date)
    transactions = BookTransaction.objects.filter(
        expected_return_date__date=reminder_date
    )

    for transaction in transactions:
        # Extract borrower ID from the transaction
        borrower_id = transaction.borrower 

        try:
            
            borrower = User.objects.get(id=borrower_id.id)
        except User.DoesNotExist:
            print(f"Borrower with ID {borrower_id} not found for transaction ID: {transaction.id}")
            continue

        subject = 'Book Return Reminder'
        message = f"""
        Hello {borrower.username},

        This is a reminder that today is the last day to return the book you borrowed: "{transaction.book.title}".

        Please return the book by the end of the day to avoid any late fees.

        Best regards,
        Library Team
        """
        # Send the email
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [borrower.email]
        )
        print(f"Reminder sent to {borrower.email} for book {transaction.book.title}")
