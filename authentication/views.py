# views.py
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.core.exceptions import ObjectDoesNotExist
from .serializers import LoginSerializer, UserSerializer

# views.py





from django.contrib.auth import authenticate


from invoicing.models import CustomerUser  # Añadimos esta importación

class LoginView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = []  # Esto deshabilita la autenticación para esta vista

    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')

            if not email or not password:
                return Response(
                    {'error': 'Por favor proporcione email y contraseña'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Primero obtener el usuario por email
            try:
                user = CustomerUser.objects.get(email=email)
            except CustomerUser.DoesNotExist:
                return Response(
                    {'error': 'No existe una cuenta con este email'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Autenticar usando el username (que obtenemos del usuario encontrado por email)
            user = authenticate(
                request=request,
                username=user.username,
                password=password
            )

            if not user:
                return Response(
                    {'error': 'Credenciales inválidas'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if not user.is_active:
                return Response(
                    {'error': 'Esta cuenta está desactivada'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Crear o obtener token
            token, _ = Token.objects.get_or_create(user=user)
            
            # Serializar datos del usuario
            user_data = UserSerializer(user).data

            return Response({
                'token': token.key,
                'user': user_data,
                'message': 'Login exitoso'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        try:
            # Eliminar token
            request.user.auth_token.delete()
            # Cerrar sesión
            logout(request)
            return Response({
                'message': 'Logout exitoso'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Error durante el proceso de logout'
            }, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        try:
            serializer = UserSerializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Error al obtener el perfil de usuario'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def patch(self, request):
        try:
            serializer = UserSerializer(
                request.user,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response({
                'error': 'Error al actualizar el perfil de usuario'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)