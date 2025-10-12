from django.shortcuts import render
from .models import Profile

def candidate_search(request):
    query = request.GET.get('q')
    location = request.GET.get('location')
    skill = request.GET.get('skill')

    candidates = Profile.objects.all()

    if query:
        candidates = candidates.filter(user__username__icontains=query)
    if location:
        candidates = candidates.filter(location__icontains=location)
    if skill:
        candidates = candidates.filter(skills__icontains=skill)

    return render(request, 'profiles/candidate_search.html', {
        'candidates': candidates,
        'query': query,
        'location': location,
        'skill': skill,
    })
