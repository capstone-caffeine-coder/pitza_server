from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.utils import swagger_auto_schema
import datetime
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .serializers import CreateDonationRequestSerializer, DonationRequestIdSerializer, DonationRequestSerializer, DonatorRegisteredIdSerializer, MatchRequestSerializer, MessageSerializer, RejectedMatchRequestSerializer, SelectedMatchRequestSerializer
from .models import DonationRequest

class DonationRequestViewSet(viewsets.ViewSet):
    swagger_schema = SwaggerAutoSchema
    
    @swagger_auto_schema(method='get',
                         responses={200: MessageSerializer})
    @action(detail=False, methods=['get'], url_path='test')
    def test(self, request):
        # Save the file to MinIO storage bucket name: pitza-media
        default_storage.save('test.png', ContentFile(open('test.png', 'rb').read()))
        return Response({"message": "Hello, world!"})
  


    @swagger_auto_schema(request_body=CreateDonationRequestSerializer,
    responses={201: DonationRequestIdSerializer})
    def create(self, request):
        serializer = CreateDonationRequestSerializer(data=request.data)
        if serializer.is_valid():
            donation_request_serializer = DonationRequestSerializer(data=serializer.data)
            if donation_request_serializer.is_valid():
                donation_request_serializer.save()
                response_serializer = DonationRequestIdSerializer(donation_request_serializer.instance.id)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            else:
                print(donation_request_serializer.errors)
                return Response(donation_request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # else:
        #     print(serializer.errors)
        #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    
    @swagger_auto_schema(responses={200: DonationRequestSerializer})
    def retrieve(self, pk=None):
        queryset = DonationRequest.objects.all()
        donation_request = get_object_or_404(queryset, pk=pk)
        serializer = DonationRequestSerializer(donation_request)
        return Response(serializer.data)
    
    @swagger_auto_schema(method='post', request_body=MatchRequestSerializer,
    responses={200: DonationRequestIdSerializer})
    @action(detail=False, methods=['post'], url_path='match')
    def match(self, request):
        serializer = MatchRequestSerializer(data=request.data)
        if serializer.is_valid():
            next_donation_date = datetime.datetime.strptime(serializer.data['next_donation_date'], '%Y-%m-%d').date()
            # Add a 7-day buffer before and after the donation due date
            queryset = DonationRequest.objects.filter(
                blood_type=serializer.data['blood_type'],
                sex=serializer.data['sex'],
                location=serializer.data['location'],
                age__gte=serializer.data['age'] - 5,
                age__lte=serializer.data['age'] + 5,
                donation_due_date__gte=next_donation_date - datetime.timedelta(days=7),
                donation_due_date__lte=next_donation_date + datetime.timedelta(days=7)
            )
            if queryset.exists():
                response_serializer = DonationRequestIdSerializer(queryset.first().id)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "No matching donation requests found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(method='post', 
    url_path='match/select',
    request_body=SelectedMatchRequestSerializer,
    responses={201: DonatorRegisteredIdSerializer})
    @action(detail=False, methods=['post'], url_path='match/select')
    def select(self, request):
        """
        Select a match for a donation request
        """
        serializer = SelectedMatchRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()        
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(method='post', url_path='match/reject', 
    request_body=RejectedMatchRequestSerializer,
    responses={201: MessageSerializer(data={})})
    @action(detail=False, methods=['post'], url_path='match/reject')
    def reject(self, request):
        """
        Reject a match for a donation request
        """
        serializer = RejectedMatchRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



