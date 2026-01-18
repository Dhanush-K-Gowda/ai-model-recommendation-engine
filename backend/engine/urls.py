from django.urls import path
from engine import views

app_name = 'engine'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),

    # Ingestion endpoints
    path('ingest/', views.ingest_trace, name='ingest_trace'),
    path('ingest/bulk/', views.ingest_traces_bulk, name='ingest_traces_bulk'),

    # Applications endpoints
    path('applications/', views.applications_list, name='applications_list'),
    path('applications/<str:application_id>/', views.application_detail, name='application_detail'),

    # Recommendations endpoints
    path('recommendations/', views.recommendations_list, name='recommendations_list'),
    path('recommendations/generate/', views.generate_recommendations_for_app, name='generate_recommendations'),

    # Dashboard endpoints
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
]
