from django.urls import path

from iot.views import (
    CreateControllerView,
    SiteListView,
    CreateSiteView,
    DeleteSiteView,
    ControllerListView,
    DeleteControllerView,
    CreateUserTokenView,
    DeleteUserTokenView,
)

app_name = "iot"

urlpatterns = [
    path("sites/", SiteListView.as_view(), name="site-list"),
    path("site/", CreateSiteView.as_view(), name="create-site"),
    path("site/<uuid:pk>/delete/", DeleteSiteView.as_view(), name="delete-site"),
    path("controllers/", ControllerListView.as_view(), name="controller-list"),
    path("controller/", CreateControllerView.as_view(), name="create-controller"),
    path("controller/<uuid:pk>/delete/", DeleteControllerView.as_view(), name="delete-controller"),
    path("user_token/", CreateUserTokenView.as_view(), name="create-user-token"),
    path("user_token/<str:pk>/delete/", DeleteUserTokenView.as_view(), name="delete-user-token"),
]