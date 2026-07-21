from django.db import models
from django.conf import settings
from django.utils import timezone
import secrets
from courses.models import Aula
from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371000  # Earth radius in meters
    return c * r


def haversine_distance_check(lat1, lon1, lat2, lon2, max_distance_meters):
    """
    Check if two points are within a maximum distance without computing the full haversine distance.
    Uses a bounding box check first for efficiency, then falls back to haversine if needed.

    Returns True if within distance, False otherwise.
    """
    # Convert to radians
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)

    # Earth radius in meters
    R = 6371000

    # Convert max distance to radians for latitude and longitude
    lat_rad = max_distance_meters / R
    lon_rad = max_distance_meters / (R * cos(lat1_rad)) if abs(cos(lat1_rad)) > 1e-10 else float('inf')

    # Bounding box check
    if (lat2_rad < lat1_rad - lat_rad or lat2_rad > lat1_rad + lat_rad or
        lon2_rad < lon1_rad - lon_rad or lon2_rad > lon1_rad + lon_rad):
        return False

    # If within bounding box, do the full haversine calculation
    return haversine(lat1, lon1, lat2, lon2) <= max_distance_meters

class SessaoChamada(models.Model):
    id = models.AutoField(primary_key=True)
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='sessoes')
    token_atual = models.CharField(max_length=100, unique=True, blank=True)
    token_expira_em = models.DateTimeField()
    ativa = models.BooleanField(default=True)
    iniciada_em = models.DateTimeField(default=timezone.now)
    encerrada_em = models.DateTimeField(null=True, blank=True)
    # Store professor's location at session start for verification
    professor_latitude = models.FloatField()
    professor_longitude = models.FloatField()
    professor_radius_meters = models.PositiveIntegerField(default=100)

    class Meta:
        indexes = [
            models.Index(fields=['ativa'], name='idx_sessaochamada_ativa'),
            models.Index(fields=['aula', 'ativa'], name='idx_sessaochamada_aula_ativa'),
            models.Index(fields=['token_expira_em'], name='idx_sessaochamada_token_expira_em'),
        ]

    def save(self, *args, **kwargs):
        if not self.token_atual:
            self.token_atual = secrets.token_urlsafe(16)
        if not self.token_expira_em:
            self.token_expira_em = timezone.now() + timezone.timedelta(seconds=30)
        super().save(*args, **kwargs)

    def is_token_valid(self):
        return self.ativa and timezone.now() < self.token_expira_em

    def refresh_token(self):
        self.token_atual = secrets.token_urlsafe(16)
        self.token_expira_em = timezone.now() + timezone.timedelta(seconds=30)
        self.save(update_fields=['token_atual', 'token_expira_em'])

    def __str__(self):
        return f"Sessao {self.id} - Aula {self.aula_id} - Token {'ativo' if self.is_token_valid() else 'expirado'}"


class Presenca(models.Model):
    id = models.AutoField(primary_key=True)
    sessao = models.ForeignKey(SessaoChamada, on_delete=models.CASCADE, related_name='presencas')
    aluno = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='presencas')
    registrada_em = models.DateTimeField(auto_now_add=True)
    # Student's location at the moment of check-in
    latitude = models.FloatField()
    longitude = models.FloatField()
    localizacao_capturada_em = models.DateTimeField(auto_now_add=True)
    valida = models.BooleanField(default=False)

    class Meta:
        unique_together = ('sessao', 'aluno')  # One attendance per session per student
        indexes = [
            models.Index(fields=['valida'], name='idx_presenca_valida'),
            models.Index(fields=['aluno', 'registrada_em'], name='idx_presenca_aluno_registrada_em'),
            models.Index(fields=['sessao'], name='idx_presenca_sessao'),
            # Composite index for optimizing the frequency query
            models.Index(fields=['sessao', 'aluno', 'valida'], name='idx_presenca_sessao_aluno_valida'),
        ]

    def save(self, *args, **kwargs):
        # Validate location against session's professor location and radius
        # Use optimized distance check that employs bounding box filtering first
        self.valida = haversine_distance_check(
            self.sessao.professor_latitude,
            self.sessao.professor_longitude,
            self.latitude,
            self.longitude,
            self.sessao.professor_radius_meters
        )
        self.localizacao_capturada_em = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Presença {self.aluno.username} na sessão {self.sessao_id} - {'Válida' if self.valida else 'Inválida'}"