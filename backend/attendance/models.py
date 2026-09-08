from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
import secrets
from courses.models import Aula
from .geolocation import (
    MAX_RADIUS_METERS,
    MIN_RADIUS_METERS,
    haversine_distance,
    is_within_radius,
    validate_coordinates,
    validate_radius,
)


def haversine(lat1, lon1, lat2, lon2):
    """Mantém compatibilidade com chamadas antigas ao cálculo de distância."""
    return haversine_distance(lat1, lon1, lat2, lon2)


def haversine_distance_check(lat1, lon1, lat2, lon2, max_distance_meters):
    """Mantém compatibilidade com chamadas antigas à regra de geofence."""
    return is_within_radius(lat1, lon1, lat2, lon2, max_distance_meters)

class SessaoChamada(models.Model):
    id = models.AutoField(primary_key=True)
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='sessoes')
    token_atual = models.CharField(max_length=100, unique=True, blank=True)
    token_expira_em = models.DateTimeField()
    ativa = models.BooleanField(default=True)
    iniciada_em = models.DateTimeField(default=timezone.now)
    encerrada_em = models.DateTimeField(null=True, blank=True)
    # Store professor's location at session start for verification
    professor_latitude = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    professor_longitude = models.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    professor_radius_meters = models.PositiveIntegerField(
        default=100,
        validators=[
            MinValueValidator(MIN_RADIUS_METERS),
            MaxValueValidator(MAX_RADIUS_METERS),
        ],
    )

    class Meta:
        indexes = [
            models.Index(fields=['ativa'], name='idx_sessao_ativa'),
            models.Index(fields=['aula', 'ativa'], name='idx_sessao_aula_ativa'),
            models.Index(fields=['token_expira_em'], name='idx_sessao_token_exp'),
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
    latitude = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    localizacao_capturada_em = models.DateTimeField(auto_now_add=True)
    # 3ª camada de segurança: biometria via WebAuthn
    webauthn_verified = models.BooleanField(default=False)
    valida = models.BooleanField(default=False)

    class Meta:
        unique_together = ('sessao', 'aluno')  # One attendance per session per student
        indexes = [
            models.Index(fields=['valida'], name='idx_presenca_valida'),
            models.Index(fields=['aluno', 'registrada_em'], name='idx_pres_aluno_reg'),
            models.Index(fields=['sessao'], name='idx_presenca_sessao'),
            # Composite index for optimizing the frequency query
            models.Index(fields=['sessao', 'aluno', 'valida'], name='idx_pres_ses_aln_val'),
        ]

    def save(self, *args, **kwargs):
        """Calcula a validade da presença antes de persistir o registro."""
        validate_coordinates(self.latitude, self.longitude)
        validate_coordinates(
            self.sessao.professor_latitude,
            self.sessao.professor_longitude,
        )
        validate_radius(self.sessao.professor_radius_meters)
        gps_ok = is_within_radius(
            self.sessao.professor_latitude,
            self.sessao.professor_longitude,
            self.latitude,
            self.longitude,
            self.sessao.professor_radius_meters
        )
        # A biometria não faz parte do fluxo ativo; QR Code e geolocalização validam a presença.
        self.valida = gps_ok
        self.localizacao_capturada_em = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Presença {self.aluno.username} na sessão {self.sessao_id} - {'Válida' if self.valida else 'Inválida'}"


class WebAuthnCredential(models.Model):
    """
    Armazena a credencial WebAuthn registrada para um aluno.
    Os dados biométricos (impressão digital, Face ID) nunca saem do dispositivo:
    apenas a chave pública e os metadados do autenticador são persistidos.
    """
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='webauthn_credentials',
        limit_choices_to={'role': 'aluno'},
    )
    # credential_id retornado pelo autenticador (base64url, sem padding)
    credential_id = models.CharField(max_length=512, unique=True)
    # chave pública (DER ou PEM, base64)
    public_key = models.TextField()
    # Algoritmo COSE (-7 ES256, -257 RS256)
    public_key_alg = models.IntegerField(default=-7)
    # contador de assinatura (proteção contra clonagem)
    sign_count = models.PositiveIntegerField(default=0)
    # Nome amigável para o dispositivo (ex.: "iPhone do aluno")
    nickname = models.CharField(max_length=80, blank=True, default='')
    criada_em = models.DateTimeField(auto_now_add=True)
    ultimo_uso_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['aluno']),
        ]

    def __str__(self):
        return f"WebAuthn[{self.aluno.username}: {self.nickname or self.credential_id[:16]}]"


class WebAuthnChallenge(models.Model):
    """
    Armazena challenges WebAuthn em curso (registro ou autenticação).
    Challenge expira em 5 minutos.
    """
    TIPO_REGISTRO = 'register'
    TIPO_AUTENTICACAO = 'authenticate'
    TIPOS = (
        (TIPO_REGISTRO, 'Registro'),
        (TIPO_AUTENTICACAO, 'Autenticação'),
    )

    # Janela de validade (5 min) para mitigar replay.
    TTL_SECONDS = 5 * 60

    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='webauthn_challenges',
    )
    challenge = models.CharField(max_length=128, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    criado_em = models.DateTimeField(auto_now_add=True)
    consumido = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['challenge']),
            models.Index(fields=['aluno', 'tipo']),
            models.Index(fields=['criado_em']),
        ]

    @classmethod
    def criar(cls, aluno, tipo):
        """Gera e persiste um challenge novo."""
        import secrets
        ch = secrets.token_urlsafe(64)
        return cls.objects.create(aluno=aluno, challenge=ch, tipo=tipo)

    def consumir(self):
        """Marca o challenge como usado (one-shot)."""
        self.consumido = True
        self.save(update_fields=['consumido'])

    def is_expired(self) -> bool:
        from django.utils import timezone
        return (timezone.now() - self.criado_em).total_seconds() > self.TTL_SECONDS

    @classmethod
    def purge_expired(cls):
        """Remove challenges vencidos. Pode ser invocado por management command."""
        from django.utils import timezone
        from datetime import timedelta
        limite = timezone.now() - timedelta(seconds=cls.TTL_SECONDS)
        return cls.objects.filter(criado_em__lt=limite).delete()

    def __str__(self):
        return f"Challenge[{self.aluno.username}: {self.tipo}]"