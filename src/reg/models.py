from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Issue(models.Model):
  ISSUE_STATUSES = {
    "open": "Open",
    "closed": "Closed",
  }
  ISSUE_TYPES = {
    "defect": "Defect",
    "suggest": "Suggestion",
    "danger": "Dangerous situation",
  }
  name = models.CharField(max_length=120, verbose_name="Name")
  date = models.DateField(verbose_name="Date when issue was found")
  project = models.CharField(max_length=120, verbose_name="Project No.")
  description = models.TextField(max_length=500, verbose_name="issue descripion")
  created = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
  created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='users_issues', verbose_name="Created by")
  status = models.CharField(
    max_length=20,
    choices=ISSUE_STATUSES,
    default="open",
    verbose_name="Status",
    )
  issue_type = models.CharField(
    max_length=25,
    choices=ISSUE_TYPES,
    default="defect",
    verbose_name="Issue type",
    )
  
  def __str__(self):
    return self.name
      
class IssuePic(models.Model):
  pic = models.ImageField(upload_to="issues/", verbose_name="Bilder") 
  issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='issue_pics')

  def __str__(self):
    return self.pic

class IssueComment(models.Model):
  comment = models.TextField(max_length=500, verbose_name="Kommentar")
  created = models.DateTimeField(auto_now_add=True, verbose_name="Hergestellt in")
  created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='users_issue_comments', verbose_name="Created by")
  issue = models.ForeignKey(Issue, on_delete=models.PROTECT, related_name='issue_user_comments')

  def __str__(self):
    return self.comment
