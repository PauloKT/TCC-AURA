"""
Tasks assíncronas para o app `accounts`.

Compatibilidade com o cadastro antigo por CEP: uma thread daemon tenta
persistir as coordenadas. Não é uma fila durável; novas sessões usam a instituição.
"""
from __future__ import annotations

import logging
import threading
from django.db import close_old_connections

logger = logging.getLogger(__name__)


def _geocode_and_update(user_pk: int, cep: str) -> None:
    """Resolve CEP → (lat, lng) e grava no professor."""
    from .models import CustomUser, get_coordinates_from_cep

    close_old_connections()
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
    finally:
        close_old_connections()


def geocode_professor_async(user_pk: int, cep: str) -> None:
    """Dispara a tentativa legada de geocodificação em uma thread daemon."""
    if not cep:
        return

    thread = threading.Thread(
        target=_geocode_and_update,
        args=(user_pk, cep),
        daemon=True,
        name=f"geocode-{user_pk}",
    )
    thread.start()
