from apps.emails.applications import AccountActivation
from .views.account_management import SendTokenAPIView, AccountActivationView
from django.urls import path


urlpatterns = [
    path(
        route="token/activation/<str:user_uuidb64>/<str:token>/",
        view=AccountActivationView.as_view(
            path_send_mail="send_activation_mail",
        ),
        name="account_activation",
    ),
    path(
        route="send/activation/<str:user_uuid>/",
        view=SendTokenAPIView.as_view(
            application_class=AccountActivation,
            action=AccountActivation.action,
        ),
        name="send_activation_mail",
    ),
]
