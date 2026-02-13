from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
import requests
from adventures.models import Lodging, LODGING_TYPES, AuditLog, ContentImage, ContentAttachment
from adventures.serializers import LodgingSerializer, LodgingMapPinSerializer, AuditLogSerializer
from rest_framework.exceptions import PermissionDenied
from adventures.permissions import IsOwnerOrSharedWithFullAccess
from rest_framework.permissions import IsAuthenticated
from adventures.utils import pagination
from adventures.utils.filtering import FilteringMixin
from adventures.utils.viewset_mixins import ViewsetUtilsMixin

class LodgingViewSet(FilteringMixin, ViewsetUtilsMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing Lodging objects.

    Inherits filtering and sorting from mixins:
    - FilteringMixin: _apply_visit_filtering, _apply_public_filtering,
                      _apply_ownership_filtering, _apply_rating_filtering
    - ViewsetUtilsMixin: apply_sorting, paginate_and_respond
    """
    queryset = Lodging.objects.all()
    serializer_class = LodgingSerializer
    permission_classes = [IsOwnerOrSharedWithFullAccess]
    pagination_class = pagination.StandardResultsSetPagination

    # Override valid_order_fields from SortingMixin
    valid_order_fields = ['name', 'last_visit', 'rating', 'updated_at', 'created_at']

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=['get'], url_path='pins')
    def pins(self, request):
        """Get all lodging with coordinates for map display."""
        if not request.user.is_authenticated:
            return Response({"error": "User is not authenticated"}, status=400)

        is_collaborative = getattr(settings, 'COLLABORATIVE_MODE', False)

        if is_collaborative:
            base_filter = Q(user=request.user) | Q(is_public=True) | Q(collections__shared_with=request.user)
        else:
            base_filter = Q(user=request.user) | Q(collections__shared_with=request.user)

        # Only get lodging with coordinates
        lodgings = Lodging.objects.filter(
            base_filter,
            latitude__isnull=False,
            longitude__isnull=False
        ).distinct()

        serializer = LodgingMapPinSerializer(lodgings, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='additional-info')
    def additional_info(self, request, pk=None):
        """Get lodging with additional sunrise/sunset information."""
        lodging = self.get_object()

        # Get base lodging data
        serializer = self.get_serializer(lodging)
        response_data = serializer.data

        # Add sunrise/sunset data
        response_data['sun_times'] = self._get_sun_times(lodging, response_data.get('visits', []))

        return Response(response_data)

    def _get_sun_times(self, lodging, visits):
        """Get sunrise/sunset times for lodging visits."""
        sun_times = []

        for visit in visits:
            date = visit.get('start_date')
            if not (date and lodging.longitude and lodging.latitude):
                continue

            api_url = (
                f'https://api.sunrisesunset.io/json?'
                f'lat={lodging.latitude}&lng={lodging.longitude}&date={date}'
            )

            try:
                response = requests.get(api_url)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', {})

                    if results.get('sunrise') and results.get('sunset'):
                        sun_times.append({
                            "date": date,
                            "visit_id": visit.get('id'),
                            "sunrise": results.get('sunrise'),
                            "sunset": results.get('sunset')
                        })
            except requests.RequestException:
                # Skip this visit if API call fails
                continue

        return sun_times

    @action(detail=False, methods=['get'])
    def filtered(self, request):
        """Filter lodging by type, visit status, and visibility."""
        from django.conf import settings

        if not request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)

        types_param = request.query_params.get('types', '')
        types = types_param.split(',') if types_param else []
        is_collaborative = getattr(settings, 'COLLABORATIVE_MODE', False)

        # Get valid lodging types
        valid_types = [t[0] for t in LODGING_TYPES]

        # Build base queryset - include public items in collaborative mode
        if is_collaborative:
            base_filter = Q(user=request.user) | Q(is_public=True) | Q(collections__shared_with=request.user)
        else:
            base_filter = Q(user=request.user) | Q(collections__shared_with=request.user)

        # Handle 'all' types
        if 'all' in types or not types:
            queryset = Lodging.objects.filter(base_filter).distinct()
        else:
            # Filter by valid types only
            filtered_types = [t for t in types if t in valid_types]
            if not filtered_types:
                return Response(
                    {"error": "Invalid lodging type provided"},
                    status=400
                )
            queryset = Lodging.objects.filter(
                base_filter,
                type__in=filtered_types
            ).distinct()

        # Apply visit and public filters
        queryset = self._apply_visit_filtering(queryset, request)
        queryset = self._apply_public_filtering(queryset, request)
        queryset = self._apply_ownership_filtering(queryset, request)
        queryset = self._apply_rating_filtering(queryset, request)

        queryset = self.apply_sorting(queryset)
        return self.paginate_and_respond(queryset, request)

    # ==================== CRUD OPERATIONS ====================

    def list(self, request, *args, **kwargs):
        from django.conf import settings

        if not request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)

        is_collaborative = getattr(settings, 'COLLABORATIVE_MODE', False)

        # In collaborative mode, include public items
        if is_collaborative:
            queryset = Lodging.objects.filter(
                Q(user=request.user.id) | Q(is_public=True) | Q(collections__shared_with=request.user.id)
            ).distinct()
        else:
            queryset = Lodging.objects.filter(
                Q(user=request.user.id) | Q(collections__shared_with=request.user.id)
            ).distinct()

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        from django.conf import settings

        user = self.request.user
        is_collaborative = getattr(settings, 'COLLABORATIVE_MODE', False)

        if self.action == 'retrieve':
            # For individual retrieval, include public, user's own, and shared
            return Lodging.objects.filter(
                Q(is_public=True) | Q(user=user.id) | Q(collections__shared_with=user.id)
            ).distinct().order_by('-updated_at')

        # In collaborative mode, include public items for all actions (except destroy)
        if is_collaborative and self.action != 'destroy':
            return Lodging.objects.filter(
                Q(is_public=True) | Q(user=user.id) | Q(collections__shared_with=user.id)
            ).distinct().order_by('-updated_at')

        # For other actions, include user's own and shared
        return Lodging.objects.filter(
            Q(user=user.id) | Q(collections__shared_with=user.id)
        ).distinct().order_by('-updated_at')

    def partial_update(self, request, *args, **kwargs):
        # Retrieve the current object
        instance = self.get_object()
        user = request.user

        # Partially update the instance with the request data
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Retrieve the collections from the validated data
        new_collections = serializer.validated_data.get('collections')

        if new_collections is not None:
            # Check if the user is the owner of all new collections
            for collection in new_collections:
                if collection.user != user:
                    raise PermissionDenied("You do not have permission to use this collection.")

        # Perform the update
        self.perform_update(serializer)

        # Return the updated instance
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()
    
    # when creating an adventure, make sure the user is the owner of the collection or shared with the collection
    def perform_create(self, serializer):
        from django.conf import settings

        # Retrieve the collections from the validated data
        collections = serializer.validated_data.get('collections', [])

        user = self.request.user

        # Check if collections are provided
        if collections:
            # Check if the user is the owner or is in the shared_with list for all collections
            for collection in collections:
                if collection.user != user and not collection.shared_with.filter(id=user.id).exists():
                    raise PermissionDenied("You do not have permission to use this collection.")

        # Save the adventure with the current user as the owner
        serializer.save(user=user)

    # ==================== HISTORY & REVERT (Collaborative Mode) ====================

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        """Get audit history for a lodging and its related content (collaborative mode only)."""
        if not getattr(settings, 'COLLABORATIVE_MODE', False):
            return Response({"error": "History is only available in collaborative mode"}, status=400)

        lodging = self.get_object()

        # Get content types for lodging, images, and attachments
        lodging_ct = ContentType.objects.get_for_model(Lodging)
        image_ct = ContentType.objects.get_for_model(ContentImage)
        attachment_ct = ContentType.objects.get_for_model(ContentAttachment)

        # Get IDs of images and attachments belonging to this lodging (including soft-deleted)
        image_ids = list(lodging.images.all().values_list('id', flat=True))
        attachment_ids = list(lodging.attachments.all().values_list('id', flat=True))

        # Build query for all related logs
        logs_query = Q(content_type=lodging_ct, object_id=lodging.pk)

        if image_ids:
            logs_query |= Q(content_type=image_ct, object_id__in=image_ids)

        if attachment_ids:
            logs_query |= Q(content_type=attachment_ct, object_id__in=attachment_ids)

        logs = AuditLog.objects.filter(logs_query).select_related('user').order_by('-timestamp')[:50]
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='revert/(?P<log_id>[^/.]+)')
    def revert(self, request, pk=None, log_id=None):
        """Revert a specific audit log entry (collaborative mode only)."""
        if not getattr(settings, 'COLLABORATIVE_MODE', False):
            return Response({"error": "Revert is only available in collaborative mode"}, status=400)

        lodging = self.get_object()

        # Get the audit log entry
        try:
            log_entry = AuditLog.objects.get(id=log_id)
        except AuditLog.DoesNotExist:
            return Response({"error": "Audit log entry not found"}, status=404)

        # Verify the log entry belongs to this lodging or its related content
        lodging_ct = ContentType.objects.get_for_model(Lodging)
        image_ct = ContentType.objects.get_for_model(ContentImage)
        attachment_ct = ContentType.objects.get_for_model(ContentAttachment)

        is_lodging_log = log_entry.content_type == lodging_ct and str(log_entry.object_id) == str(lodging.pk)
        is_image_log = log_entry.content_type == image_ct and lodging.images.filter(id=log_entry.object_id).exists()
        is_attachment_log = log_entry.content_type == attachment_ct and lodging.attachments.filter(id=log_entry.object_id).exists()

        if not (is_lodging_log or is_image_log or is_attachment_log):
            return Response({"error": "This audit log entry does not belong to this lodging"}, status=403)

        # Check permission: only the user who made the change, the lodging owner, or an admin can revert
        can_revert = (
            log_entry.user == request.user or
            lodging.user == request.user or
            request.user.is_staff
        )
        if not can_revert:
            return Response({"error": "You don't have permission to revert this change"}, status=403)

        model_class = log_entry.content_type.model_class()

        try:
            if log_entry.action == 'create':
                # Revert create = delete the object
                obj = model_class.objects.get(pk=log_entry.object_id)
                if model_class in [ContentImage, ContentAttachment]:
                    obj.deleted_by = request.user
                    obj.save(update_fields=['deleted_by'])
                obj.delete()
                return Response({"success": f"Reverted creation of {log_entry.object_repr}"})

            elif log_entry.action == 'update':
                # Revert update = restore old values
                obj = model_class.objects.get(pk=log_entry.object_id)
                changes = log_entry.changes or {}

                for field_name, values in changes.items():
                    old_value = values.get('old')
                    if old_value is not None and hasattr(obj, field_name):
                        field = obj._meta.get_field(field_name)
                        # Handle different field types
                        if field.get_internal_type() in ['FloatField', 'DecimalField']:
                            try:
                                setattr(obj, field_name, float(old_value) if old_value != 'None' else None)
                            except (ValueError, TypeError):
                                setattr(obj, field_name, None)
                        elif field.get_internal_type() == 'IntegerField':
                            try:
                                setattr(obj, field_name, int(old_value) if old_value != 'None' else None)
                            except (ValueError, TypeError):
                                setattr(obj, field_name, None)
                        elif field.get_internal_type() == 'BooleanField':
                            setattr(obj, field_name, old_value.lower() == 'true')
                        elif field.get_internal_type() in ['CharField', 'TextField']:
                            setattr(obj, field_name, old_value if old_value != 'None' else None)
                        # Skip ForeignKey and other complex fields for now

                obj.save()
                return Response({"success": f"Reverted update of {log_entry.object_repr}"})

            elif log_entry.action == 'delete':
                # Revert delete = restore soft-deleted object
                if model_class == ContentImage:
                    obj = ContentImage.objects.get(pk=log_entry.object_id)
                    obj.restore()
                    return Response({"success": "Restored deleted image"})
                elif model_class == ContentAttachment:
                    obj = ContentAttachment.objects.get(pk=log_entry.object_id)
                    obj.restore()
                    return Response({"success": "Restored deleted attachment"})
                else:
                    return Response({"error": "Cannot revert hard delete"}, status=400)

            else:
                return Response({"error": f"Unknown action: {log_entry.action}"}, status=400)

        except model_class.DoesNotExist:
            return Response({"error": "Object no longer exists"}, status=404)
        except Exception as e:
            return Response({"error": f"Failed to revert: {str(e)}"}, status=500)