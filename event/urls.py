from django.urls import path
from . import views

urlpatterns = [
    # CRUD operations
    path('events/', views.EventListView.as_view(), name='event-list'),
    path('events/create/', views.EventCreateView.as_view(), name='event-create'),
    path('events/<int:pk>/', views.EventRetrieveView.as_view(), name='event-detail'),
    path('events/<int:pk>/update/', views.EventUpdateView.as_view(), name='event-update'),
    path('events/<int:pk>/delete/', views.EventDestroyView.as_view(), name='event-delete'),
    
    # Interest Management
    path('events/<int:pk>/interest/', views.EventInterestView.as_view(), name='event-interest'),
    path('events/<int:pk>/interested-users/', 
         views.EventInterestedUsersView.as_view(), 
         name='event-interested-users'),
]