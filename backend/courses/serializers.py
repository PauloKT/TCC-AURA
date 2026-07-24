from rest_framework import serializers
from .models import Materia, Turma, Aula, TurmaAluno
from django.contrib.auth import get_user_model

User = get_user_model()

class MateriaSerializer(serializers.ModelSerializer):
    professor_username = serializers.CharField(source='professor.username', read_only=True)

    class Meta:
        model = Materia
        fields = ['id', 'nome', 'codigo', 'carga_horaria', 'frequencia_minima', 'professor', 'professor_username', 'created_at']
        read_only_fields = ['professor', 'created_at']

class TurmaSerializer(serializers.ModelSerializer):
    materia_nome = serializers.CharField(source='materia.nome', read_only=True)
    materia_codigo = serializers.CharField(source='materia.codigo', read_only=True)

    class Meta:
        model = Turma
        fields = ['id', 'nome', 'materia', 'materia_nome', 'materia_codigo', 'semestre', 'ano', 'link_acesso', 'ativa', 'created_at']
        read_only_fields = ['link_acesso', 'created_at']

class TurmaAlunoSerializer(serializers.ModelSerializer):
    aluno_username = serializers.CharField(source='aluno.username', read_only=True)
    turma_nome = serializers.CharField(source='turma.nome', read_only=True)

    class Meta:
        model = TurmaAluno
        fields = ['id', 'turma', 'aluno', 'aluno_username', 'turma_nome', 'data_entrada']
        read_only_fields = ['data_entrada']

class AulaSerializer(serializers.ModelSerializer):
    turma_nome = serializers.CharField(source='turma.nome', read_only=True)

    class Meta:
        model = Aula
        fields = ['id', 'turma', 'titulo', 'data', 'hora_inicio', 'hora_fim', 'criada_em']
        # Note: field names in model are horario_inicio and horario_fim
        # We'll map them accordingly
        extra_kwargs = {
            'horario_inicio': {'source': 'horario_inicio'},
            'horario_fim': {'source': 'horario_fim'},
            'criada_em': {'source': 'criada_em'},
        }

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Adjust field names to match expected frontend maybe
        return rep