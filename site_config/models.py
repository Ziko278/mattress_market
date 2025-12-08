from django.db import models

from backend import settings


class SiteInfoModel(models.Model):
    site_name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='site/', storage=settings.STORAGE_BACKEND)
    phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField()
    whatsapp = models.CharField(max_length=20)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    address = models.TextField()

    class Meta:
        verbose_name = "Site Information"
        verbose_name_plural = "Site Information"

    def save(self, *args, **kwargs):
        if not self.pk and SiteInfoModel.objects.exists():
            raise ValueError('Only one Site Info instance allowed')
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.site_name


class SettingsModel(models.Model):
    allow_pay_on_delivery = models.BooleanField(default=True)
    allow_online_payment = models.BooleanField(default=True)
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    terms_and_conditions = models.TextField(blank=True)

    class Meta:
        verbose_name = "Settings"
        verbose_name_plural = "Settings"

    def save(self, *args, **kwargs):
        if not self.pk and SettingsModel.objects.exists():
            raise ValueError('Only one Settings instance allowed')
        return super().save(*args, **kwargs)

    def __str__(self):
        return "Site Settings"


class SliderModel(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='sliders/', storage=settings.STORAGE_BACKEND)
    brand = models.ForeignKey('products.BrandModel', on_delete=models.CASCADE, null=True, blank=True,
                              help_text="Leave empty for general slider")
    button_text = models.CharField(max_length=50, blank=True)
    button_link = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title