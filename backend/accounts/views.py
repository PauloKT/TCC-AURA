from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from courses.models import Turma, Aula
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