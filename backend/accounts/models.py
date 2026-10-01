from django.contrib.auth.models import AbstractUser
from django.db import models


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
    # Mantidos para leitura dos cadastros anteriores às instituições.
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

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
