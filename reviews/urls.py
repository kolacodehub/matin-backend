from django.urls import path
from .views import IngestReflectionView

urlpatterns = [
    path("ingest/", IngestReflectionView.as_view(), name="ingest-reflection"),
]
