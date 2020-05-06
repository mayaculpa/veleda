from django.urls import path

from . import views

app_name = 'farms'

urlpatterns = [
    path("sites/", views.SiteListView.as_view(), name="site-list"),
    path("site-setup/", views.SiteSetupView.as_view(), name="site-setup",),
    path(
        "coordinator-setup/",
        views.CoordinatorSetupSelectView.as_view(),
        name="coordinator-setup-select",
    ),
    path(
        "coordinator-setup/<uuid:pk>/",
        views.CoordinatorSetupRegisterView.as_view(),
        name="coordinator-setup-register",
    )
]
