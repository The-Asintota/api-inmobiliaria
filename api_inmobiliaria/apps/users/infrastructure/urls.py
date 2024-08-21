from django.urls import path
from .views import (
    RegisterSearcherAPIView,
    SearcherAPIView,
    AuthenticationAPIView,
    UpdateTokenAPIView,
    LogoutAPIView,
)


urlpatterns = [
    path(
        route="searcher/",
        view=RegisterSearcherAPIView.as_view(),
        name="register_searcher_user",
    ),
    path(
        route="searcher/<str:user_uuid>/",
        view=SearcherAPIView.as_view(),
        name="searcher_user",
    ),
    path(
        route="jwt/login/",
        view=AuthenticationAPIView.as_view(),
        name="jwt_authenticate_user",
    ),
    path(
        route="jwt/update/",
        view=UpdateTokenAPIView.as_view(),
        name="update_jwt",
    ),
    path(
        route="jwt/logout/",
        view=LogoutAPIView.as_view(),
        name="jwt_logout_user",
    ),
]
