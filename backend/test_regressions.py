from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import CustomUser
from attendance.models import Presenca, SessaoChamada
from courses.models import Aula, Materia, Turma, TurmaAluno


class RegressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.prof = CustomUser.objects.create_user(username='owner', role='professor', latitude=0, longitude=0)
        cls.other = CustomUser.objects.create_user(username='other', role='professor', latitude=0, longitude=0)
        cls.student = CustomUser.objects.create_user(username='student', role='aluno')
        cls.subject = Materia.objects.create(nome='Subject', codigo='R1', carga_horaria=60, professor=cls.prof)
        cls.foreign = Materia.objects.create(nome='Other', codigo='R2', carga_horaria=60, professor=cls.other)
        cls.group = Turma.objects.create(nome='Group', materia=cls.subject, semestre='1', ano=2026)
        cls.foreign_group = Turma.objects.create(nome='Other', materia=cls.foreign, semestre='1', ano=2026)
        cls.lesson = Aula.objects.create(turma=cls.group, titulo='Lesson', data='2026-09-10', horario_inicio='08:00', horario_fim='10:00')
        cls.session = SessaoChamada.objects.create(aula=cls.lesson, professor_latitude=0, professor_longitude=0)
        cls.enrollment = TurmaAluno.objects.create(turma=cls.group, aluno=cls.student)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.prof)

    def test_teacher_cannot_modify_foreign_subject(self):
        for method in ('patch', 'delete'):
            response = getattr(self.client, method)(f'/api/materias/{self.foreign.pk}/', {'nome': 'Changed'}, format='json')
            self.assertEqual(response.status_code, 404)

    def test_create_group_and_lesson_then_select_by_parent(self):
        group = self.client.post('/api/turmas/', {
            'nome': 'Nova turma', 'materia': self.subject.pk,
            'semestre': '2', 'ano': 2026,
        }, format='json')
        self.assertEqual(group.status_code, 201, group.data)
        groups = self.client.get(f'/api/turmas/?materia={self.subject.pk}')
        self.assertIn(group.data['id'], [item['id'] for item in groups.data])
        lesson = self.client.post('/api/aulas/', {
            'turma': group.data['id'], 'titulo': 'Nova aula', 'data': '2026-09-15',
            'hora_inicio': '08:00', 'hora_fim': '10:00',
        }, format='json')
        self.assertEqual(lesson.status_code, 201, lesson.data)
        lessons = self.client.get(f"/api/aulas/?turma={group.data['id']}")
        self.assertEqual([item['id'] for item in lessons.data], [lesson.data['id']])
        self.assertEqual(lessons.data[0]['hora_inicio'], '08:00:00')

    def test_teacher_cannot_create_or_move_group_to_foreign_subject(self):
        response = self.client.post('/api/turmas/', {'nome': 'Bad', 'materia': self.foreign.pk, 'semestre': '1', 'ano': 2026})
        self.assertEqual(response.status_code, 400)
        response = self.client.patch(f'/api/turmas/{self.group.pk}/', {'materia': self.foreign.pk})
        self.assertEqual(response.status_code, 400)

    def test_teacher_cannot_move_lesson_or_enrollment_to_foreign_group(self):
        for endpoint, pk in [('aulas', self.lesson.pk), ('turma-aluno', self.enrollment.pk)]:
            response = self.client.patch(f'/api/{endpoint}/{pk}/', {'turma': self.foreign_group.pk})
            self.assertEqual(response.status_code, 400)

    def test_lesson_end_must_follow_start_on_partial_update(self):
        response = self.client.patch(f'/api/aulas/{self.lesson.pk}/', {'hora_fim': '07:00'})
        self.assertEqual(response.status_code, 400)

    def test_student_lists_only_enrolled_groups_and_lessons(self):
        self.client.force_authenticate(self.student)
        for endpoint, expected in [('turmas', self.group.pk), ('aulas', self.lesson.pk)]:
            response = self.client.get(f'/api/{endpoint}/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual([item['id'] for item in response.data], [expected])

    def test_student_cannot_bypass_invitation_or_change_enrollment(self):
        self.client.force_authenticate(self.student)
        response = self.client.post('/api/turma-aluno/', {'turma': self.foreign_group.pk, 'aluno': self.student.pk})
        self.assertEqual(response.status_code, 403)
        response = self.client.patch(f'/api/turma-aluno/{self.enrollment.pk}/', {'turma': self.foreign_group.pk})
        self.assertEqual(response.status_code, 403)

    def test_invitation_valid_invalid_and_duplicate(self):
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.post('/api/aluno/entrar-turma/', {'link_acesso': 'bad'}).status_code, 400)
        for expected in [201, 200]:
            response = self.client.post('/api/aluno/entrar-turma/', {'link_acesso': str(self.foreign_group.link_acesso)})
            self.assertEqual(response.status_code, expected)

    def test_join_by_short_code(self):
        self.assertEqual(len(self.foreign_group.codigo_acesso), 8)
        self.assertNotEqual(self.group.codigo_acesso, self.foreign_group.codigo_acesso)
        self.client.force_authenticate(self.student)
        for expected in [201, 200]:
            response = self.client.post('/api/aluno/entrar-turma/', {
                'codigo_acesso': ' ' + self.foreign_group.codigo_acesso.lower() + ' ',
            })
            self.assertEqual(response.status_code, expected, response.data)
            self.assertEqual(response.data['turma_id'], self.foreign_group.pk)
        for code in ['', 'INVALIDO', 'ABCDEFGHI']:
            self.assertEqual(self.client.post('/api/aluno/entrar-turma/', {'codigo_acesso': code}).status_code, 400)
        self.foreign_group.ativa = False
        self.foreign_group.save()
        self.assertEqual(self.client.post('/api/aluno/entrar-turma/', {
            'codigo_acesso': self.foreign_group.codigo_acesso,
        }).status_code, 400)

    def test_frequency_zero_attendance_is_not_missing_data(self):
        self.client.force_authenticate(self.student)
        response = self.client.get(f'/api/aluno/minha-frequencia/?turma={self.group.pk}')
        self.assertEqual(response.data, {'percentual': 0, 'situacao': 'reprovado'})
        with self.assertNumQueries(1):
            response = self.client.get('/api/aluno/turmas/')
        self.assertEqual(response.data['turmas'][0]['situacao'], 'reprovado')

    def test_frequency_no_sessions_and_full_attendance(self):
        self.client.force_authenticate(self.student)
        Presenca.objects.create(sessao=self.session, aluno=self.student, latitude=0, longitude=0)
        response = self.client.get('/api/aluno/turmas/')
        self.assertEqual(response.data['turmas'][0]['percentual'], 100)
        self.session.delete()
        response = self.client.get('/api/aluno/turmas/')
        self.assertEqual(response.data['turmas'][0]['situacao'], 'sem_dados')

    def test_frequency_invalid_parameter(self):
        self.client.force_authenticate(self.student)
        for query in ['', '?turma=bad']:
            self.assertEqual(self.client.get('/api/aluno/minha-frequencia/' + query).status_code, 400)

    def test_close_session_and_reject_refresh_after_close(self):
        url = f'/api/sessoes/{self.session.pk}/'
        self.assertEqual(self.client.post(url + 'encerrar/').status_code, 200)
        self.assertEqual(self.client.post(url + 'encerrar/').status_code, 400)
        self.assertEqual(self.client.get(url + 'token/').status_code, 400)

    def test_session_cannot_move_to_another_lesson(self):
        lesson = Aula.objects.create(turma=self.group, titulo='Other', data='2026-09-11', horario_inicio='08:00', horario_fim='10:00')
        response = self.client.patch(f'/api/sessoes/{self.session.pk}/', {'aula': lesson.pk})
        self.assertEqual(response.status_code, 400)

    def test_presence_requires_enrollment_and_is_idempotent(self):
        self.client.force_authenticate(self.student)
        payload = {'sessao_id': self.session.pk, 'token': self.session.token_atual, 'latitude': 0, 'longitude': 0}
        for _ in range(2):
            response = self.client.post('/api/presenca/registrar/', payload)
            self.assertEqual(response.status_code, 201)
            self.assertNotIn('webauthn_verified', response.data['presenca'])
        self.assertEqual(Presenca.objects.count(), 1)
        self.enrollment.delete()
        self.assertEqual(self.client.post('/api/presenca/registrar/', payload).status_code, 400)

    def test_biometric_routes_are_removed(self):
        from django.urls import resolve, Resolver404
        for action in ('register/begin', 'register/complete', 'authenticate/begin', 'authenticate/complete'):
            with self.assertRaises(Resolver404):
                resolve(f'/webauthn/{action}/', urlconf='attendance.urls')

    def test_models_match_migrations(self):
        from io import StringIO
        from django.core.management import call_command
        call_command('makemigrations', check=True, dry_run=True, stdout=StringIO())

    def test_calls_require_login_and_enrollment(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/sessoes/ativas/').status_code, 401)
        self.client.force_authenticate(self.student)
        data = self.client.get('/api/sessoes/ativas/').data
        self.assertEqual([s['id'] for s in data['chamadas']], [self.session.pk])
        self.assertNotIn('token_atual', data['chamadas'][0])
        self.enrollment.delete()
        self.assertEqual(self.client.get('/api/sessoes/ativas/').data['chamadas'], [])

    def test_scan_then_gps_survives_qr_rotation_and_removes_notice(self):
        self.client.force_authenticate(self.student)
        response = self.client.post(f'/api/sessoes/{self.session.pk}/preparar/', {'token': self.session.token_atual})
        self.assertEqual(response.status_code, 200)
        self.session.refresh_token()
        payload = {'sessao_id': self.session.pk, 'comprovante': response.data['comprovante'], 'latitude': 0, 'longitude': 0}
        for _ in range(2):
            result = self.client.post('/api/presenca/registrar/', payload)
            self.assertEqual(result.status_code, 201)
            self.assertTrue(result.data['presenca']['valida'])
        self.assertEqual(Presenca.objects.count(), 1)
        self.assertEqual(self.client.get('/api/sessoes/ativas/').data['chamadas'], [])

    def test_scan_rejects_expired_token(self):
        from datetime import timedelta
        from django.utils import timezone
        self.session.token_expira_em = timezone.now() - timedelta(seconds=1)
        self.session.save()
        self.client.force_authenticate(self.student)
        response = self.client.post(f'/api/sessoes/{self.session.pk}/preparar/', {'token': self.session.token_atual})
        self.assertEqual(response.status_code, 400)

    def test_receipt_rejects_other_student_expiry_and_closed_call(self):
        from unittest.mock import patch
        import time
        self.client.force_authenticate(self.student)
        with patch('django.core.signing.time.time', return_value=time.time() - 121):
            expired = self.client.post(f'/api/sessoes/{self.session.pk}/preparar/', {'token': self.session.token_atual}).data['comprovante']
        payload = {'sessao_id': self.session.pk, 'comprovante': expired, 'latitude': 0, 'longitude': 0}
        self.assertEqual(self.client.post('/api/presenca/registrar/', payload).status_code, 400)
        payload['comprovante'] = self.client.post(f'/api/sessoes/{self.session.pk}/preparar/', {'token': self.session.token_atual}).data['comprovante']
        another = CustomUser.objects.create_user(username='another', role='aluno')
        TurmaAluno.objects.create(turma=self.group, aluno=another)
        self.client.force_authenticate(another)
        self.assertEqual(self.client.post('/api/presenca/registrar/', payload).status_code, 400)
        self.client.force_authenticate(self.student)
        self.session.ativa = False
        self.session.save()
        self.assertEqual(self.client.post('/api/presenca/registrar/', payload).status_code, 400)
        self.assertFalse(Presenca.objects.exists())

    def test_gps_outside_radius_records_absence(self):
        self.client.force_authenticate(self.student)
        receipt = self.client.post(f'/api/sessoes/{self.session.pk}/preparar/', {'token': self.session.token_atual}).data['comprovante']
        response = self.client.post('/api/presenca/registrar/', {'sessao_id': self.session.pk, 'comprovante': receipt, 'latitude': 10, 'longitude': 10})
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data['presenca']['valida'])
        self.assertFalse(Presenca.objects.get().valida)
        self.assertEqual(self.client.get('/api/sessoes/ativas/').data['chamadas'], [])

    def test_results_only_visible_to_session_owner(self):
        Presenca.objects.create(sessao=self.session, aluno=self.student, latitude=10, longitude=10)
        url = f'/api/sessoes/{self.session.pk}/resultados/'
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['resultados'], [{'aluno_id': self.student.pk, 'aluno': 'student', 'status': 'falta'}])
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_start_reuses_active_session(self):
        response = self.client.post('/api/sessoes/', {'aula': self.lesson.pk})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['id'], self.session.pk)
        self.assertEqual(SessaoChamada.objects.count(), 1)
