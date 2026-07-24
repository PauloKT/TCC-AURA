from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True, label="Confirmar senha")
    cep = serializers.CharField(required=False, allow_blank=True, max_length=9)

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'matricula', 'cep', 'password', 'password2')
        extra_kwargs = {
            'email': {'required': True},
        }

    def validate_email(self, value):
        value_lower = value.lower()
        allowed_domains = ['@hotmail.com', '@gmail.com', '@outlook.com',
                          '@hotmail.com.br', '@gmail.com.br', '@outlook.com.br']
        if not any(value_lower.endswith(domain) for domain in allowed_domains):
            raise serializers.ValidationError(
                "Email deve ser de um dos domínios permitidos: hotmail, gmail ou outlook"
            )
        return value

    def validate_password(self, value):
        errors = []
        if len(value) < 5:
            errors.append("A senha deve ter pelo menos 5 caracteres.")
        if not any(char.isdigit() for char in value):
            errors.append("A senha deve conter pelo menos um número.")
        if not any(char.isupper() for char in value):
            errors.append("A senha deve conter pelo menos uma letra maiúscula.")
        if not any(not char.isalnum() and not char.isspace() for char in value):
            errors.append("A senha deve conter pelo menos um caractere especial.")
        if errors:
            raise serializers.ValidationError(errors)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})

        if attrs.get('role') == 'aluno' and not attrs.get('matricula'):
            raise serializers.ValidationError({"matricula": "Matrícula é obrigatória para alunos."})

        if attrs.get('role') == 'professor' and not attrs.get('cep'):
            raise serializers.ValidationError({"cep": "CEP é obrigatório para professores."})
        return attrs

    def create(self, validated_data):
        # Remove password2
        validated_data.pop('password2')
        password = validated_data.pop('password')
        cep = validated_data.pop('cep', None)
        # Create user with the password properly hashed
        user = User.objects.create_user(password=password, **validated_data)
        user.cep = cep
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['role'] = user.role
        token['username'] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add extra responses
        data.update({
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'role': self.user.role,
            }
        })
        return data