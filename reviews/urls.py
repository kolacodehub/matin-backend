from django.urls import path
from .views import IngestReflectionView, ReviewQueueView, GradeReviewView

urlpatterns = [
    path("ingest/", IngestReflectionView.as_view(), name="ingest-reflection"),
    path("queue/", ReviewQueueView.as_view(), name="review-queue"),
    path(
        "grade/", GradeReviewView.as_view(), name="grade-review"
    ),  # The final endpoint
]
