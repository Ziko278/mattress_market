from django.contrib import admin
from site_config.models import SettingsModel, SiteInfoModel, SliderModel

admin.site.register(SliderModel)
admin.site.register(SiteInfoModel)
admin.site.register(SettingsModel)