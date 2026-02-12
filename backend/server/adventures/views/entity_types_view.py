from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from adventures.models import TransportationType, LodgingType, ActivityType
from adventures.serializers import TransportationTypeSerializer, LodgingTypeSerializer, ActivityTypeSerializer


class TransportationTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for transportation types.
    Read-only - types are managed via Django admin.
    """
    queryset = TransportationType.objects.filter(is_active=True)
    serializer_class = TransportationTypeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Return all types without pagination


class LodgingTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for lodging types.
    Read-only - types are managed via Django admin.
    """
    queryset = LodgingType.objects.filter(is_active=True)
    serializer_class = LodgingTypeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Return all types without pagination


class ActivityTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for activity types.
    Read-only - types are managed via Django admin.
    """
    queryset = ActivityType.objects.filter(is_active=True)
    serializer_class = ActivityTypeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Return all types without pagination
