
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'password', 'password2']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Check if username already exists
        username = attrs.get('username', '')
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "Username is already in use."})
            
        # Check if email already exists
        email = attrs.get('email', '')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Email is already in use."})
            
        return attrs
    
    def create(self, validated_data):
        # Remove password2 from validated_data
        validated_data.pop('password2')
        
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'date_joined']
        read_only_fields = ['date_joined']


# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)
#         token['username'] = user.username
#         token['full_name'] = user.full_name
#         token['is_staff'] = user.is_staff
#         token['is_active'] = user.is_active
#         token['is_superuser'] = user.is_superuser
#         return token

#     def validate(self, attrs):
#         data = super().validate(attrs)
#         # Add user details to response (for API endpoints)
#         serializer = UserSerializer(self.user)
#         data.update(serializer.data)
#         return data


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add session version to token payload
        token['session_version'] = user.session_version
        token['username'] = user.username
        token['full_name'] = user.full_name
        token['is_staff'] = user.is_staff
        token['is_active'] = user.is_active
        token['is_superuser'] = user.is_superuser
        token['user_id'] = user.id # Include user ID for reference
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user details to response
        serializer = UserSerializer(self.user)
        data.update(serializer.data)
        return data