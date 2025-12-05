from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from .models import SiteInfoModel, SettingsModel, SliderModel
from .serializers import SiteInfoSerializer, SettingsSerializer, SliderSerializer


# ==================== SITE INFO MANAGEMENT ====================

class AdminSiteInfoView(APIView):
    """
    Admin: Get or update site information (singleton)
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            site_info = SiteInfoModel.objects.first()
            if not site_info:
                return Response({"error": "Site info not configured"}, status=status.HTTP_404_NOT_FOUND)
            serializer = SiteInfoSerializer(site_info)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            # Get or create site info (singleton)
            site_info = SiteInfoModel.objects.first()
            if not site_info:
                site_info = SiteInfoModel.objects.create(**request.data)
                serializer = SiteInfoSerializer(site_info)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            # Update existing
            serializer = SiteInfoSerializer(site_info, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==================== SETTINGS MANAGEMENT ====================

class AdminSettingsView(APIView):
    """
    Admin: Get or update site settings (singleton)
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            settings = SettingsModel.objects.first()
            if not settings:
                return Response({"error": "Settings not configured"}, status=status.HTTP_404_NOT_FOUND)
            serializer = SettingsSerializer(settings)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            # Get or create settings (singleton)
            settings = SettingsModel.objects.first()
            if not settings:
                settings = SettingsModel.objects.create(**request.data)
                serializer = SettingsSerializer(settings)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            # Update existing
            serializer = SettingsSerializer(settings, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==================== SLIDER MANAGEMENT ====================

class AdminSliderListCreateView(APIView):
    """
    Admin: List all sliders or create new slider
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        sliders = SliderModel.objects.all().order_by('order')
        serializer = SliderSerializer(sliders, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SliderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminSliderDetailView(APIView):
    """
    Admin: Get, update, or delete a slider
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            slider = SliderModel.objects.get(pk=pk)
            serializer = SliderSerializer(slider)
            return Response(serializer.data)
        except SliderModel.DoesNotExist:
            return Response({"error": "Slider not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            slider = SliderModel.objects.get(pk=pk)
            serializer = SliderSerializer(slider, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except SliderModel.DoesNotExist:
            return Response({"error": "Slider not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            slider = SliderModel.objects.get(pk=pk)
            slider.delete()
            return Response({"message": "Slider deleted"}, status=status.HTTP_200_OK)
        except SliderModel.DoesNotExist:
            return Response({"error": "Slider not found"}, status=status.HTTP_404_NOT_FOUND)


class AdminSliderToggleView(APIView):
    """
    Admin: Toggle slider active status
    """
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            slider = SliderModel.objects.get(pk=pk)
            slider.is_active = not slider.is_active
            slider.save()
            return Response({
                "message": "Slider status updated",
                "is_active": slider.is_active
            })
        except SliderModel.DoesNotExist:
            return Response({"error": "Slider not found"}, status=status.HTTP_404_NOT_FOUND)
        