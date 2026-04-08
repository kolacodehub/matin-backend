from django.urls import path
from .views import QFAuthExchangeView

urlpatterns = [
    path("auth/qf-exchange/", QFAuthExchangeView.as_view(), name="qf-exchange"),
]
