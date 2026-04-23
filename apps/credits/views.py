from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CreditTransaction
from .serializers import CreditTransactionSerializer, CreditRequestSerializer
from .services import log_credit_request
from apps.accounts.models import Profile


class CreditBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
            return Response({
                'credits_remaining': profile.credits_remaining,
                'subscription_tier': profile.subscription_tier
            })
        except Profile.DoesNotExist:
            return Response({
                'credits_remaining': 0,
                'subscription_tier': 'free'
            })


class CreditTransactionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = CreditTransaction.objects.filter(
            user=request.user
        ).order_by('-created_at')
        serializer = CreditTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class CreditRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreditRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        log_credit_request(
            request.user,
            serializer.validated_data.get('message', '')
        )
        return Response({'message': 'Credit request logged'})