from django.urls import path
from .views import AccountActivationView, AccountActivationEmailAPIView


urlpatterns = [
    path(
        route="token/activation/<str:user_uuidb64>/<str:token>/",
        view=AccountActivationView.as_view(),
        name="account_activation",
    ),
    path(
        route="send/activation/<str:user_uuid>/",
        view=AccountActivationEmailAPIView.as_view(),
        name="account_activation_email",
    ),
]
