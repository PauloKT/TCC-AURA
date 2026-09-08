"""
Testes do app `accounts`.

Cobre:
  - Validação do serializer de registro (aluno/professor, email, senha).
  - Registro de professor dispara geocoding sem bloquear a request.
  - Cálculo de frequência por turma.
"""
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import get_coordinates_from_cep
from accounts.serializers import UserRegistrationSerializer
from courses.models import Instituicao

User = get_user_model()


class LoginApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='login_teste',
            email='login_teste@gmail.com',
            password='Senha123!',
            role='aluno',
            matricula='M1',
        )

    def test_login_retorna_tokens_e_dados_do_usuario(self):
        response = self.client.post(
            '/api/login/',
            {'username': 'login_teste', 'password': 'Senha123!'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'aluno')

    def test_login_rejeita_credencial_invalida(self):
        response = self.client.post(
            '/api/login/',
            {'username': 'login_teste', 'password': 'senha-errada'},
            format='json',
        )

        self.assertEqual(response.status_code, 401)

    def test_refresh_retorna_novo_access_token(self):
        login_response = self.client.post(
            '/api/login/',
            {'username': 'login_teste', 'password': 'Senha123!'},
            format='json',
        )

        response = self.client.post(
            '/api/token/refresh/',
            {'refresh': login_response.data['refresh']},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)


class UserRegistrationSerializerTests(TestCase):
    def test_aluno_requer_matricula(self):
        data = {
            'username': 'aluno_teste',
            'email': 'aluno_teste@gmail.com',
            'role': 'aluno',
            'matricula': '',
            'password': 'Senha123!',
            'password2': 'Senha123!',
        }
        s = UserRegistrationSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('matricula', s.errors)

    def test_professor_requer_instituicao(self):
        data = {
            'username': 'prof_teste',
            'email': 'prof_teste@gmail.com',
            'role': 'professor',
            'password': 'Senha123!',
            'password2': 'Senha123!',
        }
        s = UserRegistrationSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('instituicao', s.errors)

    def test_professor_pode_ser_cadastrado_com_instituicao(self):
        instituicao = Instituicao.objects.create(
            nome='AEMS Teste', logradouro='Av. Júlio Ferreira Xavier',
            numero='2750', bairro='Distrito Industrial', cidade='Três Lagoas',
            estado='MS', latitude=-20.787, longitude=-51.669,
        )
        data = {
            'username': 'prof_instituicao',
            'email': 'prof_instituicao@gmail.com',
            'role': 'professor',
            'instituicao': instituicao.id,
            'password': 'Senha123!',
            'password2': 'Senha123!',
        }
        serializer = UserRegistrationSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.instituicao, instituicao)

    def test_professor_pode_se_cadastrar_em_varias_instituicoes(self):
        aems = Instituicao.objects.create(
            nome='AEMS Multi', logradouro='Av. Júlio Ferreira Xavier',
            numero='2750', bairro='Distrito Industrial', cidade='Três Lagoas',
            estado='MS', latitude=-20.786820236467992, longitude=-51.668829782798554,
        )
        outra = Instituicao.objects.create(
            nome='Outra Instituição', logradouro='Rua Teste', numero='10',
            bairro='Centro', cidade='Três Lagoas', estado='MS',
            latitude=-20.8, longitude=-51.7,
        )
        data = {
            'username': 'prof_varias_instituicoes',
            'email': 'prof_varias@gmail.com',
            'role': 'professor',
            'instituicoes': [aems.id, outra.id],
            'password': 'Senha123!',
            'password2': 'Senha123!',
        }

        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(list(user.instituicoes.all()), [aems, outra])
        self.assertEqual(user.instituicao, aems)

    def test_senhas_devem_coincidir(self):
        data = {
            'username': 'a1',
            'email': 'a1@gmail.com',
            'role': 'aluno',
            'matricula': 'M1',
            'password': 'Senha123!',
            'password2': 'Outra123!',
        }
        s = UserRegistrationSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('password', s.errors)

    def test_senha_fraca_rejeitada(self):
        data = {
            'username': 'a1',
            'email': 'a1@gmail.com',
            'role': 'aluno',
            'matricula': 'M1',
            'password': 'fraca',
            'password2': 'fraca',
        }
        s = UserRegistrationSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('password', s.errors)

    def test_email_dominio_nao_permitido(self):
        data = {
            'username': 'a1',
            'email': 'a1@protonmail.com',
            'role': 'aluno',
            'matricula': 'M1',
            'password': 'Senha123!',
            'password2': 'Senha123!',
        }
        s = UserRegistrationSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('email', s.errors)

    def test_email_valido(self):
        data = {
            'username': 'a1',
            'email': 'a1@gmail.com',
            'role': 'aluno',
            'matricula': 'M1',
            'password': 'Senha123!',
            'password2': 'Senha123!',
        }
        s = UserRegistrationSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)


class GeocodingFallbackTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_cep_invalido_retorna_none(self):
        self.assertEqual(get_coordinates_from_cep('abc'), (None, None))
        self.assertEqual(get_coordinates_from_cep('123'), (None, None))

    @patch('accounts.models.requests.get')
    def test_cep_valido_retorna_coordenadas(self, mock_get):
        # Simula ViaCEP OK
        viacep_resp = mock_get.return_value
        viacep_resp.status_code = 200
        viacep_resp.json.side_effect = [
            {
                'logradouro': 'Praça da Sé',
                'bairro': 'Sé',
                'localidade': 'São Paulo',
                'uf': 'SP',
            },
            [
                {'lat': '-23.5505', 'lon': '-46.6333'}
            ],
        ]
        lat, lng = get_coordinates_from_cep('01001000')
        self.assertEqual(lat, -23.5505)
        self.assertEqual(lng, -46.6333)

    @patch('accounts.models.requests.get')
    def test_falha_rede_retorna_none(self, mock_get):
        mock_get.side_effect = Exception('network error')
        # Usa CEP diferente para não bater no cache do teste anterior
        self.assertEqual(get_coordinates_from_cep('99999999'), (None, None))
