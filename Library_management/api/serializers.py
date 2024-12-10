from rest_framework import serializers
from .models import User, User_Address, Category, Book, BookTransaction
from django.db.models import Q
class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = User_Address
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    u_address = serializers.PrimaryKeyRelatedField(queryset=User_Address.objects.all()) 
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'mobile_no', 'user_role', 'u_address']
    def create(self, validated_data):
        address = validated_data.pop('u_address')

        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            mobile_no=validated_data.get('mobile_no'),
            user_role=validated_data.get('user_role'),
            u_address=validated_data.get('u_address'),
        )
        user = User.objects.create(**validated_data, u_address=address)
        user.set_password(validated_data['password'])  # Hash the password
        user.save()
        return user
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class BookTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookTransaction
        fields = '__all__'
    def validate(self, data):
        book_id = data.get('book_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if end_date <= start_date:
            raise serializers.ValidationError("End date must be after start date.")

        # Check if the book copy is already borrowed during the specified period
        overlapping_transactions = BookTransaction.objects.filter(
            Q(book__id=book_id),
            Q(status__in=['pending', 'approved']),
            Q(expected_return_date__gte=start_date),
            Q(borrow_date__lte=end_date)
        )
        if overlapping_transactions.exists():
            raise serializers.ValidationError("The book is already borrowed for the specified period.")

        return data

class BorrowRequestSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
