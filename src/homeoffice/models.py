from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class EmployeeAbsenceGroup(models.Model):
  name = models.CharField(max_length=120, verbose_name="Name")
  description = models.TextField(max_length=500, verbose_name="Description")

  def __str__(self):
    return self.name

class AbsenceType(models.Model):
  name = models.CharField(max_length=120, verbose_name="Name")
  description = models.TextField(max_length=500, verbose_name="Description")
  color = models.CharField(max_length=30, verbose_name="Farbe")
  working_time = models.BooleanField(default=False)

  def __str__(self):
    return self.name

class EmployeeGroup(models.Model):
  name = models.CharField(max_length=120, verbose_name="Name")
  description = models.TextField(max_length=500, verbose_name="Description")

  def __str__(self):
    return self.name

class Employee(models.Model):
  user_link = models.OneToOneField(
    User,
    on_delete=models.PROTECT,
    primary_key=True,
    )
  # user_link = models.ForeignKey(User, on_delete=models.PROTECT, related_name='user_linked', verbose_name="User")
  employee_group_link = models.ForeignKey(EmployeeGroup, on_delete=models.PROTECT, related_name='users_group', verbose_name="User group")
  employee_absence_group_link = models.ForeignKey(EmployeeAbsenceGroup, on_delete=models.PROTECT, related_name='absence_group', verbose_name="User absence group", blank=True, null=True)
  default_time_category_is_office = models.BooleanField(verbose_name="Default time category is office", default=True, blank=True, null=False) # otherwise workshop

  def __str__(self):
    return f"{self.user_link.first_name} {self.user_link.last_name}"
    # return str(self.user_link.first_name) + " " str(self.user_link.last_name)

class Project(models.Model):
  number = models.CharField(max_length=120, verbose_name="Number", blank=True, null=False)
  description = models.TextField(max_length=500, verbose_name="Description", blank=True, null=False)
  status = models.BooleanField(verbose_name="Active", default=True, blank=True, null=False)

  def __str__(self):
    return self.number

class Place(models.Model):
  project = models.ForeignKey(Project, on_delete=models.PROTECT, verbose_name="Project place", null=False, blank=False)
  name = models.CharField(max_length=120, verbose_name="Name", blank=True, null=False)

  def __str__(self):
    return f"{self.project.number} {self.name}"

class Vehicle(models.Model):
  name = models.CharField(max_length=120, verbose_name="Name", blank=True, null=False)
  number = models.CharField(max_length=120, verbose_name="Number", blank=True, null=False)
  employee = models.ForeignKey(Employee, on_delete=models.PROTECT, verbose_name="Employee's default car", null=True, blank=True)

  def __str__(self):
    if self.employee:
      return f"{self.name} ({self.employee.user_link.first_name} {self.employee.user_link.last_name})"
    else:
      return f"{self.name}"

class Task(models.Model):
  start_date = models.DateField(verbose_name="Anfangsdatum", null=False, blank=False)
  end_date = models.DateField(verbose_name="Datum des Endes", null=False, blank=False)
  employee_link = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='workers_task', verbose_name="Worker", null=False, blank=False)
  vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='vehicle_task', verbose_name="Vehicle", null=True, blank=True)
  place = models.ForeignKey(Place, on_delete=models.PROTECT, related_name='place_task', verbose_name="Task place", null=False, blank=False)

  def __str__(self):
    return f"{self.start_date} -- {self.end_date} {self.employee_link} {self.place}"

class Service(models.Model):
  start_date = models.DateField(verbose_name="Anfangsdatum", null=False, blank=False)
  end_date = models.DateField(verbose_name="Datum des Endes", null=False, blank=False)
  vehicle_link = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='vehicle_service', verbose_name='Vehicle', null=False, blank=False)

  def __str__(self):
    return f"{self.start_date} -- {self.end_date} {self.vehicle_link}"

class MontageSetup(models.Model):
  montage_group = models.ForeignKey(EmployeeGroup, on_delete=models.PROTECT, verbose_name="Montage group", related_name="default_montage_group", null=True)

class WorkTimeBase(models.Model):
  WEEKDAYS = {
    "1": "Mo",
    "2": "Di",
    "3": "Mi",
    "4": "Do",
    "5": "Fr",
    "6": "Sa",
    "7": "So"
  }
  employee = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="User", null=False, blank=False)
  weekday = models.CharField(max_length=4, choices=WEEKDAYS, verbose_name="Weekday", null=False, blank=False)
  start_time=models.TimeField(null=True, blank=False)
  end_time=models.TimeField(null=True, blank=False)

  class Meta:
    abstract=True
  
  def __str__(self):
    return f"{self.employee} {self.weekday}"

class WorkTimeSetup(WorkTimeBase):
  pass

class DefaultWorkTime(WorkTimeBase):
  working_time=models.DecimalField(null=True, max_digits=4, decimal_places=1)
  break_time=models.DecimalField(null=True, max_digits=4, decimal_places=1)

class TimeSheet(models.Model):
  STATUSES = {
    'created': 'Erstellt',
    'sent': 'Gesendet',
    'approved': 'Genehmigt',
    'rejected': 'Abgelehnt'
  }
  employee=models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="User", null=False, blank=False)
  year=models.IntegerField(null=False)
  month=models.IntegerField(null=False)
  status=models.CharField(max_length=10, choices=STATUSES, default='created', verbose_name='Event status')

  def __str__(self):
    return f"{self.employee} {self.year} {self.month} {self.status}" 

class TimeSheetLine(models.Model):
  ts=models.ForeignKey(TimeSheet, on_delete=models.PROTECT, verbose_name="Time Sheet", null=False, blank=False)
  day=models.IntegerField(null=False)
  start_time=models.TimeField(null=True, blank=False)
  end_time=models.TimeField(null=True, blank=False)
  working_time=models.DecimalField(null=True, max_digits=4, decimal_places=1)
  break_time=models.DecimalField(null=True, max_digits=4, decimal_places=1)

  def __str__(self):
    return f"{self.ts} {self.day}" 

class TimeSheetProjectLine(models.Model):
  ts=models.ForeignKey(TimeSheet, on_delete=models.PROTECT, verbose_name="Time Sheet", null=False, blank=False)
  day=models.IntegerField(null=False)
  project=models.ForeignKey(Project, on_delete=models.PROTECT, verbose_name="Project", null=False, blank=False)
  working_time=models.DecimalField(null=True, max_digits=4, decimal_places=1)
  def __str__(self):
    return f"{self.ts} {self.day} {self.project}" 

class TimeSheetSetup(models.Model):
  holiday_setup = models.ForeignKey(AbsenceType, on_delete=models.PROTECT, verbose_name="Holiday setup", related_name="holiday_setups", null=True)
  study_setup = models.ForeignKey(AbsenceType, on_delete=models.PROTECT, verbose_name="Study setup", related_name="study_setups", null=True)
  illness_setup = models.ForeignKey(AbsenceType, on_delete=models.PROTECT, verbose_name="Illness setup", related_name="illness_setups", null=True)

class AbsenceEvent(models.Model):
  """ We have a blank calendar, so we put all the events into this table:
  - absence of an employee or an employee group (EmployeeAbsenceGroup)
  - holidays
  - when employee wants to work on holidays or weekends
  Then we sum up everything and display a month with all the info about the day
  """
  class Meta:
    permissions = [
      ("change_own", "Can change only own events"),
      ("change_all", "Can change all events"),
     ]
  DAY_TYPES = {
    "full": "1",
    "half": "1/2",
    "quarter": "1/4"
  }
  EVENT_TYPES = {
    "holiday": "Holiday",
    "employee_event": "Employee",
    "employee_group_event": "Employee group"
  }
  start_date = models.DateField(verbose_name="Start date")
  end_date = models.DateField(verbose_name="End date")
  employee_link = models.ForeignKey(User, on_delete=models.PROTECT, related_name='user_link', verbose_name="User", null=True)
  absence_type = models.ForeignKey(AbsenceType, on_delete=models.PROTECT, related_name='absence_type_event', verbose_name="Absence type", null=True)
  # to be able to add absence by the group and not by employee
  employee_absence_group_link = models.ForeignKey(EmployeeAbsenceGroup, on_delete=models.PROTECT, related_name='EAG_date', verbose_name="Employee absence group", null=True)
  event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default="employee_event", verbose_name="Type of event")
  day_type = models.CharField(max_length=20, choices=DAY_TYPES, default="full", verbose_name="Type of the day")
  comment = models.CharField(max_length=220, verbose_name="Comment", blank=True)
  created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='user_created', verbose_name="Created by")
  created = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

  def __str__(self):
    absence_name = ""
    match self.event_type:
      case "employee_event":
        absence_name += str(self.employee_link) + " " + str(self.absence_type)
      case "employee_group_event":
        absence_name += str(self.employee_absence_group_link) + " Gruppe" + " " + str(self.absence_type)
      case "holiday":
        absence_name += "Holiday"
    absence_name += " " + str(self.start_date) + "-" + str(self.end_date)
    return absence_name

