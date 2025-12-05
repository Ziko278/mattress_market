from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SiteInfoModel, SettingsModel, SliderModel
from .serializers import SiteInfoSerializer, SettingsSerializer, SliderSerializer


class SiteInfoView(APIView):
    def get(self, request):
        try:
            site_info = SiteInfoModel.objects.first()
            serializer = SiteInfoSerializer(site_info, context={'request': request})  # Add context
            return Response(serializer.data)
        except:
            return Response({"error": "Site info not found"}, status=status.HTTP_404_NOT_FOUND)


class SettingsView(APIView):
    def get(self, request):
        try:
            settings = SettingsModel.objects.first()
            serializer = SettingsSerializer(settings, context={'request': request})  # Add context
            return Response(serializer.data)
        except:
            return Response({"error": "Settings not found"}, status=status.HTTP_404_NOT_FOUND)


class SliderListView(APIView):
    """
    Get all active sliders ordered by 'order' field
    Can filter by brand: /api/sliders/?brand=1
    """
    def get(self, request):
        brand_id = request.query_params.get('brand', None)
        sliders = SliderModel.objects.filter(is_active=True)
        
        if brand_id:
            sliders = sliders.filter(brand_id=brand_id)
        
        serializer = SliderSerializer(sliders, many=True, context={'request': request})  # Add context
        return Response(serializer.data)
    

    