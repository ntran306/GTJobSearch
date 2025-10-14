from django.shortcuts import render
from .models import Profile
from django.shortcuts import render, get_object_or_404
from accounts.models import JobSeekerProfile

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

def view_profile(request, user_id):
    """Display a candidate’s public profile."""
    profile = get_object_or_404(JobSeekerProfile, user__id=user_id)
    return render(request, 'profiles/view_profile.html', {'profile': profile})

