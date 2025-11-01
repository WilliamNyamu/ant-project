from rest_framework import serializers
from .models import Event, EventInterest
from accounts.serializers import CustomUserSerializer

class EventSerializer(serializers.ModelSerializer):
    organizer = CustomUserSerializer(read_only=True)
    is_organizer = serializers.SerializerMethodField()
    interested_count = serializers.SerializerMethodField()
    is_interested = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id',
            'name',
            'description',
            'start_time',
            'end_time',
            'location',
            'is_virtual',
            'image',
            'created_at',
            'updated_at',
            'organizer',
            'is_organizer',
            'interested_count',
            'is_interested',
            'reg_link',
            'instagram_link'
        ]
        read_only_fields = ['created_at', 'updated_at', 'organizer']

    def get_is_organizer(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return request.user == obj.organizer
        return False
    
    def get_interested_count(self, obj):
        return obj.interests.count()
    
    def get_is_interested(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.interests.filter(user=request.user).exists()
        return False

    def create(self, validated_data):
        # Set the organizer as the current authenticated user
        validated_data['organizer'] = self.context['request'].user
        return super().create(validated_data)