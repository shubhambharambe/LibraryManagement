from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import UserAdmin
from .models import User,Book,BookTransaction,Category 
from .models import User
from .forms import UserChangeForm
from .models import User_Address
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances can be added if needed
    # form = UserChangeForm  # Custom change form (optional)
    # add_form = UserCreationForm  # Custom add form (optional)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'mobile_no', 'user_role')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Address Info'), {'fields': ('u_address',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'mobile_no', 'user_role', 'u_address', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'mobile_no')
    ordering = ('email',)
# admin.site.register(User, UserAdmin)
@admin.register(Book)

class BookModel(admin.ModelAdmin):
    list_display=['id','title','genre','isbn','published_date','category','created_by','total_copies','available_copies']
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            if request.user.user_role == 'librarian':
                obj.created_by = request.user.username
        super().save_model(request, obj, form, change)
@admin.register(BookTransaction)

class BookTransactionAdmin(admin.ModelAdmin):
  list_display=['book','borrower','copy_isbn','fine','borrow_date','return_date','status']
  
 
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display=['name','description']
@admin.register(User_Address)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('line1', 'line2', 'city', 'pincode')  # Fields displayed in the admin list view
    search_fields = ('city', 'pincode')  # Fields to search in the admin interface
    list_filter = ('city',)  # Filter options in the admin interface