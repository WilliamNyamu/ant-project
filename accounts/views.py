from django.shortcuts import render
from .serializers import RegisterSerializer
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model, authenticate
from rest_framework.authtoken.models import Token
from rest_framework.response import Response


# Create your views here.
User = get_user_model()


class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user  # Return the current authenticated user

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if email is None or password is None:
        raise ValueError("Both fields must be present")
    
    user = authenticate(email=email, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response (
            {
                'token': token.key,
                'user_id': user.id,
                'user.email': user.email,
                'message': 'Register Successful'
            },
            status=status.HTTP_200_OK
        )
    else:
        return Response(
            {
                'error': 'User not found'
            },
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def follow_user(request, user_id):
    if request.method == 'POST':
        try:
            user_to_follow = User.objects.get(id=user_id)

        except User.DoesNotExist:
            return Response(
                {
                    'error': 'User not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        if user_to_follow  in request.user.following.all():
            return Response (
                {
                    'message': f'You already follow {user_to_follow}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if user_to_follow == request.user:
            return Response(
                {
                    'error': 'You cannot follow yourself'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        request.user.following.add(user_to_follow)
        return Response(
            {
                'message': f'You are now following {user_to_follow}'
            },
            status=status.HTTP_200_OK
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def unfollow_user(request, user_id):
    try:
        user_to_unfollow = User.objects.get(id=user_id) # Get the specific user instance to unfollow
    except User.DoesNotExist:
        return Response(
            {'error':'User not found'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check whether the user_to_unfollow exists in the list of following users
    if not request.user.following.filter(id = user_to_unfollow.id).exists():
        return Response(
            {
                'error': f'You do not follow {user_to_unfollow.username}'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    request.user.following.remove(user_to_unfollow)
    return Response(
        {
            'message': f'You have successfully unfollowed {user_to_unfollow.username}'
        },
        status=status.HTTP_200_OK
    )