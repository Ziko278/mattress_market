from rest_framework import serializers
from .models import SiteInfoModel, SettingsModel, SliderModel


class SiteInfoSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    
    class Meta:
        model = SiteInfoModel
        fields = '__all__'
    
    def get_logo(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
        return None


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SettingsModel
        fields = '__all__'


class SliderSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = SliderModel
        fields = ['id', 'title', 'subtitle', 'image', 'brand', 'brand_name', 'button_text', 'button_link', 'order', 'is_active']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None