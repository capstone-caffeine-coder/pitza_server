import json
from datetime import datetime

from django.http import JsonResponse
from django.db.models import Q

from .models import DonationRequest, SelectedMatchRequest, RejectedMatchRequest

# Create your views here.
def detail(request, id):
    donation_request = DonationRequest.objects.get(id=id)
    return JsonResponse(donation_request, status=200)

def create(request):
    # TODO: Create donation request
    request_data = request.POST.get('request_data')
    donation_request = DonationRequest.objects.create(request_data)
    return JsonResponse(status=201)

def match(request):

    if request.method == 'POST' and request.content_type == 'application/json':
        data = json.loads(request.body)
    else:
        data = request.POST
    

    # if not request.user.is_authenticated:
    #     return JsonResponse({
    #         'status': 'error',
    #         'message': 'Authentication required'
    #     }, status=401)
    
 
    query = Q()
    
    if 'blood_type' in data:
        query &= Q(blood_type=data['blood_type'])
    
    if 'sex' in data:
        query &= Q(sex=data['sex'])
    
    if 'location' in data:
        query &= Q(location=data['location'])
    
    # TODO: Improve age filter
    if 'age' in data:
        age = int(data['age'])
        age_min = age - 5  # For example, 5 years younger
        age_max = age + 5  # For example, 5 years older
        query &= Q(age__gte=age_min, age__lte=age_max)
    
    if 'next_donation_date' in data:
        next_donation_date = datetime.strptime(data['next_donation_date'], '%Y-%m-%d').date()
        query &= Q(donation_due_date__gte=next_donation_date)
    
    donation_requests = DonationRequest.objects.filter(query)
    
    rejected_request_ids = RejectedMatchRequest.objects.filter(
        user=request.user
    ).values_list('donation_request_id', flat=True)
    
    donation_requests = donation_requests.exclude(id__in=rejected_request_ids)
    
    requests_list = list(donation_requests.values(
        'id'
    ))
    
    match_request = requests_list[0]

    return JsonResponse(match_request, status=200)
    

def select_match(request):
    # TODO: Create selected match request
    user_id = request.user.id
    donation_request_id = request.POST.get('request_id')
    donation_request = DonationRequest.objects.get(id=donation_request_id)
    # TODO: Return 404 if donation request not found, or object not created
    selected_match_request = SelectedMatchRequest.objects.create(user_id, donation_request_id)
    donator_registered_id = donation_request.donator_registered_id
    return JsonResponse({"donator_registered_id": donator_registered_id}, status=200)

def reject_match(request):
    # TODO: Create rejected match request
    donator_id = request.user.id
    donation_request_id = request.POST.get('request_id')
    # TODO: Return 404 if donation request not found, or object not created
    rejected_match_request = RejectedMatchRequest.objects.create(donator_id, donation_request_id)
    return JsonResponse(status=201)

