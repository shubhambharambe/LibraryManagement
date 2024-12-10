from urllib import request
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import User, User_Address, Category, Book, BookTransaction
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import (
    UserSerializer, UserAddressSerializer, CategorySerializer,
    BookSerializer, BookTransactionSerializer, BorrowRequestSerializer
)
from .permissions import IsLibrarian,IsBorrowerOrlibrarian
from rest_framework.throttling import AnonRateThrottle,UserRateThrottle
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly,AllowAny
from django.http import HttpResponse
import csv

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    def get_permissions(self):
        if self.action == 'create': 
            permission_classes = [AllowAny]
        else: 
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

class BookTransactionViewSet(viewsets.ModelViewSet):
    queryset = BookTransaction.objects.all()
    serializer_class = BookTransactionSerializer
    authentication_classes=[JWTAuthentication]        
    permission_classes=[IsAuthenticated,IsBorrowerOrlibrarian]   
    throttle_classes=[UserRateThrottle]
    def perform_create(self, serializer):
        user = self.request.user

        # Automatically assign the logged-in user as the borrower if they are a borrower
        if user.user_role == 'borrower':
            serializer.save(borrower=user)
        else: 
            serializer.save()
    def create(self, request, *args, **kwargs):
        serializer = BorrowRequestSerializer(data=request.data)
        if serializer.is_valid():
            book_id = serializer.validated_data['book_id']
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']

            try:
                book = Book.objects.get(id=book_id)
                
                # Check for book availability in the requested period
                if BookTransaction.objects.filter(
                    book=book,
                    status='approved',
                    expected_return_date__gte=start_date,
                    borrow_date__lte=end_date
                ).exists():
                    return Response({"error": "Book is not available for the requested dates."}, status=status.HTTP_400_BAD_REQUEST)

                # Find an available copy ISBN
                used_isbns = BookTransaction.objects.filter(
                    book=book,
                    status__in=['approved', 'pending']
                ).values_list('copy_isbn', flat=True)

                available_isbns = [isbn for isbn in book.copy_isbns if isbn not in used_isbns]

                if not available_isbns:
                    return Response({"error": "No available copies for this book."}, status=status.HTTP_400_BAD_REQUEST)

                # Assign an available ISBN
                copy_isbn = available_isbns[0]

            # Create and save the transaction
                transaction = BookTransaction.objects.create(
                    book=book,
                    borrower=request.user,
                    borrow_date=start_date,
                    expected_return_date=end_date,
                    status='pending',
                    copy_isbn=copy_isbn
                )
                return Response({"msg": "Transaction created successfully.", "transaction_id": transaction.id}, status=status.HTTP_201_CREATED)

            except Book.DoesNotExist:
                return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def download_borrow_history(self, request):
        transactions = BookTransaction.objects.filter(borrower=request.user)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="borrow_history.csv"'

        writer = csv.writer(response)
        writer.writerow(['Book Title', 'Borrow Date', 'Return Date', 'Status', 'Fine'])
        for transaction in transactions:
            writer.writerow([
                transaction.book.title,
                transaction.borrow_date,
                transaction.return_date or 'N/A',
                transaction.status,
                transaction.fine
            ])
        return response

class LibrarianViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def approve_or_reject_request(self, request, pk, action):
        try:
            transaction = BookTransaction.objects.get(id=pk)
            if action == 'approve':
                transaction.status = 'approved'
                transaction.save()
                return Response({"message": "Request approved."})
            elif action == 'reject':
                transaction.status = 'rejected'
                transaction.save()
                return Response({"message": "Request rejected."})
            else:
                return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)
        except BookTransaction.DoesNotExist:
            return Response({"error": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)
