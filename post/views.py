from django.shortcuts import render, get_object_or_404
from rest_framework import generics, permissions, status, mixins
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from .models import Post, Like
from .serializers import PostSerializer
from .permissions import IsAuthorOrReadOnly

class PostListView(generics.ListCreateAPIView):
    """
    View to list all posts and create new posts.
    GET: List all posts
    POST: Create a new post (requires authentication)
    """
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            likes_count=Count('likes')
        )

        post_type = self.request.query_params.get('type', None)
        user_id = self.request.query_params.get('user', None)
        media_type = self.request.query_params.get('media', None)
        search_query = self.request.query_params.get('search', None)

        # Filter by post type
        if post_type:
            if post_type == 'following' and self.request.user.is_authenticated:
                queryset = queryset.filter(user__in=self.request.user.following.all())
            elif post_type == 'liked' and self.request.user.is_authenticated:
                queryset = queryset.filter(likes__user=self.request.user)

        # Filter by user
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by media type
        if media_type:
            if media_type == 'image':
                queryset = queryset.exclude(image='')
            elif media_type == 'video':
                queryset = queryset.exclude(video='')
            elif media_type == 'any':
                queryset = queryset.filter(
                    Q(image__isnull=False) | Q(video__isnull=False)
                )

        # Apply search filter
        if search_query:
            queryset = queryset.filter(content__icontains=search_query)

        return queryset.distinct()


class PostCreateView(generics.CreateAPIView):
    """
    View to create a new post.
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """The logged in user becomes the author automatically"""
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data['message'] = 'Post created successfully'
        return response

class PostRetrieveView(generics.RetrieveAPIView):
    """
    View to retrieve a single post.
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().annotate(
            likes_count=Count('likes')
        )

class PostUpdateView(generics.UpdateAPIView):
    """
    View to update a post.
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data['message'] = 'Post updated successfully'
        return response

class PostDestroyView(generics.DestroyAPIView):
    """
    View to delete a post.
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        return Response({
            'message': 'Post deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

class PostLikeView(generics.CreateAPIView):
    """
    View to toggle like on a post.
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs.get('pk'))
        
        # Check if like already exists
        like, created = Like.objects.get_or_create(
            post=post,
            user=request.user
        )
        
        if not created:
            like.delete()
            message = 'Post unliked successfully'
            status_code = status.HTTP_200_OK
        else:
            message = 'Post liked successfully'
            status_code = status.HTTP_201_CREATED
            
        return Response({
            'message': message,
            'likes_count': post.likes.count()
        }, status=status_code)

class PostLikersView(generics.ListAPIView):
    """
    View to list users who liked a post.
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs.get('pk')
        return Like.objects.filter(post_id=post_id).order_by('-created_at')

class PostFeedView(generics.ListAPIView):
    """
    View to get personalized feed for authenticated user.
    Includes:
    - Posts from followed users
    - Popular posts (high like count)
    - Recent posts
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Get posts from followed users
        following_posts = Post.objects.filter(
            user__in=self.request.user.following.all()
        )

        # Get popular posts (more than 5 likes)
        popular_posts = Post.objects.annotate(
            likes_count=Count('likes')
        ).filter(likes_count__gte=5)

        # Get recent posts
        recent_posts = Post.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        )

        # Combine and remove duplicates
        feed_posts = following_posts.union(
            popular_posts, recent_posts
        ).order_by('-created_at')

        return feed_posts
