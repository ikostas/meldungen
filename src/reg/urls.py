from django.urls import path, include

from . import views

urlpatterns = [
  # Working with multiple issues

  # list issues - redirects to a list with the same issue_type
  path("<slug:issue_type>/list/", views.IssueList.as_view(), name="issue_list"),

  # Working with 1 issue

  # add issue - redirects to menu
  path("<slug:issue_type>/add/", views.AddIssue.as_view(), name="issue_add"), 
  # detailed issue - redirects to the same view (issue detailed view) 
  path("satisfied/", views.satisfied_view, name="satisfied"), 
  path("<int:id>/view/", views.ViewDetailedIssue.as_view(), name="issue_detailed"),
  # update issue - redirects to a list with the same issue_type
  path("<int:id>/update/", views.UpdateIssue.as_view(), name="issue_update"),
  # change issue status - redirects to a list with the same issue_type
  path("<int:id>/change_status/", views.issue_status_change_view, name="issue_status_change"),
  
  # Delete operations

  # redirects to a list with the same issue_type
  path("<int:id>/delete/", views.issue_delete_view, name="issue_delete"),
  path("<int:pic_id>/<int:issue_id>/delete_pic/", views.issue_delete_pic_view, name="issue_delete_pic"),
  path("<int:comment_id>/<int:issue_id>/delete_comment/", views.issue_delete_comment_view, name="issue_delete_comment"),

  # General

  # redirects to menu if authorized
  path("", views.index, name="index"),
  path("menu/", views.menu, name="menu"),
  path("accounts/", include("django.contrib.auth.urls")),
  ]
