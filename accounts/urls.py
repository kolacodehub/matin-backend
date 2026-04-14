from django.urls import path
from .views import QFAuthExchangeView, qf_login_redirect, qf_callback

urlpatterns = [
    path("qf-exchange/", QFAuthExchangeView.as_view(), name="qf-exchange"),
    path("login/", qf_login_redirect, name="qf-login"),
    path("callback/", qf_callback, name="qf-callback"),
]