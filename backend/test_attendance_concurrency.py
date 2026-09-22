"""Requisições concorrentes reais, com uma conexão de banco por thread.

Execute por pytest (backend.test_settings) para usar um SQLite de teste em disco.
A mesma bateria pode ser executada com DB_ENGINE=postgres em banco de teste.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import timedelta
from threading import Barrier, Event
from types import SimpleNamespace
from unittest.mock import patch
import sqlite3

from django.db import OperationalError, connection, connections
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from accounts.models import CustomUser
from attendance.models import Presenca, SessaoChamada
from attendance.serializers import PresencaCreateSerializer
from attendance.transactions import bloquear_sessao, chamada_atomic, ChamadaOcupada
from attendance.views import SessaoChamadaViewSet
from courses.models import Aula, Materia, Turma, TurmaAluno


class AttendanceConcurrencyTests(TransactionTestCase):
    def setUp(self):
        if connection.vendor == 'sqlite' and ('memory' in str(connection.settings_dict['NAME'])):
            self.skipTest('Use backend.test_settings: concorrência SQLite exige banco em disco.')
        self.teacher = CustomUser.objects.create_user(username='teacher', role='professor', latitude=0, longitude=0)
        self.students = [CustomUser.objects.create_user(username=f'student{i}', role='aluno') for i in range(8)]
        subject = Materia.objects.create(nome='Concorrência', codigo='CON', carga_horaria=60, professor=self.teacher)
        self.group = Turma.objects.create(nome='Turma', materia=subject, semestre='2', ano=2026)
        TurmaAluno.objects.bulk_create([TurmaAluno(turma=self.group, aluno=student) for student in self.students])
        self.lesson = Aula.objects.create(turma=self.group, titulo='Threads', data='2026-09-17', horario_inicio='08:00', horario_fim='10:00')
        self.session = SessaoChamada.objects.create(aula=self.lesson, professor_latitude=0, professor_longitude=0)
        self.base = f'/api/sessoes/{self.session.pk}/'

    def request(self, user, method, path, data=None):
        client = APIClient()
        client.force_authenticate(user)
        return getattr(client, method)(path, data or {}, format='json')

    def worker(self, job):
        connections.close_all()
        try:
            return job()
        finally:
            connections.close_all()

    def parallel(self, jobs):
        barrier = Barrier(len(jobs), timeout=10)

        def start(job):
            barrier.wait()
            return self.worker(job)

        with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            futures = [pool.submit(start, job) for job in jobs]
            return [future.result(timeout=30) for future in futures]

    def payload(self, **extra):
        return {'sessao_id': self.session.pk, 'token': self.session.token_atual, 'latitude': 0, 'longitude': 0, **extra}

    def validated(self, **extra):
        serializer = PresencaCreateSerializer(data=self.payload(**extra), context={'request': SimpleNamespace(user=self.students[0])})
        serializer.is_valid(raise_exception=True)
        return serializer

    def test_closed_after_initial_validation_is_not_saved(self):
        serializer = self.validated()
        self.assertEqual(self.request(self.teacher, 'post', self.base + 'encerrar/').status_code, 200)
        with self.assertRaisesMessage(ValidationError, 'encerrada'):
            serializer.save()
        self.assertFalse(Presenca.objects.exists())

    def test_rotated_or_expired_token_after_validation_is_rejected(self):
        for expired in (False, True):
            with self.subTest(expired=expired):
                self.session.refresh_from_db()
                serializer = self.validated()
                if expired:
                    SessaoChamada.objects.filter(pk=self.session.pk).update(token_expira_em=timezone.now() - timedelta(seconds=1))
                else:
                    self.session.refresh_token()
                with self.assertRaisesMessage(ValidationError, 'expirado'):
                    serializer.save()
        self.assertFalse(Presenca.objects.exists())

    def test_receipt_expiration_is_revalidated_before_save(self):
        import time
        receipt = self.request(self.students[0], 'post', self.base + 'preparar/', {'token': self.session.token_atual}).data['comprovante']
        serializer = self.validated(comprovante=receipt)
        with patch('django.core.signing.time.time', return_value=time.time() + 121):
            with self.assertRaisesMessage(ValidationError, 'esgotado'):
                serializer.save()
        self.assertFalse(Presenca.objects.exists())

    def test_enrollment_is_revalidated_before_save(self):
        serializer = self.validated()
        TurmaAluno.objects.filter(turma=self.group, aluno=self.students[0]).delete()
        with self.assertRaisesMessage(ValidationError, 'matriculado'):
            serializer.save()
        self.assertFalse(Presenca.objects.exists())

    def test_many_students_register_simultaneously(self):
        results = self.parallel([
            lambda student=student: self.request(student, 'post', '/api/presenca/registrar/', self.payload())
            for student in self.students
        ])
        self.assertEqual([result.status_code for result in results], [201] * 8)
        self.assertEqual(Presenca.objects.filter(valida=True).count(), 8)

    def test_simultaneous_repeats_preserve_the_first_gps_result(self):
        barrier = Barrier(8, timeout=10)
        original = PresencaCreateSerializer.validate

        def validate(serializer, attrs):
            data = original(serializer, attrs)
            barrier.wait()  # All requests hold a valid, potentially stale snapshot.
            return data

        with patch.object(PresencaCreateSerializer, 'validate', validate):
            results = self.parallel([
                lambda index=index: self.request(self.students[0], 'post', '/api/presenca/registrar/', self.payload(latitude=index % 2))
                for index in range(8)
            ])
        self.assertEqual([result.status_code for result in results], [201] * 8)
        self.assertEqual(Presenca.objects.count(), 1)
        self.assertEqual(len({result.data['presenca']['id'] for result in results}), 1)
        self.assertEqual(len({result.data['presenca']['valida'] for result in results}), 1)

    def test_simultaneous_refreshes_return_the_same_new_token(self):
        SessaoChamada.objects.filter(pk=self.session.pk).update(token_expira_em=timezone.now() - timedelta(seconds=1))
        barrier = Barrier(8, timeout=10)
        original = SessaoChamadaViewSet.get_object

        def snapshot(view):
            result = original(view)
            barrier.wait()  # Force all eight requests to read the expired token first.
            return result

        with patch.object(SessaoChamadaViewSet, 'get_object', snapshot):
            results = self.parallel([lambda: self.request(self.teacher, 'get', self.base + 'token/') for _ in range(8)])
        self.assertEqual([result.status_code for result in results], [200] * 8)
        tokens = {result.data['token_atual'] for result in results}
        self.session.refresh_from_db()
        self.assertEqual(tokens, {self.session.token_atual})
        self.assertTrue(all(result['Cache-Control'] == 'no-store' for result in results))

    def test_simultaneous_starts_create_only_one_active_session(self):
        self.session.delete()
        results = self.parallel([lambda: self.request(self.teacher, 'post', '/api/sessoes/', {'aula': self.lesson.pk}) for _ in range(8)])
        self.assertEqual([result.status_code for result in results], [201] * 8)
        self.assertEqual(len({result.data['id'] for result in results}), 1)
        self.assertEqual(SessaoChamada.objects.filter(aula=self.lesson, ativa=True).count(), 1)

    def test_start_and_token_endpoint_share_the_same_rotation(self):
        SessaoChamada.objects.filter(pk=self.session.pk).update(token_expira_em=timezone.now() - timedelta(seconds=1))
        results = self.parallel(
            [lambda: self.request(self.teacher, 'post', '/api/sessoes/', {'aula': self.lesson.pk}) for _ in range(4)]
            + [lambda: self.request(self.teacher, 'get', self.base + 'token/') for _ in range(4)]
        )
        self.assertEqual([result.status_code for result in results], [201] * 4 + [200] * 4)
        self.assertEqual(len({result.data['token_atual'] for result in results}), 1)
        self.assertEqual(SessaoChamada.objects.filter(aula=self.lesson, ativa=True).count(), 1)

    def test_simultaneous_closes_preserve_one_closing_time(self):
        results = self.parallel([lambda: self.request(self.teacher, 'post', self.base + 'encerrar/') for _ in range(8)])
        self.assertEqual(sorted(result.status_code for result in results), [200] + [400] * 7)
        self.session.refresh_from_db()
        closed_at = self.session.encerrada_em
        self.assertFalse(self.session.ativa)
        self.assertIsNotNone(closed_at)
        self.request(self.teacher, 'post', self.base + 'encerrar/')
        self.session.refresh_from_db()
        self.assertEqual(self.session.encerrada_em, closed_at)

    def ordered_race(self, first, second, patch_target):
        locked, release, second_entering_transaction = Event(), Event(), Event()

        @contextmanager
        def track_transaction():
            if locked.is_set():
                second_entering_transaction.set()
            with chamada_atomic():
                yield

        def pause_once(session_id):
            session = bloquear_sessao(session_id)
            if not locked.is_set():
                locked.set()
                if not release.wait(10):
                    raise AssertionError('Teste não liberou o bloqueio')
            return session

        with (patch(patch_target, pause_once),
              patch('attendance.views.chamada_atomic', track_transaction),
              patch('attendance.serializers.chamada_atomic', track_transaction),
              ThreadPoolExecutor(max_workers=2) as pool):
            first_future = pool.submit(self.worker, first)
            try:
                self.assertTrue(locked.wait(10), 'Primeira operação não adquiriu bloqueio')
                second_future = pool.submit(self.worker, second)
                self.assertTrue(second_entering_transaction.wait(10), 'Segunda operação não chegou à transação')
                # The first lock is still held, and the second request cannot finish.
                with self.assertRaises(TimeoutError):
                    second_future.result(timeout=0.1)
            finally:
                release.set()
            return first_future.result(timeout=30), second_future.result(timeout=30)

    def test_close_wins_against_registration(self):
        results = self.ordered_race(
            lambda: self.request(self.teacher, 'post', self.base + 'encerrar/'),
            lambda: self.request(self.students[0], 'post', '/api/presenca/registrar/', self.payload()),
            'attendance.views.bloquear_sessao',
        )
        self.assertEqual([result.status_code for result in results], [200, 400])
        self.assertFalse(Presenca.objects.exists())
        self.assertEqual(self.request(self.teacher, 'get', self.base + 'token/').status_code, 400)

    def test_close_wins_against_token_refresh(self):
        SessaoChamada.objects.filter(pk=self.session.pk).update(token_expira_em=timezone.now() - timedelta(seconds=1))
        results = self.ordered_race(
            lambda: self.request(self.teacher, 'post', self.base + 'encerrar/'),
            lambda: self.request(self.teacher, 'get', self.base + 'token/'),
            'attendance.views.bloquear_sessao',
        )
        self.assertEqual([result.status_code for result in results], [200, 400])
        self.session.refresh_from_db()
        self.assertFalse(self.session.ativa)
        self.assertFalse(self.session.is_token_valid())

    def test_refresh_wins_before_close_without_reopening_session(self):
        SessaoChamada.objects.filter(pk=self.session.pk).update(token_expira_em=timezone.now() - timedelta(seconds=1))
        results = self.ordered_race(
            lambda: self.request(self.teacher, 'get', self.base + 'token/'),
            lambda: self.request(self.teacher, 'post', self.base + 'encerrar/'),
            'attendance.views.bloquear_sessao',
        )
        self.assertEqual([result.status_code for result in results], [200, 200])
        self.session.refresh_from_db()
        self.assertFalse(self.session.ativa)
        self.assertFalse(self.session.is_token_valid())

    def test_registration_wins_before_close_and_remains_saved(self):
        results = self.ordered_race(
            lambda: self.request(self.students[0], 'post', '/api/presenca/registrar/', self.payload()),
            lambda: self.request(self.teacher, 'post', self.base + 'encerrar/'),
            'attendance.serializers.bloquear_sessao',
        )
        self.assertEqual([result.status_code for result in results], [201, 200])
        self.session.refresh_from_db()
        self.assertLessEqual(Presenca.objects.get().registrada_em, self.session.encerrada_em)

    def test_stale_patch_cannot_reopen_session_or_restore_old_token(self):
        stale = SessaoChamada.objects.get(pk=self.session.pk)
        self.request(self.teacher, 'post', self.base + 'encerrar/')
        with patch.object(SessaoChamadaViewSet, 'get_object', return_value=stale):
            result = self.request(self.teacher, 'patch', self.base, {'aula': self.lesson.pk})
        self.assertEqual(result.status_code, 200)
        self.session.refresh_from_db()
        self.assertFalse(self.session.ativa)
        self.assertIsNotNone(self.session.encerrada_em)

    def test_sqlite_busy_is_temporary_error_but_other_database_errors_are_not_hidden(self):
        if connection.vendor != 'sqlite':
            self.skipTest('Tradução específica do SQLite')
        cause = sqlite3.OperationalError('database is locked')
        cause.sqlite_errorcode = sqlite3.SQLITE_BUSY
        error = OperationalError('database is locked')
        error.__cause__ = cause
        with self.assertRaises(ChamadaOcupada):
            with chamada_atomic():
                raise error
        with self.assertRaisesMessage(OperationalError, 'outro erro'):
            with chamada_atomic():
                raise OperationalError('outro erro')
