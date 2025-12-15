from django.urls import path

from .views import phone_lookup_view

app_name = "app"

urlpatterns = [
    path("", phone_lookup_view, name="phone_lookup"),
]
