from django.test import TestCase
from .serializers import UserRegistrationSerializer


class UserRegistrationSerializerTests(TestCase):
    def test_aluno_requires_matricula(self):
        data = {
            'username': 'aluno_teste',
            'email': 'aluno_teste@email.com',
            'role': 'aluno',
            'matricula': '',
            'password': '12345678',
            'password2': '12345678',
        }

        serializer = UserRegistrationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('matricula', serializer.errors)
