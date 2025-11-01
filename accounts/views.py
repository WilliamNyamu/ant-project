from django.shortcuts import render
from .serializers import RegisterSerializer
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model, authenticate
from rest_framework.authtoken.models import Token
from rest_framework.response import Response


# Create your views here.
User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    email = request.get('email')
    password = request.get('password')

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
