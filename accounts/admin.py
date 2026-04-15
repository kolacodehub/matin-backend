from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Sum

from reviews.models import ReviewLog

User = get_user_model()


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("qf_sub_id", "calculated_balance", "is_active", "is_staff")

    search_fields = ("qf_sub_id",)

    def calculated_balance(self, obj):
        # This sums up every point awarded to this user in the ReviewLog ledger
        result = ReviewLog.objects.filter(user=obj).aggregate(
            total=Sum("points_awarded")
        )["total"]
        return result or 0

    # Give the column a nice name in the Admin UI
    calculated_balance.short_description = "Points Balance"


# 4. Safely handle registration
if admin.site.is_registered(User):
    admin.site.unregister(User)

admin.site.register(User, CustomUserAdmin)
