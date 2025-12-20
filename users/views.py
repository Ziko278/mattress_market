from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .serializers import UserSerializer, UserRegisterSerializer, UserProfileSerializer
from .models import UserProfileModel


class UserRegisterView(APIView):
    """
    Register a new user
    Body: {"username", "email", "password", "first_name", "last_name"}
    """

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Create token for auto-login after registration
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                "message": "User registered successfully",
                "token": token.key,
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """
    Login user with username/email and password
    Body: {"username": "user@example.com", "password": "pass123"}
    """

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Username and password required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if username is actually an email
        if '@' in username:
            try:
                user_obj = User.objects.get(email=username)
                username = user_obj.username
            except User.DoesNotExist:
                return Response(
                    {"error": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        # Authenticate user
        user = authenticate(username=username, password=password)

        if user:
            # Get or create token
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                "message": "Login successful",
                "token": token.key,
                "user": UserSerializer(user).data
            })
        else:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )


class UserLogoutView(APIView):
    """
    Logout user by deleting their token
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Delete user's token
            request.user.auth_token.delete()
            return Response({"message": "Logout successful"})
        except Exception as e:
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(APIView):
    """
    Get authenticated user's profile
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserProfileUpdateView(APIView):
    """
    Update user profile (first_name, last_name, email, phone, avatar)
    """
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        # Update User fields
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.save()

        # Update Profile fields
        try:
            profile = user.profile
        except UserProfileModel.DoesNotExist:
            profile = UserProfileModel.objects.create(user=user)

        profile.phone = request.data.get('phone', profile.phone)

        # Handle avatar upload
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        profile.save()

        serializer = UserSerializer(user)
        return Response(serializer.data)


class PasswordChangeView(APIView):
    """
    Change user password
    Body: {"old_password", "new_password"}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response(
                {"error": "Both old and new passwords required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        # Check old password
        if not user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password changed successfully"})


class UserProfileWithAddressView(APIView):
    """
    Get authenticated user's profile with default address
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from orders.models import AddressModel
        from orders.serializers import AddressSerializer
        
        user_data = UserSerializer(request.user).data
        
        # Get default address if exists
        try:
            default_address = AddressModel.objects.get(user=request.user, is_default=True)
            user_data['default_address'] = AddressSerializer(default_address).data
        except AddressModel.DoesNotExist:
            user_data['default_address'] = None
        
        return Response(user_data)