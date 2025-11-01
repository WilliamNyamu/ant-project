from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from .models import Post, Like
from .serializers import PostSerializer, LikeSerializer

class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling post operations including creating, reading, updating,
    deleting posts, and managing likes.
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content']
    ordering_fields = ['created_at', 'likes_count']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Get posts with optional filtering:
        - all: all posts
        - following: posts from users the current user follows
        - user: posts by a specific user
        - liked: posts liked by the current user
        - media: posts with images or videos
        """
        queryset = Post.objects.annotate(
            likes_count=Count('likes')
        )

        # Get query parameters
        post_type = self.request.query_params.get('type', None)
        user_id = self.request.query_params.get('user', None)
        media_type = self.request.query_params.get('media', None)

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
                queryset = queryset.filter(Q(image__isnull=False) | Q(video__isnull=False))

        return queryset.distinct()

    def perform_create(self, serializer):
        """Set the user when creating a post"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Toggle like status for a post"""
        post = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Check if like exists
            like = Like.objects.get(post=post, user=user)
            # Unlike if exists
            like.delete()
            return Response({
                'status': 'unliked',
                'message': 'Post unliked successfully',
                'likes_count': post.likes.count()
            })
        except Like.DoesNotExist:
            # Create like if doesn't exist
            Like.objects.create(post=post, user=user)
            return Response({
                'status': 'liked',
                'message': 'Post liked successfully',
                'likes_count': post.likes.count()
            })

    @action(detail=True, methods=['get'])
    def likers(self, request, pk=None):
        """Get list of users who liked the post"""
        post = self.get_object()
        likes = post.likes.all().order_by('-created_at')
        serializer = LikeSerializer(likes, many=True)
        return Response({
            'likes_count': likes.count(),
            'likes': serializer.data
        })

    @action(detail=False, methods=['get'])
    def feed(self, request):
        """
        Get personalized feed for authenticated user
        Includes:
        - Posts from followed users
        - Popular posts (high like count)
        - Recent posts
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Get posts from followed users
        following_posts = Post.objects.filter(
            user__in=request.user.following.all()
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

        page = self.paginate_queryset(feed_posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(feed_posts, many=True)
        return Response(serializer.data)
