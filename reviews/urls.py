from django.urls import path
from .views import (
    IngestReflectionView,
    ReviewQueueView,
    GradeReviewView,
    BalanceView,
    BuyGracePeriodView,
)

urlpatterns = [
    path("ingest/", IngestReflectionView.as_view(), name="ingest-reflection"),
    path("queue/", ReviewQueueView.as_view(), name="review-queue"),
    path("grade/", GradeReviewView.as_view(), name="grade-review"),
    path("buy-grace/", BuyGracePeriodView.as_view(), name="buy-grace"),
    path("balance/", BalanceView.as_view(), name="balance"), 
]
