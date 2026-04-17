from django.urls import path
from .views import QFAuthExchangeView, LogoutView

urlpatterns = [
    path("qf-exchange/", QFAuthExchangeView.as_view(), name="qf-exchange"),
    path("logout/", LogoutView.as_view(), name="logout"),
]