"""
MCP Tools for AdventureLog.

Provides AI agents with tools to interact with AdventureLog:
- search_items: Search locations, transportations, and lodging
- get_item: Get full details of a single item
- create_location: Create a new location
- create_visit: Add a visit to an entity
- list_collections: List user's trip collections
- add_to_collection: Add an item to a collection
"""

from typing import Optional
from mcp_server import MCPToolset
from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery


class AdventureLogTools(MCPToolset):
    """MCP tools for AdventureLog."""

    def search_items(
        self,
        query: str,
        item_type: str = "all",
        limit: int = 10
    ) -> list:
        """
        Search for locations, transportations, or lodging.

        Args:
            query: Search text to find items by name, description, or location
            item_type: Type of item to search for. Options: "location", "transportation", "lodging", or "all"
            limit: Maximum number of results to return (default 10, max 50)

        Returns:
            List of matching items with basic info (id, name, type, description excerpt)
        """
        from adventures.models import Location, Transportation, Lodging

        user = self.request.user
        limit = min(limit, 50)  # Cap at 50
        results = []

        if item_type in ("all", "location"):
            locations = Location.objects.annotate(
                search=SearchVector('name', 'description', 'location')
            ).filter(
                search=SearchQuery(query),
                user=user
            )[:limit]

            for loc in locations:
                results.append({
                    "type": "location",
                    "id": str(loc.id),
                    "name": loc.name,
                    "description": (loc.description or "")[:200],
                    "location": loc.location,
                    "is_public": loc.is_public,
                    "latitude": float(loc.latitude) if loc.latitude else None,
                    "longitude": float(loc.longitude) if loc.longitude else None,
                })

        if item_type in ("all", "transportation"):
            transportations = Transportation.objects.annotate(
                search=SearchVector('name', 'description', 'from_location', 'to_location', 'flight_number')
            ).filter(
                search=SearchQuery(query),
                user=user
            )[:limit]

            for t in transportations:
                results.append({
                    "type": "transportation",
                    "id": str(t.id),
                    "name": t.name,
                    "description": (t.description or "")[:200],
                    "transportation_type": t.type,
                    "from_location": t.from_location,
                    "to_location": t.to_location,
                    "is_public": t.is_public,
                })

        if item_type in ("all", "lodging"):
            lodgings = Lodging.objects.annotate(
                search=SearchVector('name', 'description', 'location', 'reservation_number')
            ).filter(
                search=SearchQuery(query),
                user=user
            )[:limit]

            for l in lodgings:
                results.append({
                    "type": "lodging",
                    "id": str(l.id),
                    "name": l.name,
                    "description": (l.description or "")[:200],
                    "lodging_type": l.type,
                    "location": l.location,
                    "is_public": l.is_public,
                    "latitude": float(l.latitude) if l.latitude else None,
                    "longitude": float(l.longitude) if l.longitude else None,
                })

        return results[:limit]

    def get_item(self, item_type: str, item_id: str) -> dict:
        """
        Get full details of a location, transportation, or lodging.

        Args:
            item_type: Type of item. Options: "location", "transportation", or "lodging"
            item_id: UUID of the item

        Returns:
            Full item details including visits, collections, and images
        """
        from adventures.models import Location, Transportation, Lodging
        from adventures.serializers import LocationSerializer, TransportationSerializer, LodgingSerializer

        user = self.request.user

        if item_type == "location":
            try:
                location = Location.objects.get(
                    Q(id=item_id) & (Q(user=user) | Q(is_public=True))
                )
                serializer = LocationSerializer(location, context={'request': self.request})
                return {"type": "location", **serializer.data}
            except Location.DoesNotExist:
                return {"error": f"Location {item_id} not found or not accessible"}

        elif item_type == "transportation":
            try:
                transportation = Transportation.objects.get(
                    Q(id=item_id) & (Q(user=user) | Q(is_public=True))
                )
                serializer = TransportationSerializer(transportation, context={'request': self.request})
                return {"type": "transportation", **serializer.data}
            except Transportation.DoesNotExist:
                return {"error": f"Transportation {item_id} not found or not accessible"}

        elif item_type == "lodging":
            try:
                lodging = Lodging.objects.get(
                    Q(id=item_id) & (Q(user=user) | Q(is_public=True))
                )
                serializer = LodgingSerializer(lodging, context={'request': self.request})
                return {"type": "lodging", **serializer.data}
            except Lodging.DoesNotExist:
                return {"error": f"Lodging {item_id} not found or not accessible"}

        else:
            return {"error": f"Invalid item_type: {item_type}. Must be 'location', 'transportation', or 'lodging'"}

    def create_location(
        self,
        name: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        description: str = "",
        location: str = "",
        is_public: bool = False,
        tags: Optional[list] = None
    ) -> dict:
        """
        Create a new location.

        Args:
            name: Name of the location (required)
            latitude: Latitude coordinate (optional but recommended)
            longitude: Longitude coordinate (optional but recommended)
            description: Description of the location
            location: Address or place name
            is_public: Whether the location should be public (default False)
            tags: List of tags for categorization

        Returns:
            The created location details
        """
        from adventures.models import Location, Category
        from adventures.serializers import LocationSerializer

        user = self.request.user

        # Get or create default category
        category, _ = Category.objects.get_or_create(
            user=user,
            name='general',
            defaults={'display_name': 'General', 'icon': ''}
        )

        location_obj = Location.objects.create(
            user=user,
            name=name,
            latitude=latitude,
            longitude=longitude,
            description=description,
            location=location,
            is_public=is_public,
            tags=tags or [],
            category=category
        )

        serializer = LocationSerializer(location_obj, context={'request': self.request})
        return {
            "success": True,
            "message": f"Created location: {name}",
            "location": serializer.data
        }

    def create_visit(
        self,
        item_type: str,
        item_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        notes: str = "",
        rating: Optional[float] = None
    ) -> dict:
        """
        Record a visit to a location, transportation, or lodging.

        Args:
            item_type: Type of item. Options: "location", "transportation", or "lodging"
            item_id: UUID of the item to add a visit to
            start_date: Start date in ISO format (YYYY-MM-DDTHH:MM:SS) or None for undated
            end_date: End date in ISO format (YYYY-MM-DDTHH:MM:SS) or None for undated
            notes: Notes about the visit
            rating: Rating from 0-5 (optional)

        Returns:
            The created visit details
        """
        from adventures.models import Location, Transportation, Lodging, Visit
        from adventures.serializers import VisitSerializer
        from django.utils.dateparse import parse_datetime

        user = self.request.user

        # Parse dates if provided
        parsed_start = parse_datetime(start_date) if start_date else None
        parsed_end = parse_datetime(end_date) if end_date else None

        # Validate rating
        if rating is not None and (rating < 0 or rating > 5):
            return {"error": "Rating must be between 0 and 5"}

        # Get the parent item
        parent_kwargs = {}
        if item_type == "location":
            try:
                parent = Location.objects.get(
                    Q(id=item_id) & (Q(user=user) | Q(collections__shared_with=user))
                )
                parent_kwargs['location'] = parent
            except Location.DoesNotExist:
                return {"error": f"Location {item_id} not found or not accessible"}

        elif item_type == "transportation":
            try:
                parent = Transportation.objects.get(
                    Q(id=item_id) & (Q(user=user) | Q(collections__shared_with=user))
                )
                parent_kwargs['transportation'] = parent
            except Transportation.DoesNotExist:
                return {"error": f"Transportation {item_id} not found or not accessible"}

        elif item_type == "lodging":
            try:
                parent = Lodging.objects.get(
                    Q(id=item_id) & (Q(user=user) | Q(collections__shared_with=user))
                )
                parent_kwargs['lodging'] = parent
            except Lodging.DoesNotExist:
                return {"error": f"Lodging {item_id} not found or not accessible"}
        else:
            return {"error": f"Invalid item_type: {item_type}"}

        # Create the visit
        visit = Visit.objects.create(
            user=user,
            start_date=parsed_start,
            end_date=parsed_end,
            notes=notes,
            rating=rating,
            **parent_kwargs
        )

        serializer = VisitSerializer(visit, context={'request': self.request})
        return {
            "success": True,
            "message": f"Created visit to {parent.name}",
            "visit": serializer.data
        }

    def list_collections(self, status: str = "all", limit: int = 20) -> list:
        """
        List user's trip collections.

        Args:
            status: Filter by status. Options: "all", "upcoming", "in_progress", "completed", "folder"
            limit: Maximum number of collections to return (default 20, max 50)

        Returns:
            List of collections with basic info
        """
        from adventures.models import Collection
        from datetime import date

        user = self.request.user
        limit = min(limit, 50)
        today = date.today()

        queryset = Collection.objects.filter(user=user, is_archived=False)

        if status == "folder":
            queryset = queryset.filter(Q(start_date__isnull=True) | Q(end_date__isnull=True))
        elif status == "upcoming":
            queryset = queryset.filter(start_date__gt=today)
        elif status == "in_progress":
            queryset = queryset.filter(start_date__lte=today, end_date__gte=today)
        elif status == "completed":
            queryset = queryset.filter(end_date__lt=today)

        collections = queryset.order_by('-updated_at')[:limit]

        results = []
        for c in collections:
            results.append({
                "id": str(c.id),
                "name": c.name,
                "description": (c.description or "")[:200],
                "is_public": c.is_public,
                "start_date": c.start_date.isoformat() if c.start_date else None,
                "end_date": c.end_date.isoformat() if c.end_date else None,
                "location_count": c.locations.count(),
                "is_archived": c.is_archived,
            })

        return results

    def add_to_collection(
        self,
        item_type: str,
        item_id: str,
        collection_id: str
    ) -> dict:
        """
        Add a location, transportation, or lodging to a collection.

        Args:
            item_type: Type of item. Options: "location", "transportation", or "lodging"
            item_id: UUID of the item to add
            collection_id: UUID of the collection to add the item to

        Returns:
            Success message or error
        """
        from adventures.models import Location, Transportation, Lodging, Collection

        user = self.request.user

        # Get the collection (must be owned by user or shared with user)
        try:
            collection = Collection.objects.get(
                Q(id=collection_id) & (Q(user=user) | Q(shared_with=user))
            )
        except Collection.DoesNotExist:
            return {"error": f"Collection {collection_id} not found or not accessible"}

        # Get the item and add to collection
        if item_type == "location":
            try:
                location = Location.objects.get(
                    Q(id=item_id) & (Q(user=user) | Q(collections__shared_with=user) | Q(is_public=True))
                )
                location.collections.add(collection)
                return {
                    "success": True,
                    "message": f"Added location '{location.name}' to collection '{collection.name}'"
                }
            except Location.DoesNotExist:
                return {"error": f"Location {item_id} not found or not accessible"}

        elif item_type == "transportation":
            try:
                transportation = Transportation.objects.get(
                    Q(id=item_id) & (Q(user=user) | Q(collections__shared_with=user) | Q(is_public=True))
                )
                transportation.collections.add(collection)
                return {
                    "success": True,
                    "message": f"Added transportation '{transportation.name}' to collection '{collection.name}'"
                }
            except Transportation.DoesNotExist:
                return {"error": f"Transportation {item_id} not found or not accessible"}

        elif item_type == "lodging":
            try:
                lodging = Lodging.objects.get(
                    Q(id=item_id) & (Q(user=user) | Q(collections__shared_with=user) | Q(is_public=True))
                )
                lodging.collections.add(collection)
                return {
                    "success": True,
                    "message": f"Added lodging '{lodging.name}' to collection '{collection.name}'"
                }
            except Lodging.DoesNotExist:
                return {"error": f"Lodging {item_id} not found or not accessible"}

        else:
            return {"error": f"Invalid item_type: {item_type}. Must be 'location', 'transportation', or 'lodging'"}
