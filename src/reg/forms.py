from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm
from reg.models import Issue, IssuePic, IssueComment

# multiple file upload 
class MultipleFileInput(forms.ClearableFileInput):
  allow_multiple_selected = True

# multiple file upload 
class MultipleFileField(forms.ImageField):
  def __init__(self, *args, **kwargs):
    kwargs.setdefault("widget", MultipleFileInput())
    super().__init__(*args, **kwargs)

  def clean(self, data, initial=None):
    single_file_clean = super().clean
    if isinstance(data, (list, tuple)):
        result = [single_file_clean(d, initial) for d in data]
    else:
        result = single_file_clean(data, initial)
    return result

class DefectForm(ModelForm):
  class Meta:
    model = Issue
    fields = ['name', 'date', 'project', 'description'] 
    labels = {
      "name": _("Keywords"),
      "date": _("Creation date"),
      "project": _("Project No."),
      "description": _("Defect description"),
    }
    widgets = {
      'date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}),
    }

class DangerForm(ModelForm):
  class Meta:
    model = Issue 
    fields = ['name', 'date', 'description'] 
    labels = {
      "name": _("Keywords"),
      "date": _("Creation date"),
      "description": _("Situation description"),
    }
    widgets = {
      'date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}),
    }
    
class SuggestForm(ModelForm):
  class Meta:
    model = Issue 
    fields = ['name', 'description'] 
    labels = {
      "name": _("Keywords"),
      "description": _("Suggestion"),
    }
    widgets = {
      'date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}),
    }
    
class PicsForm(forms.Form):
  pics = MultipleFileField(label="Bilder", required=False)

class FilterIssuesForm(forms.Form):
  OPTIONS = {
    "all": "All",
    "open": "Open",
    "closed": "Closed",
  }
  TYPES = {
    "all": "All",
    "defect": "Defects",
    "danger": "Unsafe situation",
    "suggest": "Suggestion"
  }
  data_filter = forms.ChoiceField(label="What to show:", choices=OPTIONS)
  type_filter = forms.ChoiceField(label="Report type", choices=TYPES)

class IssueCommentsForm(forms.Form):
  comment = forms.CharField(widget=forms.Textarea(attrs={"rows":"5"}), label="Comment")
