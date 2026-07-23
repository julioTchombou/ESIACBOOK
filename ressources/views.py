from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Resource
from .serializers import ResourceSerializer, ResourceCreateUpdateSerializer
from .permissions import IsProfessorOrReadOnly, IsOwnerOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from subscriptions.models import Subscription  # Ajouté pour filtrer selon les abonnements

class ResourceListCreateView(generics.ListCreateAPIView):
    serializer_class = ResourceSerializer
    permission_classes = [IsProfessorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['resource_type', 'subject', 'level', 'uploaded_by__id']
    search_fields = ['title', 'description', 'subject', 'level', 'uploaded_by__first_name', 'uploaded_by__last_name']
    ordering_fields = ['uploaded_at', 'title', 'subject', 'level']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            prof_ids = Subscription.objects.filter(student=user).values_list('professor_id', flat=True)
            return Resource.objects.filter(uploaded_by__id__in=prof_ids)
        elif user.role == 'professor':
            return Resource.objects.filter(uploaded_by=user)
        else:
            return Resource.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ResourceCreateUpdateSerializer
        return ResourceSerializer

    def perform_create(self, serializer):
        # Vérifie que seul un professeur peut uploader
        if self.request.user.role != 'professor':
            raise permissions.PermissionDenied("Seuls les professeurs peuvent uploader des ressources.")
        serializer.save(uploaded_by=self.request.user)

class ResourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [IsProfessorOrReadOnly, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ResourceCreateUpdateSerializer
        return ResourceSerializer