from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from datetime import datetime
from django.utils import timezone
from .models import Event, EventInterest
from .serializers import EventSerializer

class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Event operations.
    Provides CRUD operations and additional actions for event management.
    """
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Get the list of events with optional filtering.
        Supports filtering by:
        - upcoming (future events)
        - past (past events)
        - organized (events organized by the current user)
        - interested (events the user is interested in)
        - search (search in name, description, location)
        - virtual (virtual or in-person events)
        """
        queryset = Event.objects.all().annotate(
            interest_count=Count('interests')
        ).order_by('-start_time')
        
        # Get query parameters
        event_type = self.request.query_params.get('type', None)
        search_query = self.request.query_params.get('search', None)
        is_virtual = self.request.query_params.get('virtual', None)
        
        # Filter by event type
        if event_type:
            now = timezone.now()
            if event_type == 'upcoming':
                queryset = queryset.filter(start_time__gt=now)
            elif event_type == 'past':
                queryset = queryset.filter(start_time__lt=now)
            elif event_type == 'organized' and self.request.user.is_authenticated:
                queryset = queryset.filter(organizer=self.request.user)
            elif event_type == 'interested' and self.request.user.is_authenticated:
                queryset = queryset.filter(interests__user=self.request.user)
        
        # Filter by virtual/in-person
        if is_virtual is not None:
            is_virtual = is_virtual.lower() == 'true'
            queryset = queryset.filter(is_virtual=is_virtual)
        
        # Apply search filter
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        return queryset.distinct()

    def perform_create(self, serializer):
        """Save the event with the current user as organizer"""
        serializer.save(organizer=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_interest(self, request, pk=None):
        """Toggle user's interest in an event"""
        event = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            # Try to get existing interest
            interest = EventInterest.objects.get(event=event, user=user)
            # If exists, remove it (user is un-interested)
            interest.delete()
            return Response({
                'status': 'removed',
                'message': 'Interest removed from event',
                'interest_count': event.interests.count()
            }, status=status.HTTP_200_OK)
        except EventInterest.DoesNotExist:
            # If doesn't exist, create it (user is interested)
            EventInterest.objects.create(event=event, user=user)
            return Response({
                'status': 'added',
                'message': 'Interest added to event',
                'interest_count': event.interests.count()
            }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def interested_users(self, request, pk=None):
        """Get list of users interested in an event"""
        event = self.get_object()
        interested_users = User.objects.filter(interested_events__event=event)
        from accounts.serializers import CustomUserSerializer
        serializer = CustomUserSerializer(interested_users, many=True)
        return Response({
            'count': interested_users.count(),
            'users': serializer.data
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get event statistics"""
        now = timezone.now()
        total_events = Event.objects.count()
        upcoming_events = Event.objects.filter(start_time__gt=now).count()
        past_events = Event.objects.filter(start_time__lt=now).count()
        virtual_events = Event.objects.filter(is_virtual=True).count()
        
        if request.user.is_authenticated:
            organized_events = Event.objects.filter(organizer=request.user).count()
            interested_events = Event.objects.filter(interests__user=request.user).count()
        else:
            organized_events = 0
            interested_events = 0
        
        return Response({
            'total_events': total_events,
            'upcoming_events': upcoming_events,
            'past_events': past_events,
            'virtual_events': virtual_events,
            'organized_events': organized_events,
            'interested_events': interested_events
        })
