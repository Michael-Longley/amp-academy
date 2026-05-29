from django.urls import path

from . import views

app_name = "sponsorship"

urlpatterns = [
    # Portal home — list institutions for this user
    path("", views.portal_home, name="portal_home"),

    # Student management (institution-scoped)
    path("<slug:institution_slug>/", views.student_list, name="student_list"),
    path("<slug:institution_slug>/add/", views.student_add, name="student_add"),
    path("<slug:institution_slug>/student/<int:pk>/", views.student_detail, name="student_detail"),
    path("<slug:institution_slug>/student/<int:pk>/edit/", views.student_edit, name="student_edit"),
    path("<slug:institution_slug>/student/<int:pk>/remove/", views.student_remove, name="student_remove"),

    # Institution course access
    path("<slug:institution_slug>/courses/", views.institution_courses, name="institution_courses"),
    path("<slug:institution_slug>/courses/add/", views.course_add, name="course_add"),
    path("<slug:institution_slug>/courses/<int:pk>/edit/", views.course_edit, name="course_edit"),
    path("<slug:institution_slug>/courses/<int:pk>/remove/", views.course_remove, name="course_remove"),

    # Teacher management (admin-only)
    path("<slug:institution_slug>/teachers/", views.teacher_list, name="teacher_list"),
    path("<slug:institution_slug>/teachers/add/", views.teacher_add, name="teacher_add"),
    path("<slug:institution_slug>/teachers/<int:teacher_pk>/assign/", views.teacher_assign, name="teacher_assign"),

    # Student self-enrollment flows
    path("invite/<uuid:token>/", views.accept_invitation, name="accept_invitation"),
    path("claim/", views.claim_sponsorship, name="claim_sponsorship"),
]
