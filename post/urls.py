from django.urls import path
from . import views

urlpatterns = [
    # CRUD operations
    path('posts/', views.PostListView.as_view(), name='post-list'),
    path('posts/create/', views.PostCreateView.as_view(), name='post-create'),
    path('posts/<int:pk>/', views.PostRetrieveView.as_view(), name='post-detail'),
    path('posts/<int:pk>/update/', views.PostUpdateView.as_view(), name='post-update'),
    path('posts/<int:pk>/delete/', views.PostDestroyView.as_view(), name='post-delete'),
    
    # Like management
    path('posts/<int:pk>/like/', views.PostLikeView.as_view(), name='post-like'),
    path('posts/<int:pk>/likers/', views.PostLikersView.as_view(), name='post-likers'),
    
    # Feed
    path('posts/feed/', views.PostFeedView.as_view(), name='post-feed'),
]