from rest_framework import serializers
from .models import Instituicao, Materia, Turma, Aula, TurmaAluno
from django.contrib.auth import get_user_model

User = get_user_model()

class MateriaSerializer(serializers.ModelSerializer):
    professor_username = serializers.CharField(source='professor.username', read_only=True)

    class Meta:
        model = Materia
        fields = ['id', 'nome', 'codigo', 'carga_horaria', 'frequencia_minima', 'professor', 'professor_username', 'created_at']
        read_only_fields = ['professor', 'created_at']


class InstituicaoSerializer(serializers.ModelSerializer):
    """Expõe instituições ativas e suas coordenadas confirmadas."""

    endereco_completo = serializers.ReadOnlyField()

    class Meta:
        model = Instituicao
        fields = [
            'id', 'nome', 'logradouro', 'numero', 'bairro', 'cidade',
            'estado', 'pais', 'endereco_completo', 'latitude', 'longitude',
            'radius_meters', 'geocodificada_em', 'geocoding_source', 'ativa',
        ]
        read_only_fields = [
            'latitude', 'longitude', 'geocodificada_em', 'geocoding_source',
        ]

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
    hora_inicio = serializers.TimeField(source='horario_inicio')
    hora_fim = serializers.TimeField(source='horario_fim')
    criada_em = serializers.DateTimeField(source='criada_em', read_only=True)

    class Meta:
        model = Aula
        fields = ['id', 'turma', 'titulo', 'data', 'hora_inicio', 'hora_fim', 'criada_em']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Adjust field names to match expected frontend maybe
        return rep