from rest_framework import generics, permissions
from .models import DonationPost, RequestPost
from .serializers import DonationPostSerializer, RequestPostSerializer
from rest_framework.parsers import MultiPartParser, FormParser

#로그인
#from django.contrib.auth import get_user_model
#User = get_user_model()

# 기부하기
class DonationPostList(generics.ListAPIView):
    queryset = DonationPost.objects.all().order_by('-created_at')
    serializer_class = DonationPostSerializer
    permission_classes = [permissions.AllowAny]

class DonationPostCreate(generics.CreateAPIView):
    queryset = DonationPost.objects.all()
    serializer_class = DonationPostSerializer
    #permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    """
    #로그인
    def perform_create(self, serializer):
        serializer.save(donor=self.request.user)
    """
    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(donor=self.request.user)
        else:
            serializer.save(donor=None)  # 로그인 안 되어 있을 경우 None으로 저장

class DonationPostDetail(generics.RetrieveAPIView):
    queryset = DonationPost.objects.all()
    serializer_class = DonationPostSerializer
    permission_classes = [permissions.AllowAny]

# 요청하기
class RequestPostList(generics.ListAPIView):
    queryset = RequestPost.objects.all().order_by('-created_at')
    serializer_class = RequestPostSerializer
    permission_classes = [permissions.AllowAny]

class RequestPostCreate(generics.CreateAPIView):
    queryset = RequestPost.objects.all()
    serializer_class = RequestPostSerializer
    #permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser] 

    def perform_create(self, serializer):
        #로그인
        serializer.save(requester=self.request.user)
        #test_user = User.objects.first()  # 또는 특정 ID로 지정: User.objects.get(id=1)
        #serializer.save(requester=test_user)

class RequestPostDetail(generics.RetrieveAPIView):
    queryset = RequestPost.objects.all()
    serializer_class = RequestPostSerializer
    permission_classes = [permissions.AllowAny]