from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import CustomUser
from attendance.models import Presenca, SessaoChamada
from courses.models import Aula, Materia, Turma, TurmaAluno


class InterfaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = CustomUser.objects.create_user(username='ui_teacher', role='professor')
        cls.other = CustomUser.objects.create_user(username='ui_other', role='professor')
        cls.student = CustomUser.objects.create_user(username='ui_student', role='aluno')
        cls.subject = Materia.objects.create(nome='Interface', codigo='UI', carga_horaria=60, professor=cls.teacher)
        cls.group = Turma.objects.create(nome='Turma UI', materia=cls.subject, semestre='2', ano=2026)
        TurmaAluno.objects.create(turma=cls.group, aluno=cls.student)
        cls.lesson = Aula.objects.create(turma=cls.group, titulo='Aula UI', data='2026-09-16', horario_inicio='08:00', horario_fim='10:00')
        cls.session = SessaoChamada.objects.create(aula=cls.lesson, professor_latitude=0, professor_longitude=0)
        Presenca.objects.create(sessao=cls.session, aluno=cls.student, latitude=0, longitude=0)

    def test_templates_render_shared_layout_and_static(self):
        for url in ['/', '/login.html', '/register.html', '/professor.html', '/aluno.html', '/confirmar-presenca.html']:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertContains(response, '/static/app.css')
            self.assertNotContains(response, '{%')
            self.assertContains(response, 'id="main"')

    @override_settings(DEBUG=False)
    def test_pages_are_not_debug_only(self):
        self.assertEqual(self.client.get('/professor.html').status_code, 200)

    def test_workspace_permissions_and_frequency(self):
        client = APIClient()
        self.assertEqual(client.get('/api/interface/painel/').status_code, 401)
        client.force_authenticate(self.teacher)
        result = client.get('/api/interface/painel/').data
        self.assertEqual(result['turmas'][0]['alunos'], 1)
        self.assertEqual(result['frequencias'][0]['percentual'], 100)
        self.assertEqual(result['frequencias'][0]['faltas'], 0)
        client.force_authenticate(self.other)
        result = client.get('/api/interface/painel/').data
        self.assertEqual(result['turmas'], [])
        self.assertEqual(result['frequencias'], [])
        client.force_authenticate(self.student)
        result = client.get('/api/interface/painel/').data
        self.assertEqual(len(result['frequencias']), 1)
        self.assertEqual(result['frequencias'][0]['aluno_id'], self.student.pk)
        self.assertIsNone(result['turmas'][0]['codigo_acesso'])

    def test_profile_is_current_user_only(self):
        client = APIClient()
        self.assertEqual(client.get('/api/interface/perfil/').status_code, 401)
        client.force_authenticate(self.student)
        self.assertEqual(client.get('/api/interface/perfil/').data['username'], 'ui_student')

    def test_workspace_aggregation_keeps_students_and_groups_separate(self):
        absent = CustomUser.objects.create_user(username='ui_absent', role='aluno')
        TurmaAluno.objects.create(turma=self.group, aluno=absent)
        empty_group = Turma.objects.create(nome='Sem chamadas', materia=self.subject, semestre='2', ano=2026)
        TurmaAluno.objects.create(turma=empty_group, aluno=self.student)
        session = SessaoChamada.objects.create(aula=self.lesson, professor_latitude=0, professor_longitude=0)
        Presenca.objects.create(sessao=session, aluno=self.student, latitude=1, longitude=1)
        client = APIClient()
        client.force_authenticate(self.teacher)
        result = client.get('/api/interface/painel/').data
        rows = {(row['turma_id'], row['aluno_id']): row for row in result['frequencias']}
        present = rows[(self.group.pk, self.student.pk)]
        self.assertEqual((present['aulas'], present['presencas'], present['faltas']), (2, 1, 1))
        self.assertEqual(rows[(self.group.pk, absent.pk)]['percentual'], 0)
        self.assertEqual(rows[(empty_group.pk, self.student.pk)]['situacao'], 'sem_dados')
        groups = {group['id']: group for group in result['turmas']}
        self.assertEqual(groups[self.group.pk]['media'], 25)
        self.assertIsNone(groups[empty_group.pk]['media'])
