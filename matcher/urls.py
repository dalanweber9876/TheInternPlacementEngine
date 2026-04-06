from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("upload-student/", views.upload_student_csv, name="upload_student"),
    path("upload-employer/", views.upload_employer_csv, name="upload_employer"),
    path('report/', views.generate_report, name='generate_report'),
    path('clear_employer_file/', views.clear_employer_file, name='clear_employer_file'),
    path('clear_student_file/', views.clear_student_file, name='clear_student_file'),
]