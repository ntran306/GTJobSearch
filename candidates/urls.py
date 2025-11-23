from django.urls import path
from . import views
from . import views_filters

app_name = 'candidates'

urlpatterns = [
    path('search/', views.search_candidates, name='search_candidates'),
    path("recommendations/", views.recommended_candidates, name="recommended_candidates"),
    
    # Filter endpoints
    path("save_filter/", views_filters.save_filter, name="save_filter"),
    path("list_filters/", views_filters.list_filters, name="list_filters"),
    path("delete_filter/<int:filter_id>/", views_filters.delete_filter, name="delete_filter"),
    
    # Notification endpoints
    path("notifications/", views_filters.get_notifications, name="get_notifications"),
    path("notifications/<int:notification_id>/read/", views_filters.mark_notification_read, name="mark_notification_read"),
    path("notifications/read_all/", views_filters.mark_all_notifications_read, name="mark_all_notifications_read"),
]