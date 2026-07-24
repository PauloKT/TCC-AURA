from django.db import models
from django.conf import settings
import uuid

class Materia(models.Model):
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    carga_horaria = models.IntegerField(help_text="Carga horária total em horas")
    frequencia_minima = models.IntegerField(default=75, help_text="Percentual mínimo de frequência para aprovação")
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'professor'},
        related_name='materias'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.codigo})"

    class Meta:
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['professor']),
        ]


class Turma(models.Model):
    nome = models.CharField(max_length=100)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='turmas')
    semestre = models.CharField(max_length=20)  # e.g., "2024.1"
    ano = models.IntegerField()
    link_acesso = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    ativa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} - {self.materia.nome} ({self.semestre}/{self.ano})"

    class Meta:
        indexes = [
            models.Index(fields=['ativa']),
            models.Index(fields=['ano', 'semestre']),
            models.Index(fields=['materia', 'ativa']),
        ]


class TurmaAluno(models.Model):
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='alunos')
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'aluno'},
        related_name='turmas'
    )
    data_entrada = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('turma', 'aluno')
        verbose_name = "Turma Aluno"
        verbose_name_plural = "Turmas Alunos"
        indexes = [
            models.Index(fields=['aluno']),
            models.Index(fields=['data_entrada']),
        ]

    def __str__(self):
        return f"{self.aluno.username} na {self.turma}"


class Aula(models.Model):
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='aulas')
    titulo = models.CharField(max_length=200)
    data = models.DateField()
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField()
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.turma} ({self.data})"

    class Meta:
        indexes = [
            models.Index(fields=['data']),
            models.Index(fields=['turma', 'data']),
            models.Index(fields=['criada_em']),
        ]