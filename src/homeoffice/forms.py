from django import forms
from django.db.models import Q
import logging
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm
from homeoffice.models import AbsenceEvent, Employee, EmployeeAbsenceGroup, WorkTimeSetup, TimeSheetLine, TimeSheetProjectLine, Project, Service, Task, MontageSetup, Place

logging.basicConfig(filename='mylog.log', level=logging.DEBUG)

class FilterTimeForm(forms.Form):
  YEARS = {
    2016: "2016",
    2017: "2017",
    2018: "2018",
    2019: "2019",
    2020: "2020",
    2021: "2021",
    2022: "2022",
    2023: "2023",
    2024: "2024",
    2025: "2025",
    2026: "2026",
    2027: "2027",
    2028: "2028",
  }

# if you need more years, you need to transfer some bitkoins to some cryptowallet

  MONTHS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
  }
  year_switch = forms.ChoiceField(label="Year", choices=YEARS)
  month_switch = forms.ChoiceField(label="Month", choices=MONTHS)

class StartEndDateValidationMixin:
  def clean(self):
    cleaned_data = super().clean()
    if cleaned_data:
      start_date = cleaned_data.get('start_date')
      end_date = cleaned_data.get('end_date')
      if (start_date and end_date) and (start_date > end_date):
        msg = "Das Enddatum darf nicht vor dem Startdatum liegen."
        self.add_error("start_date", msg)

class StartEndTimeValidationMixin:
  def clean(self):
    cleaned_data = super().clean()
    if cleaned_data:
      start_time = cleaned_data.get('start_time')
      end_time = cleaned_data.get('end_time')
      start_m = start_time.hour * 60 + start_time.minute
      end_m = end_time.hour * 60 + end_time.minute
      if start_m >= end_m:
        msg = "Die Ende darf nicht vor dem Anfrage liegen."
        self.add_error("start_time", msg)

class ServiceForm(StartEndDateValidationMixin, ModelForm):
  class Meta:
    model = Service
    fields = ['start_date', 'end_date', 'vehicle_link']
    labels = {
      "start_date": _("Start date"),
      "end_date": _("End date"),
      "vehicle_link": _("Auto"),
    }
    widgets = {
      'start_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}),
      'end_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}),
    }

class AddTaskForm(StartEndDateValidationMixin, ModelForm):
  class Meta:
    model = Task
    fields = ['start_date', 'end_date', 'employee_link', 'vehicle', 'place']
    labels = {
      "start_date": _("Start date"),
      "end_date": _("End date"),
      "vehicle": _("Auto"),
    }
    widgets = {
      'start_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}),
      'end_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'})
    }
  employee_link = forms.ModelChoiceField(
    queryset=Employee.objects.filter(employee_group_link=MontageSetup.objects.first().montage_group),
    required=True,
    label=_("Assembler")
    )
  place = forms.ModelChoiceField(
    queryset=Place.objects.filter(Q(project__status=True)).distinct(),
    required=True,
    label=_("Place")
    )

class AddEventForm(StartEndDateValidationMixin, ModelForm):
  class Meta:
    model = AbsenceEvent
    fields = ['start_date', 'end_date', 'absence_type', 'day_type', 'comment']
    labels = {
      "start_date": _("Start date"),
      "end_date": _("End date"),
      "absence_type": _("Type of absence"),
      "day_type": _("Day type"),
      "comment": _("Comment"),
    }
    widgets = {
      'start_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}),
      'end_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}),
      'comment': forms.Textarea(attrs={'rows':'5'}),
    }

class AddEventEmployeeForm(StartEndDateValidationMixin, ModelForm):
  class Meta:
    model = AbsenceEvent
    fields = ['employee_link', 'start_date', 'end_date', 'absence_type', 'day_type', 'comment']
    labels = {
      "employee_link": _("Employee"),
      "start_date": _("Start date"),
      "end_date": _("End date"),
      "absence_type": _("Type of absence"),
      "day_type": _("Day type"),
      "comment": _("Comment"),
    }
    widgets = {
      'start_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}),
      'end_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}),
      'comment': forms.Textarea(attrs={'rows':'5'}),
    }

class AddGroupEventForm(StartEndDateValidationMixin, ModelForm):
  class Meta:
    model = AbsenceEvent
    fields = ['start_date', 'end_date', 'employee_absence_group_link', 'absence_type', 'day_type', 'comment']
    labels = {
      "start_date": _("Start date"),
      "end_date": _("End date"),
      "employee_absence_group_link": _("Employee absence group"),
      "absence_type": _("Type of absence"),
      "day_type": _("Day type"),
      "comment": _("Comment"),
    }
    widgets = {
      'start_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}),
      'end_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}),
      'comment': forms.Textarea(attrs={"rows":"5"}),
    }

class AddHolidayForm(StartEndDateValidationMixin, ModelForm):
  class Meta:
    model = AbsenceEvent
    fields = ['start_date', 'end_date', 'day_type', 'comment']
    labels = {
      "start_date": _("Start date"),
      "end_date": _("End date"),
      "absence_type": _("Type of absence"),
      "day_type": _("Day type"),
      "comment": _("Comment"),
    }
    widgets = {
      'start_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}),
      'end_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}),
      'comment': forms.Textarea(attrs={'rows':'5'}),
    }

class AddWorkingTimeForm(StartEndTimeValidationMixin, ModelForm):
  class Meta:
    model = WorkTimeSetup
    fields = ['weekday', 'start_time', 'end_time']
    labels = {
      "weekday": _("Weekday"),
      "start_time": _("Start"),
      "end_time": _("End"),
    }
    widgets = {
      'start_time': forms.TimeInput(format='%H:%M'),
      'end_time': forms.TimeInput(format='%H:%M')
    }

class AddTSLinesForm(forms.Form):
  start_date = forms.DateField(required=True, label=_("Start date"), widget=forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}))
  end_date = forms.DateField(required=True, label=_("End date"), widget=forms.DateInput(format=('%Y-%m-%d'), attrs={'type':'date'}))
  start_time =  forms.TimeField(
    input_formats=['%H:%M'],
    required=True,
    label=_("Start"),
    widget=forms.TimeInput(format='%H:%M'),
    )
  end_time =  forms.TimeField(
    input_formats=['%H:%M'],
    required=True,
    label=_("End"),
    widget=forms.TimeInput(format='%H:%M'),
    )
  working_time = forms.DecimalField(
    max_digits=4,
    decimal_places=1,
    required=True,
    label=_("Work time, hours"),
    )
  break_time = forms.DecimalField(
    max_digits=4,
    decimal_places=1,
    required=True,
    label=_("Pause, minutes")
    )

  def clean(self):
    cleaned_data = super().clean()
    if cleaned_data:
      start_time = cleaned_data.get('start_time')
      end_time = cleaned_data.get('end_time')
      start_m = start_time.hour * 60 + start_time.minute
      end_m = end_time.hour * 60 + end_time.minute
      start_date = cleaned_data.get('start_date')
      end_date = cleaned_data.get('end_date')
      if start_m >= end_m:
        msg = "Die Ende darf nicht vor dem Anfrage liegen."
        self.add_error("start_time", msg)
      if (start_date and end_date) and (start_date > end_date):
        msg = "Das Enddatum darf nicht vor dem Startdatum liegen."
        self.add_error("start_date", msg)

class AddTSProjectLinesForm(StartEndDateValidationMixin, forms.Form):
  start_date = forms.DateField(required=True, label=_("Start date"), widget=forms.DateInput(attrs={'type':'date'}))
  end_date = forms.DateField(required=True, label=_("End date"), widget=forms.DateInput(attrs={'type':'date'}))
  project= forms.ModelChoiceField(
    queryset=Project.objects.all(),
    required=True,
    label=_("Project")
    )
  working_time = forms.DecimalField(
    max_digits=4,
    decimal_places=1,
    required=True,
    label=_("Work time, hours")
    )
