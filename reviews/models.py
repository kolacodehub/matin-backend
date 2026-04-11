from django.db import models
from django.conf import settings
from django.utils import timezone


class Reflection(models.Model):
    # Ownership & Content
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reflections"
    )
    ayah_key = models.CharField(max_length=20)  # e.g. "2:255"
    reflection_text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    # SRS Algorithm State (SM-2)
    ease_factor = models.FloatField(default=2.5)
    interval = models.IntegerField(default=0)
    repetitions = models.IntegerField(default=0)

    # Scheduling
    next_review_date = models.DateTimeField(default=timezone.now)

    # Economy Cache
    total_points_earned = models.IntegerField(default=0)

    class Meta:
        ordering = ["next_review_date"]

    def __str__(self):
        return f"Reflection {self.id} ({self.ayah_key}) - {self.user.qf_sub_id}"


class ReviewLog(models.Model):
    GRADE_CHOICES = [
        (0, "Forgot / Complete Failure"),
        (1, "Hard / Remembered with immense effort"),
        (2, "Good / Remembered after hesitation"),
        (3, "Easy / Perfect recall"),
    ]

    # Ownership
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_logs"
    )
    reflection = models.ForeignKey(
        Reflection, on_delete=models.CASCADE, related_name="review_logs", null=True, blank=True
    )

    # The Action
    reviewed_at = models.DateTimeField(default=timezone.now)
    grade = models.IntegerField(choices=GRADE_CHOICES, null=True, blank=True)
    
    # The Economic Result
    points_awarded = models.IntegerField()
    was_in_grace_period = models.BooleanField(default=False)

    class Meta:
        ordering = ["-reviewed_at"]
        indexes = [
            models.Index(fields=["reviewed_at"]),
        ]

    def __str__(self):
        return f"Log {self.id} - Ref {self.reflection.id} - Grade {self.grade}"
