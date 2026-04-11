from django.contrib import admin
from .models import Reflection, ReviewLog


@admin.register(Reflection)
class ReflectionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "ayah_key",
        "interval",
        "repetitions",
        "ease_factor",
        "next_review_date",
        "is_active",
    ]
    list_filter = ["is_active", "next_review_date"]
    search_fields = ["ayah_key", "user__username", "reflection_text"]
    ordering = ["next_review_date"]
    readonly_fields = ["created_at", "total_points_earned"]


@admin.register(ReviewLog)
class ReviewLogAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "reflection",
        "grade",
        "points_awarded",
        "was_in_grace_period",
        "reviewed_at",
    ]
    list_filter = ["grade", "was_in_grace_period"]
    search_fields = ["user__username"]
    ordering = ["-reviewed_at"]
    readonly_fields = ["reviewed_at"]
