from django.db import models

class BloodCenter(models.Model):
    name = models.CharField(max_length=100, verbose_name="헌혈의 집")
    address = models.CharField(max_length=255, verbose_name="주소지")
    phone = models.CharField(max_length=20, verbose_name="전화번호", blank=True)
    center_type = models.CharField(max_length=50, verbose_name="구분", blank=True)
    blood_office = models.CharField(max_length=50, verbose_name="혈액원", blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name
