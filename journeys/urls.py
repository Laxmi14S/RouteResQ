from django.urls import path
from . import views

urlpatterns = [
    path("", views.api_home, name="api_home"),
    path("routes/", views.route_list, name="route_list"),
    path("recovery/", views.recover_journey, name="recover_journey"),
]