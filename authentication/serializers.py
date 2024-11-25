# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from invoicing.models import CustomerUser

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            try:
                user_obj = CustomerUser.objects.get(email=email)
                username = user_obj.username
            except CustomerUser.DoesNotExist:
                msg = _('No se encontró una cuenta con este correo electrónico.')
                raise serializers.ValidationError({'error': msg})

            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            if not user:
                msg = _('Las credenciales proporcionadas son inválidas.')
                raise serializers.ValidationError({'error': msg})
            
            if not user.is_active:
                msg = _('Esta cuenta está desactivada.')
                raise serializers.ValidationError({'error': msg})
        else:
            msg = _('Debe incluir correo electrónico y contraseña.')
            raise serializers.ValidationError({'error': msg})

        attrs['user'] = user
        return attrs

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerUser
        fields = (
            'id', 
            'email', 
            'first_name', 
            'last_name',
            'identification_type', 
            'identification_number', 
            'phone_number',
            'username',
            'is_active'
        )
        read_only_fields = ('id', 'username', 'is_active')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user