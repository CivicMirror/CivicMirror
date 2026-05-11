from knox.auth import TokenAuthentication
from rest_framework import mixins, permissions, viewsets

from .models import MockVote
from .serializers import MockVoteSerializer


class MockVoteViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = MockVoteSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MockVote.objects.select_related('race', 'candidate', 'measure_option').filter(user=self.request.user)
