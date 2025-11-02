from django.shortcuts import render, get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from .models import Event, EventInterest
from .serializers import EventSerializer
from .permissions import IsOrganizerOrReadOnly

class EventListView(generics.ListAPIView):
    """
    View to list all events.
    """
    queryset = Event.objects.all().order_by('-start_time')
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            interest_count=Count('interests')
        )
        
        event_type = self.request.query_params.get('type', None)
        is_virtual = self.request.query_params.get('virtual', None)
        search_query = self.request.query_params.get('search', None)
        
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
        
        if is_virtual is not None:
            is_virtual = is_virtual.lower() == 'true'
            queryset = queryset.filter(is_virtual=is_virtual)
            
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        return queryset.distinct()

class EventCreateView(generics.CreateAPIView):
    """
    View to create a new event.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """The logged in user becomes the organizer automatically"""
        serializer.save(organizer=self.request.user)
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data['message'] = 'Event created successfully'
        return response

class EventRetrieveView(generics.RetrieveAPIView):
    """
    View to retrieve a single event.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().annotate(
            interest_count=Count('interests')
        )

class EventUpdateView(generics.UpdateAPIView):
    """
    View to update an event.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizerOrReadOnly]

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data['message'] = 'Event updated successfully'
        return response

class EventDestroyView(generics.DestroyAPIView):
    """
    View to delete an event.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizerOrReadOnly]

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        return Response({
            'message': 'Event deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

class EventInterestView(generics.CreateAPIView):
    """
    View to toggle interest in an event.
    """
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        event = get_object_or_404(Event, pk=self.kwargs.get('pk'))
        
        # Check if interest already exists
        interest, created = EventInterest.objects.get_or_create(
            event=event,
            user=request.user
        )
        
        if not created:
            interest.delete()
            message = 'Interest removed from event'
            status_code = status.HTTP_200_OK
        else:
            message = 'Interest added to event'
            status_code = status.HTTP_201_CREATED
            
        return Response({
            'message': message,
            'interest_count': event.interests.count()
        }, status=status_code)

class EventInterestedUsersView(generics.ListAPIView):
    """
    View to list users interested in an event.
    """
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        event_id = self.kwargs.get('pk')
        return EventInterest.objects.filter(event_id=event_id)

    def get_queryset(self):
        queryset = Event.objects.all().annotate(
            interest_count=Count('interests')
        )
        
        event_type = self.request.query_params.get('type', None)
        is_virtual = self.request.query_params.get('virtual', None)
        
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
        
        if is_virtual is not None:
            is_virtual = is_virtual.lower() == 'true'
            queryset = queryset.filter(is_virtual=is_virtual)
        
        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    get: Retrieve an event
    put: Update an event
    delete: Delete an event
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Event.objects.annotate(interest_count=Count('interests'))



class EventInterestedUsersView(generics.ListAPIView):
    """
    get: List users interested in an event
    """
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        event_id = self.kwargs['pk']
        return EventInterest.objects.filter(event_id=event_id)

class UserEventsView(generics.ListAPIView):
    """
    get: List events for a specific user
    """
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Event.objects.filter(organizer_id=user_id).annotate(
            interest_count=Count('interests')
        )

class UpcomingEventsView(generics.ListAPIView):
    """
    get: List upcoming events
    """
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        now = timezone.now()
        return Event.objects.filter(start_time__gt=now).annotate(
            interest_count=Count('interests')
        ).order_by('start_time')

