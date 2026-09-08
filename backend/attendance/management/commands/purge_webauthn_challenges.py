"""
Limpa WebAuthnChallenge vencidos (mais de 5 minutos).

Recomenda-se agendar via cron ou Celery beat em produção:
    0 * * * *  python manage.py purge_webauthn_challenges
"""
from django.core.management.base import BaseCommand

from attendance.models import WebAuthnChallenge


class Command(BaseCommand):
    help = "Remove WebAuthnChallenge vencidos para reduzir superfície de ataque."

    def handle(self, *args, **options):
        deleted, _ = WebAuthnChallenge.purge_expired()
        self.stdout.write(self.style.SUCCESS(f"Removidos {deleted} challenges vencidos."))
