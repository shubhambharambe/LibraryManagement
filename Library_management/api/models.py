from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
class User_Address(models.Model):
   line1=models.CharField(max_length=250,blank=False)
   line2=models.CharField(max_length=250,blank=False)
   line3=models.CharField(max_length=250,blank=True)
   city=models.CharField(max_length=50,blank=False)
   pincode=models.IntegerField()
class User(AbstractUser):
  role_choices = [
        ('librarian', 'Librarian'),
        ('borrower', 'Borrower')
    ]
  username = models.CharField(max_length = 50, blank = True, null = True, unique = True)
  email = models.EmailField(('email address'), unique = True)
  first_name=models.CharField(max_length=250,blank=False,null=True)
  last_name=models.CharField(max_length=250,blank=False,null=True)
  mobile_no = models.IntegerField(null=True)
  user_role = models.CharField(max_length=10, choices=role_choices, default='borrower')
  u_address=models.ForeignKey(User_Address, null=True,related_name='adress',on_delete=models.CASCADE)
  
  USERNAME_FIELD = 'email'
  REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
  def __str__(self):
      return "{}".format(self.email)
class Category(models.Model):
    name=models.CharField(max_length=50,unique=True)
    description=models.CharField(null=True,max_length=100,blank=True)
    def __str__(self):
        return f"{self.name}" 
      
class Book(models.Model):
    title = models.CharField(max_length=50)
    isbn = models.IntegerField(unique=True, null=False, blank=False, 
                               validators=[
                                   MinValueValidator(10000000),  # Minimum value for 8 digits
                                   MaxValueValidator(99999999)  # Maximum value for 8 digits
                               ])
    genre = models.CharField(max_length=50)
    published_date = models.DateField()
    total_copies = models.PositiveIntegerField()
    available_copies = models.PositiveIntegerField()
    category=models.ForeignKey(Category,related_name='books',on_delete=models.CASCADE)
    price =models.PositiveIntegerField(null=False)
    created_by=models.CharField(max_length=50,blank=True)
    copy_isbns = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.title}"

    def save(self, *args, **kwargs):
        # Ensure available_copies does not exceed total_copies
        if self.available_copies > self.total_copies:
            self.available_copies = self.total_copies
        
        # Generate ISBNs for the copies if not already generated
        if not self.copy_isbns:
            self.generate_copy_isbns()

        super().save(*args, **kwargs) 
    
       

    def generate_copy_isbns(self):
        """Generates unique ISBNs for each copy of the book."""
        self.copy_isbns = []
        for i in range(1, self.total_copies + 1):
            # Generate the unique copy ISBN by appending a number to the base ISBN
            copy_isbn = f"{self.isbn}{str(i).zfill(4)}"  # Adding 4 digits to make it unique for each copy
            self.copy_isbns.append(copy_isbn)
class BookTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    book = models.ForeignKey(Book, related_name='transactions', on_delete=models.CASCADE)
    borrower = models.ForeignKey(User, related_name='borrowed_books', on_delete=models.CASCADE)
    borrow_date = models.DateTimeField(default=timezone.now)
    expected_return_date = models.DateTimeField(null=True, blank=True) 
    return_date = models.DateTimeField(null=True, blank=True)
    fine = models.PositiveIntegerField(default=0)
    copy_isbn = models.CharField(max_length=12, unique=True, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.borrower.username} borrowed {self.book.title} with ISBN {self.copy_isbn}"

    def save(self, *args, **kwargs):
        if BookTransaction.objects.filter(
            copy_isbn=self.copy_isbn, 
            status__in=['pending', 'approved'], 
            return_date__isnull=True
        ).exists():
            raise ValueError("This book copy is already borrowed by another user.")
    # Set expected return date if not provided
        if not self.expected_return_date:
            self.expected_return_date = self.borrow_date + timedelta(days=10)

        # Calculate fine only if return_date is provided
        if self.return_date and self.return_date.date() > self.expected_return_date.date():
            overdue_days = (self.return_date.date() - self.expected_return_date.date()).days
            if overdue_days <= 8:
                self.fine = overdue_days * 10
            else:
                self.fine = (8 * 10) + ((overdue_days - 8) * 20)
        else:
            self.fine = 0 

        if not self.return_date:
            if self.book.available_copies > 0:
                self.book.available_copies -= 1
                self.book.save()

                 # Assign a unique copy ISBN (choose the first available ISBN from copy_isbns)
                self.copy_isbn = self.book.copy_isbns[0]  # Choose the first copy for simplicity

                # Remove the chosen ISBN from the list of available copies (so it's not available again until it's returned)
                self.book.copy_isbns.pop(0)
                self.book.save()

        else:
            self.book.available_copies += 1
            self.book.copy_isbns.append(self.copy_isbn)
            
            self.book.save()
        super().save(*args, **kwargs)
        
