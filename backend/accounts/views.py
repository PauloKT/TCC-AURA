from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from courses.models import Turma, Aula, TurmaAluno
from attendance.models import SessaoChamada, Presenca
from .serializers import UserRegistrationSerializer, CustomTokenObtainPairSerializer
from .models import CustomUser

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            },
            "message": "Usuário criado com sucesso."
        }, status=201, headers=headers)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class AlunoMinhaFrequenciaView(APIView):
    # Optimized query for frequency calculation
    """
    GET /api/aluno/minha-frequencia/
    Expects: ?turma=<turma_id>
    Returns: { percentual: number, situacao: string }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Ensure the user is an aluno
        if request.user.role != 'aluno':
            return Response(
                {'detail': 'Apenas alunos podem acessar esta informação.'},
                status=status.HTTP_403_FORBIDDEN
            )

        turma_id = request.query_params.get('turma')
        if not turma_id:
            return Response(
                {'detail': 'Parâmetro "turma" é obrigatório.'}
            )

        # Get the turma and verify the aluno is enrolled in it
        turma = get_object_or_404(Turma, id=turma_id)
        # More efficient check using the explicit through model
        is_enrolled = TurmaAluno.objects.filter(turma=turma, aluno=request.user).exists()
        if not is_enrolled:
            return Response(
                {'detail': 'Você não está matriculado nesta turma.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all sessoes (sessions) for this turma in a single query
        # This eliminates the need for a separate query on Aula and the 'in' lookup
        sessoes = SessaoChamada.objects.filter(aula__turma=turma)

        # Count total sessions
        total_sessoes = sessoes.count()

        if total_sessoes == 0:
            # No sessions yet
            return Response({
                'percentual': 0,
                'situacao': 'sem_dados'
            })

        # Count how many sessions the student has attended (with valid presence)
        present_sessoes = sessoes.filter(
            presencas__aluno=request.user,
            presencas__valida=True
        ).distinct().count()

        # Calculate percentage
        percentual = (present_sessoes / total_sessoes) * 100 if total_sessoes > 0 else 0

        # Determine status based on frequencia_minima from the materia
        frequencia_minima = turma.materia.frequencia_minima

        if percentual >= frequencia_minima:
            situacao = 'aprovado'
        elif percentual > 0:
            situacao = 'reprovado'
        else:
            situacao = 'sem_dados'

        return Response({
            'percentual': round(percentual, 2),
            'situacao': situacao
        })


def _calcular_frequencia(aluno, turma):
    """
    Calcula o percentual de frequência de um aluno em uma turma.
    Retorna (percentual, situacao).
    """
    sessoes = SessaoChamada.objects.filter(aula__turma=turma)
    total_sessoes = sessoes.count()

    if total_sessoes == 0:
        return 0.0, 'sem_dados'

    presencas_validas = sessoes.filter(
        presencas__aluno=aluno,
        presencas__valida=True,
    ).distinct().count()

    percentual = (presencas_validas / total_sessoes) * 100

    frequencia_minima = turma.materia.frequencia_minima
    if percentual >= frequencia_minima:
        situacao = 'aprovado'
    elif percentual > 0:
        situacao = 'reprovado'
    else:
        situacao = 'sem_dados'

    return round(percentual, 2), situacao


class AlunoTurmasView(APIView):
    """
    GET /api/aluno/turmas/
    Retorna todas as turmas em que o aluno está matriculado,
    cada uma com o percentual de frequência calculado e a situação.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'aluno':
            return Response(
                {'detail': 'Apenas alunos podem acessar esta informação.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Otimização: prefetch da materia e contagem de sessões em uma query agregada.
        turmas = (
            Turma.objects
            .filter(turmaaluno__aluno=request.user)
            .select_related('materia')
            .distinct()
        )

        # Pré-calcula totais e presenças em batch para eliminar N+1.
        from django.db.models import Count, Q
        agregados = {
            t['id']: t
            for t in turmas.annotate(
                total_sessoes=Count('aulas__sessoes', distinct=True),
                presencas_validas=Count(
                    'aulas__sessoes__presencas',
                    filter=Q(aulas__sessoes__presencas__aluno=request.user,
                             aulas__sessoes__presencas__valida=True),
                    distinct=True,
                ),
            ).values('id', 'total_sessoes', 'presencas_validas')
        }

        resultado = []
        for turma in turmas:
            agg = agregados.get(turma.id, {'total_sessoes': 0, 'presencas_validas': 0})
            total = agg['total_sessoes'] or 0
            pres = agg['presencas_validas'] or 0
            if total == 0:
                percentual, situacao = 0.0, 'sem_dados'
            else:
                percentual = round((pres / total) * 100, 2)
                freq_min = turma.materia.frequencia_minima
                if percentual >= freq_min:
                    situacao = 'aprovado'
                elif percentual > 0:
                    situacao = 'reprovado'
                else:
                    situacao = 'sem_dados'

            resultado.append({
                'turma_id': turma.id,
                'nome': turma.nome,
                'materia': {
                    'id': turma.materia.id,
                    'nome': turma.materia.nome,
                    'codigo': turma.materia.codigo,
                },
                'semestre': turma.semestre,
                'ano': turma.ano,
                'ativa': turma.ativa,
                'percentual': percentual,
                'situacao': situacao,
            })

        return Response({'turmas': resultado})


class AlunoEntrarTurmaView(APIView):
    """
    POST /api/aluno/entrar-turma/
    Body: { "link_acesso": "<uuid>" }
    Matricula o aluno autenticado na turma cujo link_acesso bate.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'aluno':
            return Response(
                {'detail': 'Apenas alunos podem entrar em turmas.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        link = request.data.get('link_acesso')
        if not link:
            return Response(
                {'detail': 'Campo "link_acesso" é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        turma = get_object_or_404(Turma, link_acesso=link, ativa=True)

        matricula, created = TurmaAluno.objects.get_or_create(
            turma=turma,
            aluno=request.user,
        )

        if not created:
            return Response(
                {'detail': 'Você já está matriculado nesta turma.', 'turma_id': turma.id},
                status=status.HTTP_200_OK,
            )

        return Response(
            {'detail': 'Matriculado com sucesso.', 'turma_id': turma.id},
            status=status.HTTP_201_CREATED,
        )