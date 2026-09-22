"""Instituições novas exigem endereço e confirmação administrativa do GPS."""
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import CustomUser
from accounts.serializers import UserRegistrationSerializer
from courses.admin import InstituicaoAdminForm
from courses.models import Aula, Instituicao, Materia, Turma


class InstitutionRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.address = dict(nome='Campus Novo', logradouro='Rua Acadêmica', numero='10',
                            bairro='Centro', cidade='Três Lagoas', estado='ms')
        self.payload = dict(username='novo_professor', email='professor@gmail.com', role='professor',
                            password='Senha123!', password2='Senha123!', nova_instituicao=self.address)

    def test_new_institution_is_linked_but_cannot_start_call_before_confirmation(self):
        self.address.update(latitude=0, longitude=0, radius_meters=10000, geocoding_source='forjada')
        response = self.client.post('/api/register/', self.payload, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        user = CustomUser.objects.get(username='novo_professor')
        institution = user.instituicao
        self.assertEqual(list(user.instituicoes.all()), [institution])
        self.assertEqual(institution.estado, 'MS')
        self.assertIsNone(institution.latitude)
        self.assertIsNone(institution.longitude)
        self.assertEqual(institution.radius_meters, 100)
        self.assertEqual(institution.geocoding_source, '')
        subject = Materia.objects.create(nome='Matéria', codigo='NOVA', carga_horaria=60, professor=user)
        group = Turma.objects.create(nome='Turma', materia=subject, semestre='2', ano=2026)
        lesson = Aula.objects.create(turma=group, titulo='Teste', data='2026-09-16', horario_inicio='08:00', horario_fim='10:00')
        self.client.force_authenticate(user)
        response = self.client.post('/api/sessoes/', {'aula': lesson.pk})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.post(f'/api/instituicoes/{institution.pk}/confirmar-localizacao/', {'latitude': 0, 'longitude': 0}).status_code, 403)
        admin = CustomUser.objects.create_superuser(username='administrador', password='Senha123!')
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.post(f'/api/instituicoes/{institution.pk}/confirmar-localizacao/', {'latitude': 0, 'longitude': 0}).status_code, 200)
        self.client.force_authenticate(user)
        self.assertEqual(self.client.post('/api/sessoes/', {'aula': lesson.pk}).status_code, 201)

    def test_student_cannot_create_institution(self):
        self.payload.update(role='aluno', matricula='A1')
        self.assertEqual(self.client.post('/api/register/', self.payload, format='json').status_code, 400)
        self.assertFalse(Instituicao.objects.filter(nome='Campus Novo').exists())

    def test_invalid_address_does_not_create_account(self):
        for field, value in [('estado', 'XX'), ('nome', ''), ('logradouro', '')]:
            with self.subTest(field=field):
                data = {**self.payload, 'nova_instituicao': {**self.address, field: value}}
                response = self.client.post('/api/register/', data, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data['nova_instituicao'])
        self.assertFalse(CustomUser.objects.filter(username='novo_professor').exists())

    def test_duplicate_name_is_rejected_case_insensitively(self):
        Instituicao.objects.create(**{**self.address, 'estado': 'MS'})
        self.address['nome'] = 'campus novo'
        response = self.client.post('/api/register/', self.payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('nome', response.data['nova_instituicao'])

    def test_new_and_existing_institution_cannot_be_combined(self):
        institution = Instituicao.objects.create(**{**self.address, 'nome': 'Campus existente'})
        self.payload['instituicoes'] = [institution.pk]
        response = self.client.post('/api/register/', self.payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_user_creation_failure_rolls_back_new_institution(self):
        serializer = UserRegistrationSerializer(data=self.payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        with patch('accounts.serializers.User.objects.create_user', side_effect=RuntimeError('falha')):
            with self.assertRaises(RuntimeError):
                serializer.save()
        self.assertFalse(Instituicao.objects.filter(nome='Campus Novo').exists())

    def test_admin_rejects_partial_coordinates_and_invalid_radius(self):
        for extra in [dict(latitude=1), dict(radius_meters=0), dict(latitude=100, longitude=0)]:
            form = InstituicaoAdminForm(data={**self.address, 'estado': 'MS', 'pais': 'Brasil', 'radius_meters': 100, **extra})
            self.assertFalse(form.is_valid())

    def test_institution_is_available_in_admin_for_superuser(self):
        admin = CustomUser.objects.create_superuser(username='admin_ui', password='Senha123!')
        self.client.force_login(admin)
        self.assertEqual(self.client.get('/admin/courses/instituicao/').status_code, 200)
