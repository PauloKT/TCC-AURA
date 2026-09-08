"""
Tasks assíncronas para o app `accounts`.

Em produção, prefira Celery + Redis/RabbitMQ. Para mantermos zero
infra-dependência no ambiente de dev/testes, usamos um thread daemon
com timeout que persiste o resultado no banco.
"""
from __future__ import annotations

import logging
import threading
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


def _geocode_and_update(user_pk: int, cep: str) -> None:
    """Resolve CEP → (lat, lng) e grava no professor."""
    from .models import CustomUser, get_coordinates_from_cep

    try:
        lat, lng = get_coordinates_from_cep(cep)
        if lat is None or lng is None:
            logger.warning("Geocoding falhou para CEP=%s user_pk=%s", cep, user_pk)
            return
        # update_fields para não disparar signals/save custom novamente.
        CustomUser.objects.filter(pk=user_pk).update(latitude=lat, longitude=lng)
        logger.info("Geocoding ok: user_pk=%s cep=%s", user_pk, cep)
    except Exception:
        logger.exception("Erro inesperado no geocoding assíncrono")


def geocode_professor_async(user_pk: int, cep: str) -> None:
    """
    Dispara geocoding em background. Usa Celery se disponível; caso contrário,
    lança um thread daemon.
    """
    if not cep:
        return

    # Caminho Celery (produção).
    try:
        from celery import shared_task  # type: ignore

        @shared_task
        def _task(pk: int, c: str) -> None:
            _geocode_and_update(pk, c)

        _task.delay(user_pk, cep)
        return
    except Exception:
        # Sem Celery configurado → fallback em thread.
        pass

    thread = threading.Thread(
        target=_geocode_and_update,
        args=(user_pk, cep),
        daemon=True,
        name=f"geocode-{user_pk}",
    )
    thread.start()
