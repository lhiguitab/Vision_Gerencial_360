from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Negotiator, AllowedEmail
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ('cedula', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('cedula', 'email', 'first_name', 'last_name')
    ordering = ('cedula',)

    # Personalizar los campos que se muestran al editar/crear un usuario
    fieldsets = (
        (None, {'fields': ('cedula', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Custom Fields', {'fields': ('role',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('cedula', 'password', 'password2', 'email', 'first_name', 'last_name', 'role'),
        }),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Negotiator)
admin.site.register(AllowedEmail)