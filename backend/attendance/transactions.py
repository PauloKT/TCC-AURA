"""Transações curtas compartilhadas pelas operações de uma chamada.

PostgreSQL bloqueia a linha com select_for_update. SQLite usa BEGIN IMMEDIATE
(settings.py), pois select_for_update não tem efeito nesse banco.
"""
from contextlib import contextmanager
import sqlite3

from django.db import OperationalError, connection, transaction
from rest_framework.exceptions import APIException, ValidationError

from .models import SessaoChamada


class ChamadaOcupada(APIException):
    status_code = 503
    default_detail = 'A chamada está ocupada no momento. Aguarde alguns segundos e tente novamente.'
    default_code = 'chamada_ocupada'


@contextmanager
def chamada_atomic():
    """Não refaz envios automaticamente; devolve erro temporário se o SQLite saturar."""
    try:
        with transaction.atomic():
            yield
    except OperationalError as exc:
        code = getattr(exc.__cause__, 'sqlite_errorcode', None)
        if connection.vendor == 'sqlite' and code is not None and (code & 0xff) in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
            raise ChamadaOcupada() from exc
        raise


def bloquear_sessao(sessao_id):
    """Recarrega e bloqueia somente a sessão; chamar dentro de chamada_atomic."""
    sessao = SessaoChamada.objects.select_for_update().filter(pk=sessao_id).first()
    if sessao is None:
        raise ValidationError({'sessao_id': 'Sessão não encontrada.'})
    return sessao
