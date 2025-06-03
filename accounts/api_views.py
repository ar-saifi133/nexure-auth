from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
import os
from django.conf import settings
from django.http import FileResponse, HttpResponseNotFound
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import (
    UserSerializer,
    CustomTokenObtainPairSerializer,
    RegisterSerializer
)

User = get_user_model()

class RegisterAPIView(generics.CreateAPIView):
    """
    API endpoint for user registration
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate tokens for the new user
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'User registered successfully'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain pair view that uses our serializer
    """
    serializer_class = CustomTokenObtainPairSerializer



class LogoutAPIView(APIView):
    permission_classes = [permissions.AllowAny]  # Change to AllowAny
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'error': 'Refresh token is required'}, status=400)
            
            # Blacklist the token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Increment session version for global logout
            user = token.payload.get('user_id')
            if user:
                user = User.objects.get(id=user)
                user.session_version += 1
                user.save()
                logger.debug(f"Session version incremented for user: {user.id}")
            
            return Response({'message': 'Global logout successful'}, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=400)




class UserAPIView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for retrieving and updating user information
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user

    
class AvatarImageView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        #avatar_path = os.path.join(settings.STATIC_ROOT, 'avatars', user.avatar)
        avatar_path = os.path.join(settings.BASE_DIR, 'static', 'avatars', user.avatar)
        if os.path.exists(avatar_path):
            return FileResponse(open(avatar_path, 'rb'), content_type='image/webp')
        return HttpResponseNotFound('Avatar not found')






from rest_framework_simplejwt.exceptions import InvalidToken

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except InvalidToken as e:
            # Decode token to check session version
            try:
                refresh_token = request.data.get('refresh')
                payload = jwt.decode(
                    refresh_token,
                    settings.SECRET_KEY,
                    algorithms=["HS256"],
                    options={"verify_exp": False}
                )
                user_id = payload.get('user_id')
                user = User.objects.get(id=user_id)
                
                # Check session version
                if payload.get('session_version') != user.session_version:
                    raise InvalidToken("Session expired. Please log in again.")
                
            except (jwt.InvalidTokenError, User.DoesNotExist):
                pass
            raise e
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)