from django.contrib import admin
from .models import DonationRequest, SelectedMatchRequest, RejectedMatchRequest
# Register your models here.

admin.site.register(DonationRequest)
admin.site.register(SelectedMatchRequest)
admin.site.register(RejectedMatchRequest)
