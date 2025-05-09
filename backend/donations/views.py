from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
import json
import datetime
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from .serializers import CreateDonationRequestSerializer, DonationRequestIdSerializer, DonationRequestSerializer, DonatorRegisteredIdSerializer, MatchRequestSerializer, MessageSerializer, RejectedMatchRequestSerializer, SelectedMatchRequestSerializer
from .models import DonationRequest, SelectedMatchRequest, RejectedMatchRequest


# @swagger_auto_schema(method='post', responses={201: DonationRequestIdSerializer})
# @api_view(['POST'])
# def create(request):
#     """
#     Create a donation request
#     """
#     # TODO: When donation due date is past today, return 400

#     request_data = json.loads(request.POST.get('request_data'))
    
#     donation_request = DonationRequest.objects.create(
#         requester_id=request.user,
#         **request_data
#     )
    
#     # Handle image upload if present
#     if 'image' in request.FILES:
#         donation_request.image = request.FILES['image']
#         donation_request.save()
        
#     return JsonResponse({
#         'id': donation_request.id,
#     }, status=201)
        
# @swagger_auto_schema(method='get', responses={200: DonationRequestSerializer})
# @api_view(['GET'])
# def detail(request, id):
#     """
#     Get a donation request by id
#     """
#     donation_request = DonationRequest.objects.get(id=id)
#     return JsonResponse(donation_request, status=200)


# @swagger_auto_schema(method='post', responses={200: MatchRequestSerializer})
# @api_view(['POST'])
# def match(request, ):
#     """
#     Match a donation request to a donator
#     """

#     if request.method == 'POST':
#         # TODO: Consider AST rather than JSON
#         data = json.loads(request.body)
#     else:
#         data = request.POST
    

#     # if not request.user.is_authenticated:
#     #     return JsonResponse({
#     #         'status': 'error',
#     #         'message': 'Authentication required'
#     #     }, status=401)
    
 
#     query = Q()
    
#     if 'blood_type' in data:
#         query &= Q(blood_type=data['blood_type'])
    
#     if 'sex' in data:
#         query &= Q(sex=data['sex'])
    
#     if 'location' in data:
#         query &= Q(location=data['location'])
    
#     # TODO: Improve age filter
#     if 'age' in data:
#         age = int(data['age'])
#         age_min = age - 5  # For example, 5 years younger
#         age_max = age + 5  # For example, 5 years older
#         query &= Q(age__gte=age_min, age__lte=age_max)
    
#     if 'next_donation_date' in data:
#         next_donation_date = datetime.strptime(data['next_donation_date'], '%Y-%m-%d').date()
#         query &= Q(donation_due_date__gte=next_donation_date)
    
#     donation_requests = DonationRequest.objects.filter(query)
    
#     rejected_request_ids = RejectedMatchRequest.objects.filter(
#         user=request.user
#     ).values_list('donation_request_id', flat=True)
    
#     donation_requests = donation_requests.exclude(id__in=rejected_request_ids)
    
#     requests_list = list(donation_requests.values(
#         'id'
#     ))
    
#     match_request = requests_list[0]

    
#     return JsonResponse(match_request, status=200)
    

class DonationRequestViewSet(viewsets.ViewSet):
    swagger_schema = SwaggerAutoSchema
    
    @swagger_auto_schema(method='get', url_path='test',
    responses={200: MessageSerializer(data={'message': 'Hello, world!'})})
    @action(detail=False, methods=['get'], url_path='test')
    def test(self, request):
        """
        Test endpoint
        """
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
    def retrieve(self, request, pk=None):
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
            next_donation_date = serializer.data['next_donation_date']
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
                return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(method='post', 
    url_path='match/select',
    request_body=DonatorRegisteredIdSerializer,
    responses={201: DonatorRegisteredIdSerializer})
    @action(detail=False, methods=['post'], url_path='match/select')
    def select(self, request):
        """
        Select a match for a donation request
        """
        # user_id = request.user.id
        # donation_request_id = request.POST.get('request_id')
        # donation_request = DonationRequest.objects.get(id=donation_request_id)
        # # TODO: Return 404 if donation request not found, or object not created
        # selected_match_request = SelectedMatchRequest.objects.create(user_id, donation_request_id)
        # donator_registered_id = donation_request.donator_registered_id
        # return JsonResponse({"donator_registered_id": donator_registered_id}, status=200)
        
        serializer = SelectedMatchRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # TODO: update donation request with donator_registered_id -> donator_registered.
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(method='post', url_path='match/reject', 
    request_body=DonatorRegisteredIdSerializer,
    responses={201: MessageSerializer(data={})})
    @action(detail=False, methods=['post'], url_path='match/reject')
    def reject(self, request):
        """
        Reject a match for a donation request
        """
        # donator_id = request.user.id
        # donation_request_id = request.POST.get('request_id')
        # # TODO: Return 404 if donation request not found, or object not created
        # rejected_match_request = RejectedMatchRequest.objects.create(donator_id, donation_request_id)
        # return JsonResponse(status=201)
        
        serializer = RejectedMatchRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



