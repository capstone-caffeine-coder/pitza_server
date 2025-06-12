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
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Case, When, IntegerField # Import necessary functions
from datetime import timedelta
from django.core.files.storage import storages
from django.core.files import File

from .serializers import CreateDonationRequestSerializer, DonationRequestIdSerializer, DonationRequestSerializer, DonatorRegisteredIdSerializer, MatchRequestSerializer, MessageSerializer, RejectedMatchRequestSerializer, SelectedMatchRequestSerializer
from .models import DonationRequest, RejectedMatchRequest

class DonationRequestViewSet(viewsets.ViewSet):
    swagger_schema = SwaggerAutoSchema
    parser_classes = [MultiPartParser, FormParser]
    
    @swagger_auto_schema(method='get',
                         responses={200: MessageSerializer})
    @action(detail=False, methods=['get'], url_path='test')
    def test(self, request):
        
        # Save the file to MinIO storage bucket name: pitza-media
        default_storage.save('test.png', ContentFile(open('/backend/test_assets/test.png', 'rb').read()))
        img = storages['default'].url('test.png')
        
        return Response({"message": "Test successful", "image_url": img}, status=status.HTTP_200_OK)
  
    @swagger_auto_schema(request_body=CreateDonationRequestSerializer,
    responses={201: DonationRequestIdSerializer})
    def create(self, request):
        serializer = CreateDonationRequestSerializer(data=request.data)
        
        if serializer.is_valid():

            validated_data = serializer.validated_data
            image_file = validated_data.get('image', None)
            copied_validated_data = validated_data.copy()
            
            if 'image' in copied_validated_data:
               del copied_validated_data['image']
            
            donation_request_serializer = DonationRequestSerializer(data=copied_validated_data)

            if donation_request_serializer.is_valid():
                donation_request = donation_request_serializer.save()
                
                if image_file:
                    django_file = File(image_file, name=image_file.name)
                    donation_request.image = django_file
                    donation_request.save()

                response_serializer = DonationRequestIdSerializer(donation_request)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            else:
                print(donation_request_serializer.errors)
                return Response(donation_request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            print(serializer.errors)
        #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @swagger_auto_schema(responses={200: DonationRequestSerializer})
    def retrieve(self, request, pk):
        donation_request = get_object_or_404(DonationRequest, pk=pk)
        serializer = DonationRequestSerializer(donation_request)
        return Response(serializer.data)
    
    @swagger_auto_schema(method='post', request_body=MatchRequestSerializer,
    responses={200: DonationRequestIdSerializer})
    @action(detail=False, methods=['post'], url_path='match')
    def match(self, request):
        serializer = MatchRequestSerializer(data=request.data)
        if serializer.is_valid():
            
            # calculate the date range for the next donation date
            next_donation_date = datetime.datetime.strptime(serializer.data['next_donation_date'], '%Y-%m-%d').date()
              
            requested_blood_type = serializer.validated_data['blood_type']
            requested_sex = serializer.validated_data['sex']
            requested_location = serializer.validated_data['location']
            requested_age = serializer.validated_data['age']
            
            # set the ranges for age and date
            age_min = requested_age - 5
            age_max = requested_age + 5
            date_min = next_donation_date - timedelta(days=7)
            date_max = next_donation_date + timedelta(days=7)
 

            # get the list of rejected donation request IDs for the current user
            rejected_ids = RejectedMatchRequest.objects.filter(user=serializer.validated_data['id']).values_list('donation_request_id', flat=True)

            queryset = DonationRequest.objects.filter(
                blood_type=requested_blood_type,
                donation_due_date__gte=date_min,  
                donation_due_date__lte=date_max
            ).exclude(id__in=rejected_ids)

            # filter the queryset based on sex, location, age, and date
            queryset = queryset.annotate(
                matches_sex=Case(
                    When(sex=requested_sex, then=1),
                    default=0,
                    output_field=IntegerField()
                ),
                matches_location=Case(
                    When(location=requested_location, then=1),
                    default=0,
                    output_field=IntegerField()
                ),
                matches_age_range=Case(
                    When(age__gte=age_min, age__lte=age_max, then=1),
                    default=0,
                    output_field=IntegerField()
                ),
            )

            queryset = queryset.order_by(
                '-matches_location',
                '-matches_sex',       
                '-matches_age_range',  
            )
            
            if queryset.exists():
                response_serializer = DonationRequestIdSerializer(queryset.first())
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
            response_serializer = DonatorRegisteredIdSerializer(serializer.instance.donation_request)       
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(method='post', url_path='match/reject', 
    request_body=RejectedMatchRequestSerializer,
    responses={201: MessageSerializer})
    @action(detail=False, methods=['post'], url_path='match/reject')
    def reject(self, request):
        """
        Reject a match for a donation request
        """
        serializer = RejectedMatchRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response_serializer = MessageSerializer(data={'message': 'Match rejected'})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



