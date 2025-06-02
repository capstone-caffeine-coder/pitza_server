from django.urls import path
from . import views

urlpatterns = [
    # 기부
    path('donations/', views.DonationPostList.as_view(), name='donation-list'),
    path('donations/create/', views.DonationPostCreate.as_view(), name='donation-create'),
    path('donations/<int:pk>/', views.DonationPostDetail.as_view(), name='donation-detail'),

    # 요청
    path('requests/', views.RequestPostList.as_view(), name='request-list'),
    path('requests/create/', views.RequestPostCreate.as_view(), name='request-create'),
    path('requests/<int:pk>/', views.RequestPostDetail.as_view(), name='request-detail'),
]