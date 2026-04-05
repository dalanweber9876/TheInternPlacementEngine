from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("upload-student/", views.upload_student_csv, name="upload_student"),
    path("upload-employer/", views.upload_employer_csv, name="upload_employer"),
]