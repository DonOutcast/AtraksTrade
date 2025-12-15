from django.urls import path

from .views import api_phone_info

app_name = "app"

urlpatterns = [
    path("api/phone-info/", api_phone_info, name="api_phone_info"),
]
