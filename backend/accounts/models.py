from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
import requests
import json
from django.conf import settings
import re
from django.core.cache import cache
from django.utils import timezone

# Database indexing strategy for performance optimization:
# - Role-based queries: Index on 'role' field for filtering professors/alunos
# - CEP lookups: Index on 'cep' field for geocoding operations
# - Additional indexes should be added based on query analysis and usage patterns

def get_coordinates_from_cep(cep):
    """
    Use the ViaCEP API (free) to get latitude and longitude from a Brazilian CEP.
    Returns (latitude, longitude) or (None, None) if not found.
    Note: ViaCEP does not provide lat/lon; we will use Nominatim (OpenStreetMap) as fallback.
    Includes caching to prevent redundant API calls.
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
                        # Cache the result for 24 hours (86400 seconds)
                        cache.set(cache_key, (lat, lon), 86400)
                        return lat, lon
    except Exception as e:
        # Log error if needed
        pass
    return None, None

import re

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('professor', 'Professor'),
        ('aluno', 'Aluno'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    matricula = models.CharField(max_length=20, blank=True, null=True, help_text="Matrícula do aluno (opcional)")
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
        # If cep is provided, check if we need to geocode
        if self.role == 'professor' and self.cep:
            # If this is an existing instance, check if CEP has changed
            if self.pk is not None:
                try:
                    old_instance = self.__class__.objects.get(pk=self.pk)
                    # Only geocode if CEP has changed or lat/lng are not set
                    if self.cep != old_instance.cep or self.latitude is None or self.longitude is None:
                        lat, lng = get_coordinates_from_cep(self.cep)
                        if lat is not None and lng is not None:
                            self.latitude = lat
                            self.longitude = lng
                except self.__class__.DoesNotExist:
                    # If we can't find the old instance, geocode if lat/lng are not set
                    if self.latitude is None or self.longitude is None:
                        lat, lng = get_coordinates_from_cep(self.cep)
                        if lat is not None and lng is not None:
                            self.latitude = lat
                            self.longitude = lng
            else:
                # This is a new instance, geocode if lat/lng are not set
                if self.latitude is None or self.longitude is None:
                    lat, lng = get_coordinates_from_cep(self.cep)
                    if lat is not None and lng is not None:
                        self.latitude = lat
                        self.longitude = lng
        super().save(*args, **kwargs)

    def schedule_geocoding(self):
        """
        Schedule geocoding for asynchronous processing.
        In a production environment, this would use Celery or similar task queue.
        Example:
            from geocode_tasks import geocode_cep_task
            geocode_cep_task.delay(self.id, self.cep)
        """
        # For now, we'll do it synchronously but with caching
        # In production, uncomment the following lines and implement Celery task:
        #
        # if self.role == 'professor' and self.cep:
        #     from .tasks import geocode_cep_task
        #     geocode_cep_task.delay(self.id, self.cep)
        pass

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"