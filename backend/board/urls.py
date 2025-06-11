from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 기부
    path('donation-cards/donate/', views.DonationPostList.as_view(), name='donation-list'),
    path('donation-cards/donate/create/', views.DonationPostCreate.as_view(), name='donation-create'),
    path('donation-cards/donate/<int:pk>/', views.DonationPostDetail.as_view(), name='donation-detail'),

    # 요청
    path('donation-cards/request/', views.RequestPostList.as_view(), name='request-list'),
    path('donation-cards/request/create/', views.RequestPostCreate.as_view(), name='request-create'),
    path('donation-cards/request/<int:pk>/', views.RequestPostDetail.as_view(), name='request-detail'),
]

if settings.DEBUG:
    urlpatterns += static('/media/', document_root='media')