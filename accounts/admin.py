from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('qf_sub_id', 'is_staff', 'is_superuser', 'timezone')