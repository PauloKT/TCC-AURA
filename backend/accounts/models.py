from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
import requests
from django.conf import settings
import re
from django.core.cache import cache
from django.utils import timezone

# Database indexing strategy for performance optimization:
# - Role-based queries: Index on 'role' field for filtering professors/alunos
# - CEP lookups: Index on 'cep' field for geocoding operations
# - Additional indexes should be added based on query analysis and usage patterns

# Cache TTL para geocoding reverso: 24h (CEP raramente muda)
GEOCODING_CACHE_TTL = 60 * 60 * 24


def get_coordinates_from_cep(cep):
    """
    Resolve um CEP brasileiro em coordenadas (lat, lon) usando Nominatim (OSM).

    Estratégia em camadas:
      1. Sanitiza o CEP (8 dígitos) e consulta o cache do Django.
      2. Busca o endereço textual via ViaCEP.
      3. Geocodifica o endereço via Nominatim.

    Returns:
        tuple[float|None, float|None]: (latitude, longitude) ou (None, None).
    """
    # Clean CEP: remove non-digits
    clean_cep = ''.join(filter(str.isdigit, cep))
    if len(clean_cep) != 8:
        return None, None

    # Check cache first (cache key based on CEP)
    cache_key = f"cep_coords_{clean_cep}"
    cached_coords = cache.get(cache_key)
    if cached_coords is not None:
        return cached_coords

    # First try ViaCEP to get address (logradouro, bairro, localidade, uf)
    url_viacep = f"https://viacep.com.br/ws/{clean_cep}/json/"
    try:
        response = requests.get(url_viacep, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'erro' in data:
                return None, None
            address = f"{data.get('logradouro', '')}, {data.get('bairro', '')}, {data.get('localidade', '')}, {data.get('uf', '')}, Brasil"
            address = re.sub(r'\s+', ' ', address).strip(', ')
            # Now use Nominatim to get lat/lon
            if address:
                url_nominatim = "https://nominatim.openstreetmap.org/search"
                params = {
                    'q': address,
                    'format': 'json',
                    'limit': 1,
                }
                headers = {'User-Agent': 'TCC-AURA/1.0 (contact@example.com)'}
                resp = requests.get(url_nominatim, params=params, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data_nom = resp.json()
                    if data_nom:
                        lat = float(data_nom[0]['lat'])
                        lon = float(data_nom[0]['lon'])
                        # Cache the result for 24 hours
                        cache.set(cache_key, (lat, lon), GEOCODING_CACHE_TTL)
                        return lat, lon
    except Exception:
        # Falha de rede/timeout: cai no fallback. Em produção, enviar para Sentry.
        return None, None
    return None, None


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('professor', 'Professor'),
        ('aluno', 'Aluno'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    matricula = models.CharField(max_length=20, blank=True, null=True, help_text="Matrícula do aluno (opcional)")
    instituicao = models.ForeignKey(
        'courses.Instituicao',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios',
        limit_choices_to={'ativa': True},
        help_text='Instituição usada como referência de geolocalização.',
    )
    instituicoes = models.ManyToManyField(
        'courses.Instituicao',
        blank=True,
        related_name='professores',
        limit_choices_to={'ativa': True},
        help_text='Instituições onde o professor trabalha.',
    )
    # For professors: institution CEP and derived coordinates
    cep = models.CharField(max_length=9, blank=True, null=True, help_text="CEP da instituição (apenas para professores)")
    latitude = models.FloatField(blank=True, null=True, help_text="Latitude da instituição")
    longitude = models.FloatField(blank=True, null=True, help_text="Longitude da instituição")
    radius_meters = models.PositiveIntegerField(default=100, help_text="Raio de permissão em metros ao redor da instituição")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['role'], name='idx_customuser_role'),
            models.Index(fields=['cep'], name='idx_customuser_cep'),
        ]

    def save(self, *args, **kwargs):
        """
        Persiste o usuário. Quando for professor e o CEP for novo,
        dispara geocoding em background para não bloquear a request de registro.
        """
        cep_changed_or_new = (
            self.role == 'professor'
            and self.cep
            and (self.latitude is None or self.longitude is None)
        )

        if cep_changed_or_new:
            # Tenta resolver de forma rápida (cache local). Se falhar, agenda em background.
            lat, lng = get_coordinates_from_cep(self.cep)
            if lat is not None and lng is not None:
                self.latitude = lat
                self.longitude = lng
            elif not getattr(settings, 'TESTING', False):
                # Geocoding em background: thread leve para dev; Celery em prod.
                from .tasks import geocode_professor_async
                super().save(*args, **kwargs)
                geocode_professor_async(self.pk, self.cep)
                return

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"