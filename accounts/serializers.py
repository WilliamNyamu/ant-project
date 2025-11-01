from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    token = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'password2', 'token']

    def validate(self, attrs):
        """Validate that both passwords are equal"""
        password = attrs.get('password')
        password2 = attrs.get('password2')

        if not password or not password2:
            raise serializers.ValidationError("All fields must be inserted properly")
        
        if password != password2:
            raise serializers.ValidationError("Both password fields should be the same.")
        
        return attrs
    
    def create(self, validated_data):
        # remove the password2 field because it is not part of the input fields
        validated_data.pop('password2')
        # create a user object
        user = get_user_model().objects.create_user(**validated_data)
        # create a token for the newly created user
        Token.objects.create(user = user)

        return user
    
    def get_token(self, obj):
        token, created = Token.objects.get_or_create(user = obj)
        return token.key

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'profile_picture']
        