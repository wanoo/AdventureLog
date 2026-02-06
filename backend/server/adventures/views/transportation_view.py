from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.db.models.functions import Lower
from adventures.models import Transportation, TRANSPORTATION_TYPES
from adventures.serializers import TransportationSerializer
from rest_framework.exceptions import PermissionDenied
from adventures.permissions import IsOwnerOrSharedWithFullAccess
from adventures.utils import pagination

class TransportationViewSet(viewsets.ModelViewSet):
    queryset = Transportation.objects.all()
    serializer_class = TransportationSerializer
    permission_classes = [IsOwnerOrSharedWithFullAccess]
    pagination_class = pagination.StandardResultsSetPagination

    # ==================== SORTING & FILTERING ====================

    def apply_sorting(self, queryset):
        """Apply sorting to queryset."""
        order_by = self.request.query_params.get('order_by', 'updated_at')
        order_direction = self.request.query_params.get('order_direction', 'asc')

        # Validate parameters
        valid_order_by = ['name', 'date', 'rating', 'updated_at']
        if order_by not in valid_order_by:
            order_by = 'updated_at'

        if order_direction not in ['asc', 'desc']:
            order_direction = 'asc'

        return self._apply_ordering(queryset, order_by, order_direction)

    def _apply_ordering(self, queryset, order_by, order_direction):
        """Apply ordering to queryset based on field type."""
        if order_by == 'date':
            ordering = 'date'
        elif order_by == 'name':
            queryset = queryset.annotate(lower_name=Lower('name'))
            ordering = 'lower_name'
        elif order_by == 'rating':
            queryset = queryset.filter(rating__isnull=False)
            ordering = 'rating'
        elif order_by == 'updated_at':
            # Special handling for updated_at (reverse default order)
            ordering = '-updated_at' if order_direction == 'asc' else 'updated_at'
            return queryset.order_by(ordering)
        else:
            ordering = order_by

        # Apply direction
        if order_direction == 'desc':
            ordering = f'-{ordering}'

        return queryset.order_by(ordering)

    def paginate_and_respond(self, queryset, request):
        """Paginate queryset and return response."""
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=['get'])
    def filtered(self, request):
        """Filter transportations by type."""
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)

        types_param = request.query_params.get('types', '')
        types = types_param.split(',') if types_param else []

        # Get valid transportation types
        valid_types = [t[0] for t in TRANSPORTATION_TYPES]

        # Handle 'all' types
        if 'all' in types or not types:
            queryset = Transportation.objects.filter(user=request.user)
        else:
            # Filter by valid types only
            filtered_types = [t for t in types if t in valid_types]
            if not filtered_types:
                return Response(
                    {"error": "Invalid transportation type provided"},
                    status=400
                )
            queryset = Transportation.objects.filter(
                user=request.user,
                type__in=filtered_types
            )

        queryset = self.apply_sorting(queryset)
        return self.paginate_and_respond(queryset, request)

    # ==================== CRUD OPERATIONS ====================

    def list(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)
        queryset = Transportation.objects.filter(
            Q(user=request.user.id)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        user = self.request.user
        if self.action == 'retrieve':
            # For individual adventure retrieval, include public locations, user's own locations and shared locations
            return Transportation.objects.filter(
                Q(is_public=True) | Q(user=user.id) | Q(collection__shared_with=user.id)
            ).distinct().order_by('-updated_at')
        # For other actions, include user's own locations and shared locations
        return Transportation.objects.filter(
            Q(user=user.id) | Q(collection__shared_with=user.id)
        ).distinct().order_by('-updated_at')

    def partial_update(self, request, *args, **kwargs):
        # Retrieve the current object
        instance = self.get_object()
        user = request.user

        # Partially update the instance with the request data
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Retrieve the collection from the validated data
        new_collection = serializer.validated_data.get('collection')

        if new_collection is not None and new_collection != instance.collection:
            # Check if the user is the owner of the new collection
            if new_collection.user != user or instance.user != user:
                raise PermissionDenied("You do not have permission to use this collection.")
        elif new_collection is None:
            # Handle the case where the user is trying to set the collection to None
            if instance.collection is not None and instance.collection.user != user:
                raise PermissionDenied("You cannot remove the collection as you are not the owner.")
        
        # Perform the update
        self.perform_update(serializer)
        
        # Return the updated instance
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()
    
    # when creating an adventure, make sure the user is the owner of the collection or shared with the collection
    def perform_create(self, serializer):
        from django.conf import settings

        # Retrieve the collection from the validated data
        collection = serializer.validated_data.get('collection')

        # Check if a collection is provided
        if collection:
            user = self.request.user
            # Check if the user is the owner or is in the shared_with list
            if collection.user != user and not collection.shared_with.filter(id=user.id).exists():
                # Return an error response if the user does not have permission
                raise PermissionDenied("You do not have permission to use this collection.")

            # In collaborative mode, items are attributed to the creator, not the collection owner
            if getattr(settings, 'COLLABORATIVE_MODE', False):
                serializer.save(user=self.request.user)
            else:
                # if collection the owner of the adventure is the owner of the collection
                serializer.save(user=collection.user)
            return

        # Save the adventure with the current user as the owner
        serializer.save(user=self.request.user)