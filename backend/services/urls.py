from django.urls import path
from .views import blood_centers_nearby, blood_centers_all

urlpatterns = [
    path("blood-centers-nearby/", blood_centers_nearby, name="blood_centers_nearby"),
    path('blood-centers/', blood_centers_all, name='blood_centers_all'),
]