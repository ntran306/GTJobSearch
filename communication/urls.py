from django.urls import path
from . import views

app_name = "communication"

urlpatterns = [
    # Email contact
    path("contact/<int:user_id>/", views.contact_user, name="contact_user"),

    # Messaging (Twilio Conversations)
    path("messaging/list/", views.list_conversations, name="list_conversations"),
    path("messaging/token/", views.get_twilio_token, name="get_twilio_token"),
    path("messaging/start/<int:user_id>/", views.start_conversation, name="start_conversation"),
    path("messaging/thread/<str:conversation_sid>/", views.conversation_view, name="conversation_view"),

    # Connections
    path("connections/request/<int:user_id>/", views.connections_request, name="connections_request"),
    path("connections/accept/<int:user_id>/", views.connections_accept, name="connections_accept"),
    path("connections/decline/<int:user_id>/", views.connections_decline, name="connections_decline"),
    path("connections/remove/<int:user_id>/", views.connections_remove, name="connections_remove"),
    path("api/connections", views.api_connections, name="api_connections"),
]