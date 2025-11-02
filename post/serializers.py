from rest_framework import serializers
from .models import Post, Like
from accounts.serializers import CustomUserSerializer
from event.serializers import EventSerializer
from event.models import Event

class LikeSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Like
        fields = ['id', 'user', 'created_at']
        read_only_fields = ['created_at']

class PostSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    post_type = serializers.CharField(read_only=True)
    likes = LikeSerializer(many=True, read_only=True)
    tagged_event = EventSerializer(read_only=True)
    tagged_event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        source='tagged_event',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Post
        fields = [
            'id',
            'user',
            'content',
            'image',
            'video',
            'post_type',
            'created_at',
            'updated_at',
            'likes_count',
            'is_liked',
            'likes',
            'tagged_event',
            'tagged_event_id'
        ]
        read_only_fields = ['created_at', 'updated_at', 'user', 'post_type']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def validate(self, data):
        """
        Validate that at least one content type is provided
        """
        content = data.get('content')
        image = data.get('image')
        video = data.get('video')

        if not any([content, image, video]):
            raise serializers.ValidationError(
                "Post must contain at least one of: text content, image, or video"
            )

        # Check video file size (limit to 100MB)
        if video:
            if video.size > 100 * 1024 * 1024:  # 100MB in bytes
                raise serializers.ValidationError(
                    "Video file size must not exceed 100MB"
                )

        return data

    def create(self, validated_data):
        # Set the user from the request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)