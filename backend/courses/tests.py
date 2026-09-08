"""
Testes do app `courses`.
"""
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import CustomUser
from courses.models import Instituicao, Materia, Turma, Aula, TurmaAluno


class InstituicaoApiTests(TestCase):
    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            nome='AEMS Teste', logradouro='Av. Júlio Ferreira Xavier',
            numero='2750', bairro='Distrito Industrial', cidade='Três Lagoas',
            estado='MS', latitude=-20.787, longitude=-51.669,
        )
        self.client = APIClient()

    def test_instituicoes_ativas_sao_publicas(self):
        response = self.client.get('/api/instituicoes/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(item['id'] == self.instituicao.id for item in response.data))

    def test_confirmar_localizacao_exige_administrador(self):
        response = self.client.post(
            f'/api/instituicoes/{self.instituicao.id}/confirmar-localizacao/',
            {'latitude': -20.787, 'longitude': -51.669},
            format='json',
        )

        self.assertEqual(response.status_code, 401)

    def test_confirmar_localizacao_rejeita_coordenada_invalida(self):
        admin = CustomUser.objects.create_superuser(
            username='admin', email='admin@gmail.com', password='Senha123!'
        )
        self.client.force_authenticate(user=admin)

        response = self.client.post(
            f'/api/instituicoes/{self.instituicao.id}/confirmar-localizacao/',
            {'latitude': 91, 'longitude': -51.669},
            format='json',
        )

        self.assertEqual(response.status_code, 400)


class MateriaModelTests(TestCase):
    def setUp(self):
        self.prof = CustomUser.objects.create_user(
            username='prof1', password='x', role='professor',
            email='p1@gmail.com', cep='01310100',
        )
        self.prof.latitude = -23.5505
        self.prof.longitude = -46.6333
        self.prof.save()

    def test_criar_materia(self):
        m = Materia.objects.create(
            nome='Cálculo I', codigo='MAT101', carga_horaria=60,
            frequencia_minima=75, professor=self.prof,
        )
        self.assertEqual(str(m), 'Cálculo I (MAT101)')
        self.assertEqual(m.frequencia_minima, 75)

    def test_codigo_unico(self):
        Materia.objects.create(
            nome='A', codigo='A1', carga_horaria=10,
            frequencia_minima=75, professor=self.prof,
        )
        with self.assertRaises(Exception):
            Materia.objects.create(
                nome='B', codigo='A1', carga_horaria=10,
                frequencia_minima=75, professor=self.prof,
            )


class TurmaTests(TestCase):
    def setUp(self):
        self.prof = CustomUser.objects.create_user(
            username='prof2', password='x', role='professor',
            email='p2@gmail.com', latitude=0, longitude=0,
        )
        self.aluno = CustomUser.objects.create_user(
            username='aluno1', password='x', role='aluno',
            email='a1@gmail.com', matricula='M1',
        )
        self.materia = Materia.objects.create(
            nome='Algoritmos', codigo='ALG101', carga_horaria=60,
            frequencia_minima=75, professor=self.prof,
        )
        self.turma = Turma.objects.create(
            nome='Turma A', materia=self.materia, semestre='2024.1', ano=2024,
        )

    def test_aluno_pode_entrar(self):
        ta, created = TurmaAluno.objects.get_or_create(turma=self.turma, aluno=self.aluno)
        self.assertTrue(created)
        self.assertEqual(self.turma.alunos.count(), 1)

    def test_aluno_duplicado_unico(self):
        TurmaAluno.objects.create(turma=self.turma, aluno=self.aluno)
        with self.assertRaises(Exception):
            TurmaAluno.objects.create(turma=self.turma, aluno=self.aluno)

    def test_aula_associada(self):
        a = Aula.objects.create(
            turma=self.turma, titulo='Aula 1', data='2024-03-10',
            horario_inicio='08:00', horario_fim='10:00',
        )
        self.assertIn(a, self.turma.aulas.all())
