"""
Testes de presença, token dinâmico e localização.
"""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import CustomUser
from attendance.models import (
    SessaoChamada, Presenca,
)
from attendance.geolocation import haversine_distance, is_within_radius
from courses.models import Materia, Turma, TurmaAluno, Aula


class SessaoChamadaTests(TestCase):
    def setUp(self):
        self.prof = CustomUser.objects.create_user(
            username='prof', password='x', role='professor',
            email='prof@gmail.com', latitude=-23.5505, longitude=-46.6333,
            radius_meters=100,
        )
        self.aluno = CustomUser.objects.create_user(
            username='aluno', password='x', role='aluno',
            email='aluno@gmail.com', matricula='M1',
        )
        self.materia = Materia.objects.create(
            nome='M', codigo='M1', carga_horaria=60,
            frequencia_minima=75, professor=self.prof,
        )
        self.turma = Turma.objects.create(
            nome='T', materia=self.materia, semestre='2024.1', ano=2024,
        )
        self.aula = Aula.objects.create(
            turma=self.turma, titulo='Aula 1', data='2024-03-10',
            horario_inicio='08:00', horario_fim='10:00',
        )
        self.sessao = SessaoChamada.objects.create(
            aula=self.aula,
            professor_latitude=-23.5505,
            professor_longitude=-46.6333,
            professor_radius_meters=100,
        )

    def test_token_inicial_gerado(self):
        self.assertTrue(self.sessao.token_atual)
        self.assertTrue(self.sessao.is_token_valid())

    def test_token_expirado(self):
        self.sessao.token_expira_em = timezone.now() - timedelta(seconds=1)
        self.sessao.save(update_fields=['token_expira_em'])
        self.assertFalse(self.sessao.is_token_valid())

    def test_refresh_token_gera_novo(self):
        antigo = self.sessao.token_atual
        self.sessao.refresh_token()
        self.assertNotEqual(antigo, self.sessao.token_atual)

    def test_aluno_matriculado_nao_obtem_token_sem_ler_qr(self):
        TurmaAluno.objects.create(turma=self.turma, aluno=self.aluno)
        client = APIClient()
        client.force_authenticate(user=self.aluno)

        response = client.get(f'/api/sessoes/{self.sessao.id}/token/')

        self.assertEqual(response.status_code, 403)

    def test_aluno_nao_matriculado_nao_pode_consultar_token(self):
        client = APIClient()
        client.force_authenticate(user=self.aluno)

        response = client.get(f'/api/sessoes/{self.sessao.id}/token/')

        self.assertEqual(response.status_code, 403)


class PresencaTests(TestCase):
    def setUp(self):
        self.prof = CustomUser.objects.create_user(
            username='prof', password='x', role='professor',
            email='prof@gmail.com', latitude=-23.5505, longitude=-46.6333,
            radius_meters=100,
        )
        self.aluno = CustomUser.objects.create_user(
            username='aluno', password='x', role='aluno',
            email='aluno@gmail.com', matricula='M1',
        )
        materia = Materia.objects.create(
            nome='M', codigo='M1', carga_horaria=60,
            frequencia_minima=75, professor=self.prof,
        )
        turma = Turma.objects.create(
            nome='T', materia=materia, semestre='2024.1', ano=2024,
        )
        aula = Aula.objects.create(
            turma=turma, titulo='A', data='2024-03-10',
            horario_inicio='08:00', horario_fim='10:00',
        )
        self.sessao = SessaoChamada.objects.create(
            aula=aula,
            professor_latitude=-23.5505,
            professor_longitude=-46.6333,
            professor_radius_meters=100,
        )

    def test_presenca_valida_com_gps_ok(self):
        p = Presenca(
            sessao=self.sessao, aluno=self.aluno,
            latitude=-23.5505, longitude=-46.6333,
        )
        p.save()
        self.assertTrue(p.valida)

    def test_presenca_valida_com_localizacao_institucional(self):
        p = Presenca(
            sessao=self.sessao, aluno=self.aluno,
            latitude=-23.5505, longitude=-46.6333,
        )
        p.save()
        self.assertTrue(p.valida)

    def test_presenca_invalida_gps_longe(self):
        p = Presenca(
            sessao=self.sessao, aluno=self.aluno,
            latitude=-23.0, longitude=-46.0,  # ~ 100km de distância
        )
        p.save()
        self.assertFalse(p.valida)

    def test_presenca_idempotente(self):
        p1 = Presenca(
            sessao=self.sessao, aluno=self.aluno,
            latitude=-23.5505, longitude=-46.6333,
        )
        p1.save()
        # Segunda tentativa não deve duplicar (unique_together)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            p2 = Presenca(
                sessao=self.sessao, aluno=self.aluno,
                latitude=-23.5505, longitude=-46.6333,
            )
            p2.save()

    def test_geolocalizacao_aceita_o_limite_do_raio(self):
        distance = haversine_distance(-23.5505, -46.6333, -23.5496, -46.6333)

        self.assertTrue(is_within_radius(
            -23.5505, -46.6333,
            -23.5505 + (100 / 111_320), -46.6333,
            100,
        ))
        self.assertGreater(distance, 90)

    def test_geolocalizacao_rejeita_coordenada_fora_dos_limites(self):
        self.assertFalse(is_within_radius(
            -23.5505, -46.6333, -23.0, -46.0, 100,
        ))


class PresencaAPITests(TestCase):
    def setUp(self):
        self.prof = CustomUser.objects.create_user(
            username='prof', password='x', role='professor',
            email='prof@gmail.com', latitude=-23.5505, longitude=-46.6333,
            radius_meters=100,
        )
        self.aluno = CustomUser.objects.create_user(
            username='aluno', password='x', role='aluno',
            email='aluno@gmail.com', matricula='M1',
        )
        materia = Materia.objects.create(
            nome='M', codigo='M1', carga_horaria=60,
            frequencia_minima=75, professor=self.prof,
        )
        turma = Turma.objects.create(
            nome='T', materia=materia, semestre='2024.1', ano=2024,
        )
        TurmaAluno = __import__('courses.models', fromlist=['TurmaAluno']).TurmaAluno
        TurmaAluno.objects.create(turma=turma, aluno=self.aluno)
        aula = Aula.objects.create(
            turma=turma, titulo='A', data='2024-03-10',
            horario_inicio='08:00', horario_fim='10:00',
        )
        self.sessao = SessaoChamada.objects.create(
            aula=aula,
            professor_latitude=-23.5505,
            professor_longitude=-46.6333,
            professor_radius_meters=100,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.aluno)

    def test_registrar_presenca_sucesso(self):
        url = '/api/presenca/registrar/'
        resp = self.client.post(url, data={
            'sessao_id': self.sessao.id,
            'token': self.sessao.token_atual,
            'latitude': -23.5505,
            'longitude': -46.6333,
        }, format='json')
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertTrue(resp.data['presenca']['valida'])

    def test_registrar_presenca_token_invalido(self):
        url = '/api/presenca/registrar/'
        resp = self.client.post(url, data={
            'sessao_id': self.sessao.id,
            'token': 'token-errado',
            'latitude': -23.5505,
            'longitude': -46.6333,
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_registrar_presenca_fora_do_raio_persiste_falta(self):
        url = '/api/presenca/registrar/'
        resp = self.client.post(url, data={
            'sessao_id': self.sessao.id,
            'token': self.sessao.token_atual,
            'latitude': -23.0,
            'longitude': -46.0,
        }, format='json')

        self.assertEqual(resp.status_code, 201)
        self.assertFalse(resp.data['presenca']['valida'])
        self.assertTrue(Presenca.objects.filter(
            sessao=self.sessao,
            aluno=self.aluno,
        ).exists())

        retry = self.client.post(url, data={
            'sessao_id': self.sessao.id,
            'token': self.sessao.token_atual,
            'latitude': -23.5505,
            'longitude': -46.6333,
        }, format='json')

        self.assertEqual(retry.status_code, 201, retry.data)
        self.assertFalse(retry.data['presenca']['valida'])
        self.assertEqual(Presenca.objects.filter(sessao=self.sessao, aluno=self.aluno).count(), 1)

    def test_registrar_presenca_rejeita_latitude_invalida(self):
        response = self.client.post('/api/presenca/registrar/', data={
            'sessao_id': self.sessao.id,
            'token': self.sessao.token_atual,
            'latitude': 91,
            'longitude': -46.6333,
        }, format='json')

        self.assertEqual(response.status_code, 400)
