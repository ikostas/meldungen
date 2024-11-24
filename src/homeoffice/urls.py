from django.urls import path, include

from . import views

urlpatterns = [
  path('', views.index, name='index'),
  path('calendar/', views.CalendarView.as_view(), name='calendar'),
  path('mycal/', views.MyCalendarView.as_view(), name='mycal'),
  path('timesheet/', views.TimeSheetView.as_view(), name='timesheet'),
  path('montage/', views.MontageCalendarView.as_view(), name='montage'),
  path('montage/add_service/', views.ServiceAddView.as_view(), name='add_service'),
  path('montage/delete_service/<int:id>/', views.service_delete_view, name='delete_service'),
  path('montage/edit_service/<int:id>/', views.ServiceEditView.as_view(), name='edit_service'),
  path('montage/add_task/', views.TaskAddView.as_view(), name='add_task'),
    path('montage/add_date_task/<int:day>/<int:month>/<int:year>/<str:place>/', views.TaskDateAddView.as_view(), name='add_date_task'),
  path('montage/delete_task/<int:id>/', views.task_delete_view, name='delete_task'),
  path('montage/edit_task/<int:id>/', views.TaskEditView.as_view(), name='edit_task'),
  path('montage/mycal_montage/', views.MyMontageCalendarView.as_view(), name='mycal_montage'),
  path('default_time/', views. DefaultTimeView.as_view(), name='default_time'),
  path('<int:id>/delete_time/', views.default_time_delete, name='default_time_delete'),
  path('<int:id>/view/', views.detailed_event_view, name='event_view'),
  path('<int:id>/delete/', views. event_delete_view, name='event_delete'),
  path('<int:id>/edit/', views.DetailedEditView.as_view(), name='event_edit'),
  path('add_event/<str:event_type>/', views.AddEventView.as_view(), name='add_event'),
  path('add_time/<str:line_type>/<int:timesheet>/', views.AddTimeView.as_view(), name='add_time'),
#  path("accounts/", include("django.contrib.auth.urls")),
]
