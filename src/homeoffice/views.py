from django.shortcuts import render, redirect, get_object_or_404, reverse
from collections import defaultdict
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
import logging
import calendar
import datetime
from django.contrib.auth.models import User
from .models import Employee, EmployeeGroup, EmployeeAbsenceGroup, AbsenceEvent, AbsenceType, WorkTimeSetup, DefaultWorkTime, TimeSheet, TimeSheetLine, TimeSheetProjectLine, TimeSheetSetup, Project, Place, Task, Vehicle, MontageSetup, Service
from .forms import FilterTimeForm, AddEventForm, AddGroupEventForm, AddHolidayForm, AddEventEmployeeForm, AddWorkingTimeForm, AddTSLinesForm, AddTSProjectLinesForm, ServiceForm, AddTaskForm
from django.db.models import F, Q
from itertools import chain
from django.views import View
from django.contrib import messages
# import locale


# locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')

# Create your views here.
def index(request):
  if request.user.is_authenticated:
    return redirect('calendar')
  return render(request, "homeoffice/index.html")

decorators = []
logging.basicConfig(filename='mylog.log', level=logging.DEBUG)

class EventCalendar:
  def __init__(self, year, month):
    mycal = calendar.Calendar()
    self.weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    self.monthdays = [ day for day in mycal.itermonthdays(year, month) if day > 0 ]
    self.month_table = calendar.monthcalendar(year, month)
    self.monthweekday = [ self.weekdays[calendar.weekday(year, month, i)] for i in self.monthdays ]
    self.holidays = self.holidays_weekends(year, month, self.monthdays, self.monthweekday)
    today = datetime.date.today()
    if year == today.year and month == today.month:
      self.today_day = today.day
    else:
      self.today_day = 0

  def holidays_weekends(self, year, month, monthdays, monthweekday):
    # fill in the holidays 
    holiday_events = AbsenceEvent.objects.filter(
      ( 
        Q(start_date__year=year, start_date__month=month) |
        Q(end_date__year=year, end_date__month=month)
      ),
      event_type="holiday"
      )
    holidays_list = [
      {
        'text': 'FT',
        'comment': holiday_item.comment,
        'day_type': holiday_item.day_type,
        'link': reverse('event_view', args=[holiday_item.id]),
        'color': '#808b96',
        'day': day
      }
      for day in monthdays
      for holiday_item in holiday_events.filter(
        start_date__lte=datetime.date(year, month, day),
        end_date__gte=datetime.date(year, month, day))
    ]

    # fill in the weekends list
    weekends_list = [
      {
        'color': "#e0e0e0", 
        'day': day +1 
      }
      for day, weekday in enumerate(monthweekday) if weekday in ("Sa", "So")
    ]

    return {
      'holidays_list': holidays_list,
      'weekends_list': weekends_list
    }

@method_decorator(login_required, name="dispatch")
class CalendarView(View):
  template_name = "homeoffice/calendar.html"

  def get(self, request):
    context = self.initcontext()
    return render(request, self.template_name, context)

  def post(self, request):
    form = FilterTimeForm(request.POST)
    if form.is_valid():
      current_year = int(form.cleaned_data["year_switch"])
      current_month = int(form.cleaned_data["month_switch"])
    context = self.initcontext(current_year, current_month)
    return render(request, self.template_name, context)

  def initcontext(self, year=None, month=None):
    today = datetime.date.today()
    current_year = year or today.year
    current_month = month or today.month
    cal = EventCalendar(current_year, current_month)
    form = FilterTimeForm(initial={'year_switch': current_year, 'month_switch': current_month})
    calendar_array = self.make_calendar(current_year, current_month, cal.monthdays, cal.holidays)
    
    context = {
      'monthdays': cal.monthdays,
      'monthweekday': cal.monthweekday,
      'holidays': cal.holidays['holidays_list'],
      'weekends': cal.holidays['weekends_list'],
      'eag': calendar_array['eag'],
      'eag_events': calendar_array['eag_events'],
      'employees': calendar_array['employees'],
      'employee_groups': calendar_array['employee_groups'],
      'employee_events': calendar_array['employee_events'],
      'e_colors': calendar_array['e_colors'],
      'eag_colors': calendar_array['eag_colors'],
      'month': current_month,
      'year': current_year,
      'form': form,
      'today_day': cal.today_day
    }
    return context

  def make_calendar(self, year, month, monthdays, holidays):
    employees = Employee.objects.all().annotate(
      last_name=F('user_link__last_name'),
      first_name=F('user_link__first_name'),
      employee_absence_group=F('employee_absence_group_link__name'),
      employee_group=F('employee_group_link__name')).order_by('employee_group_link__name', 'last_name')
    employee_groups = EmployeeGroup.objects.all()
    employee_absence_groups = EmployeeAbsenceGroup.objects.all()

    # events relevant for employee + create a list of employee names
    employee_events_list = []
    employee_events_list = self.events_list(year, month, monthdays, True)
    employee_names_list = [[ f"{e.last_name} {e.first_name}" + (f" ({e.employee_absence_group_link.name})" if e.employee_absence_group_link else ""), e.employee_absence_group, e.employee_group, e.user_link.id ]
      for e in employees
    ]
    
    # events relevant for employee absence groups 
    eag_list = []
    eag_list = self.events_list(year, month, monthdays, False)

    # now we need to add group events for relevant employees, appending "(G)" to the event name
    employee_group_events_list = [
      {
        'employee': e.user_link.id,
        'text': event['text'] + "(G)",
        'comment': event['comment'],
        'day_type': event['day_type'],
        'link': event['link'],
        'color': event['color'],
        'day': event['day'],
        'group_event': True
      }
      for e in employees
      if e.employee_absence_group_link
      for event in eag_list
      if event['employee_group'] == e.employee_absence_group_link.id
    ]
    employee_events_list += employee_group_events_list 

    e_colors = [
      {
        'e_id': e.user_link.id,
        'day': day,
        'color': self.select_e_color(employee_events_list, e.user_link.id, day, holidays)
      }
      for e in employees
      for day in monthdays 
    ]

    eag_colors = [
      {
        'eag': eag.id,
        'day': day,
        'color': self.select_eag_color(eag_list, eag.id, day, holidays)
      }
      for eag in employee_absence_groups
      for day in monthdays
    ]

    return {
      'employees': employee_names_list,
      'eag': employee_absence_groups,
      'employee_groups': employee_groups,
      'eag_events': eag_list,
      'employee_events': employee_events_list,
      'e_colors': e_colors,
      'eag_colors': eag_colors
      }

  def select_e_color(self, events, e, day, holidays):
    # actually we can do that before we call this function
    filtered_e_events = list(filter(lambda item: item['employee'] == e and item['day'] == day and item['group_event'] == False, events)) or False
    filtered_eag_events = list(filter(lambda item: item['employee'] == e and item['day'] == day and item['group_event'] == True, events)) or False
    filtered_holidays = list(filter(lambda item: item['day'] == day, holidays['holidays_list'])) or False
    filtered_weekends = list(filter(lambda item: item['day'] == day, holidays['weekends_list'])) or False

    # we return the last color, that's it -- and it works with 1 element in the list
    if filtered_e_events: 
      # logging.debug('personal event color=%s', filtered_e_events[-1]['color']) 
      return filtered_e_events[-1]['color']
    elif filtered_eag_events:
      # logging.debug('group event color=%s', filtered_eag_events[-1]['color'])
      return filtered_eag_events[-1]['color']
    elif filtered_holidays:
      return filtered_holidays[-1]['color']
    elif filtered_weekends:
      return filtered_weekends[-1]['color']
    else:
      return "white"

  def select_eag_color(self, events, eag, day, holidays):
    filtered_eag_events = list(filter(lambda item: item['employee_group'] == eag and item['day'] == day, events)) or False
    filtered_holidays = list(filter(lambda item: item['day'] == day, holidays['holidays_list'])) or False
    filtered_weekends = list(filter(lambda item: item['day'] == day, holidays['weekends_list'])) or False

    if filtered_eag_events:
      return filtered_eag_events[-1]['color']
    elif filtered_holidays:
      return filtered_holidays[-1]['color']
    elif filtered_weekends:
      return filtered_weekends[-1]['color']
    else:
      return "white"

  def events_list(self, year, month, monthdays, employee):
    # for employee we create a list of employee events and employee group events
    if employee:
      employee_events = AbsenceEvent.objects.filter(
        Q(event_type="employee_event"),
        ( 
          Q(start_date__year=year, start_date__month=month) |
          Q(end_date__year=year, end_date__month=month)
        )
      ).annotate(
        color=F('absence_type__color'),
        e_absence=F('absence_type__name'))
      employee_events_list = [
        {
          'employee': event.employee_link.id,
          'text': event.e_absence,
          'comment': event.comment,
          'day_type': event.day_type,
          'link': reverse('event_view', args=[event.id]),
          'color': event.color,
          'day': day,
          'group_event': False
        }
        for day in monthdays
        for event in employee_events.filter(
          start_date__lte=datetime.date(year, month, day),
          end_date__gte=datetime.date(year, month, day)
        )
      ]
      return employee_events_list

      # for employee group we create a list of employee group events only
    else:
      absence_group_events = AbsenceEvent.objects.filter(
        ( 
          Q(start_date__year=year, start_date__month=month) |
          Q(end_date__year=year, end_date__month=month)
        ),
        event_type="employee_group_event"
      ).annotate(
        color=F('absence_type__color'),
        e_absence=F('absence_type__name'))

      employee_group_events_list= [
        {
          'employee_group': event.employee_absence_group_link.id,
          'text': event.e_absence,
          'comment': event.comment,
          'day_type': event.day_type,
          'link': reverse('event_view', args=[event.id]),
          'color': event.color,
          'day': day,
          'group_event': True
        }
        for day in monthdays
        for event in absence_group_events.filter(
          start_date__lte=datetime.date(year, month, day),
          end_date__gte=datetime.date(year, month, day)
        )
      ]
      return employee_group_events_list

@method_decorator(login_required, name="dispatch")
class MyCalendarView(View):
  template_name = "homeoffice/mycal.html"

  def get(self, request):
    context = self.initcontext()
    return render(request, self.template_name, context)

  def post(self, request):
    form = FilterTimeForm(request.POST)
    if form.is_valid():
      current_year = int(form.cleaned_data["year_switch"])
      current_month = int(form.cleaned_data["month_switch"])
    context = self.initcontext(current_year, current_month)
    return render(request, self.template_name, context)

  def initcontext(self, year=None, month=None):
    # potentilly we could create a class for the next 5 variables + some more like today_month, today_day
    absence_arr = list_absence_types()
    employee = Employee.objects.get(pk=self.request.user)
    empl_fullname = employee.user_link.first_name + " " + employee.user_link.last_name
    today = datetime.date.today()
    current_year = year or today.year
    current_month = month or today.month
    cal = EventCalendar(current_year, current_month)
    cal_array = make_calendar(self, current_year, current_month, employee, cal.monthdays, cal.holidays, True)
    form = FilterTimeForm(initial={'year_switch': current_year, 'month_switch': current_month})
    if employee.employee_absence_group_link == None:
      agl = 'None'
    else:
      agl = employee.employee_absence_group_link.name
    context = {
      'monthdays': cal.monthdays,
      'month_table': cal.month_table,
      'weekdays': cal.weekdays,
      'employee_events': cal_array['employee_events_list'],
      'e_colors': cal_array['e_colors'],
      'e_full_name': empl_fullname,
      'e_abs_group': agl,
      'e_group': employee.employee_group_link.name,
      'month': current_month,
      'year': current_year,
      'form': form,
      'today_day': cal.today_day,
      'absence_types': absence_arr
    }
    return context

# withcolors - True for mycalendar, return colors array, False for TimeSheet
def make_calendar(self, year, month, e, monthdays, holidays, withcolors):
  employee_events = AbsenceEvent.objects.filter(
    Q(event_type="employee_event"),
    ( 
      Q(start_date__year=year, start_date__month=month) |
      Q(end_date__year=year, end_date__month=month)
    ),
    employee_link=e.user_link # that's why we don't call events_list() function
  ).annotate(
    color=F('absence_type__color'),
    e_absence=F('absence_type__name'))
  employee_events_list = [
    {
      'text': event.e_absence,
      'comment': event.comment,
      'day_type': event.day_type,
      'link': reverse('event_view', args=[event.id]),
      'color': event.color,
      'day': day,
      'group_event': False
    }
    for day in monthdays
    for event in employee_events.filter(
      start_date__lte=datetime.date(year, month, day),
      end_date__gte=datetime.date(year, month, day)
    )
  ]

  if withcolors:
    show_group_events = "(G)"
  else:
    show_group_events = ""

  # now we add relevant absence group events
  # but that makes sence only if employee is in absence group
  if e.employee_absence_group_link:
    absence_group_events = AbsenceEvent.objects.filter(
      ( 
        Q(start_date__year=year, start_date__month=month) |
        Q(end_date__year=year, end_date__month=month)
      ),
      event_type="employee_group_event",
      employee_absence_group_link=e.employee_absence_group_link
    ).annotate(
      color=F('absence_type__color'),
      e_absence=F('absence_type__name'))

    absence_group_events_list= [
      {
        'text': event.e_absence,
        'comment': event.comment,
        'day_type': event.day_type,
        'link': reverse('event_view', args=[event.id]),
        'color': event.color,
        'day': day,
        'group_event': True
      }
      for day in monthdays
      for event in absence_group_events.filter(
        start_date__lte=datetime.date(year, month, day),
        end_date__gte=datetime.date(year, month, day)
      )
    ]

    employee_group_events = [
      {
        'text': event['text'] + show_group_events,
        'comment': event['comment'],
        'day_type': event['day_type'],
        'link': event['link'],
        'color': event['color'],
        'day': event['day'],
        'group_event': True
      }
      for event in absence_group_events_list
    ]
    employee_events_list += employee_group_events

  if withcolors:  
    e_colors = [
      {
        'day': day,
        'color': select_e_color(self, employee_events_list, day, holidays)
      }
      for day in monthdays 
    ]
    
    holiday_events_list = [
      {
        'text': event['text'],
        'comment': event['comment'],
        'day_type': event['day_type'],
        'link': event['link'],
        'color': event['color'],
        'day': event['day'],
        'group_event': True
      }
      for event in holidays['holidays_list']
    ]
    employee_events_list += holiday_events_list

  else:
    e_colors = [
      {
        'day': day,
        'color': select_report_color(self, day, holidays)
      }
      for day in monthdays 
    ]
  return {
    'employee_events_list': employee_events_list,
    'e_colors': e_colors
  }

def select_e_color(self, events, day, holidays):
  # actually we can do that before we call this function
  filtered_e_events = list(filter(lambda item: item['day'] == day and item['group_event'] == False, events)) or False
  filtered_eag_events = list(filter(lambda item: item['day'] == day and item['group_event'] == True, events)) or False
  filtered_holidays = list(filter(lambda item: item['day'] == day, holidays['holidays_list'])) or False
  filtered_weekends = list(filter(lambda item: item['day'] == day, holidays['weekends_list'])) or False

  # we return the last color, that's it -- and it works with 1 element in the list
  if filtered_e_events:
    return filtered_e_events[-1]['color']
  elif filtered_eag_events:
    return filtered_eag_events[-1]['color']
  elif filtered_holidays:
    return filtered_holidays[-1]['color']
  elif filtered_weekends:
    return filtered_weekends[-1]['color']
  else:
    return "white"

def select_report_color(self, day, holidays):
  # actually we can do that before we call this function
  filtered_holidays = list(filter(lambda item: item['day'] == day, holidays['holidays_list'])) or False
  filtered_weekends = list(filter(lambda item: item['day'] == day, holidays['weekends_list'])) or False

  # we return the last color, that's it -- and it works with 1 element in the list
  if filtered_holidays:
    return "#f9e79f"
  elif filtered_weekends:
    return filtered_weekends[-1]['color']
  else:
    return "white"

@login_required(login_url='index')
def detailed_event_view(request, id):
  event = get_object_or_404(AbsenceEvent, id=id)
  context = { 
    'event': event,
    'created_by': event.created_by.first_name + " " + event.created_by.last_name,
    'created': event.created,
    'id': id,
    'user': request.user.id,
    'employee': event.employee_link.user_link
  }

  match event.event_type:
    case "employee_group_event":
      context['eag'] = event.employee_absence_group_link
      context['employee'] = False
      context['absence_type'] = event.absence_type.name
      context['absence_descr'] = event.absence_type.description
    case "employee_event":
      context['eag'] = False
      context['employee'] = event.employee_link.first_name + " " + event.employee_link.last_name
      context['absence_type'] = event.absence_type.name
      context['absence_descr'] = event.absence_type.description
    case "holiday":
      context['employee'] = False
      context['eag'] = False
      context['absence_type'] = False
      context['absence_descr'] = False

  return render(request, "homeoffice/event_view.html", context)

@login_required(login_url='index')
def event_delete_view(request, id):
  event = get_object_or_404(AbsenceEvent, id=id)
  event.delete()
  messages.success(request, "Die Abwesenheit wurde gelöscht")
  return redirect('calendar')

@method_decorator(login_required, name="dispatch")
class DetailedEditView(View):
  def get(self, request, id):
    event = get_object_or_404(AbsenceEvent, id=id)
    page_type = self.choose_form(event.event_type)
    pagename = page_type['pagename']
    form = page_type['form_type'](instance=event)
    absence_arr = list_absence_types()
    context = {'form': form, 'pagename': pagename, 'add': False, 'absence_types': absence_arr, 'id': id}
    return render(request, "homeoffice/add_event.html", context)

  def post(self, request, id):
    event = get_object_or_404(AbsenceEvent, id=id)
    page_type = self.choose_form(event.event_type)
    form = page_type['form_type'](request.POST, instance=event)
    # logging.debug('form=%s', form)
    if form.is_valid():
      form.save()
      messages.success(request, "Die Abwesenheit wurde geändert")
    return redirect('calendar')

  def choose_form(self, event_type):
    match event_type:
      case "holiday":
        pagename = "Veranstaltungsbearbeitung -- Feiertag"
        form_type = AddHolidayForm
      case "employee_event":
        pagename = "Veranstaltungsbearbeitung -- Abwesenheit des Mitarbeiters"
        form_type = AddEventForm
      case "employee_group_event":
        pagename = "Veranstaltungsbearbeitung -- Abwesenheit des Mitarbeitergruppe"
        form_type = AddGroupEventForm
    return { 'pagename': pagename, 'form_type': form_type }

@method_decorator(login_required, name="dispatch")
class AddEventView(View):
  def get(self, request, event_type):
    context_array = self.initcontext(event_type)
    context = {'form': context_array['form'], 'pagename': context_array['pagename'], 'add': True, 'id': False, 'absence_types': context_array['absence_types'], 'event_type': event_type}
    return render(request, "homeoffice/add_event.html", context)

  def post(self, request, event_type):
    context_array = self.initcontext(event_type)
    save_result = False
    # in this case employee is chosen in the form field
    if event_type == 'other_employee_event':
      event_type = 'employee_event'
      save_result = self.save_form(context_array['form'], False, event_type)
    else:
      save_result = self.save_form(context_array['form'], True, event_type)
    if save_result:
      messages.success(request, "Die Abwesenheit wurde hinzugefügt")
      return redirect('calendar')
    else:
      messages.error(request, "Die Abwesenheit wurde nicht hinzugefügt")
      context = {'form': context_array['form'], 'pagename': context_array['pagename'], 'add': True, 'id': False, 'absence_types': context_array['absence_types'], 'event_type': event_type}
      return render(request, "homeoffice/add_event.html", context)

  def initcontext(self, event_type):
    match event_type:
      case "holiday":
        pagename = "Feiertag"
        form_type = AddHolidayForm
        absence_types = ""
      case "employee_event":
        pagename = "Abwesenheitsereignis"
        form_type = AddEventForm
        absence_types = list_absence_types()
      case "employee_group_event":
        pagename = "Gruppenveranstaltung"
        form_type = AddGroupEventForm
        absence_types = list_absence_types()
      case "other_employee_event":
        pagename = "Veranstaltung für einen anderen Mitarbeiter"
        form_type = AddEventEmployeeForm
        absence_types = list_absence_types()
    
    if self.request.method == 'POST':
      args = { 'data': self.request.POST }
    else:
      args = {}
    form = form_type(**args)
    return { 'pagename': pagename, 'form': form, 'absence_types': absence_types }

  def save_form(self, form, employee, event_type):
    if form.is_valid():
      #logging.debug('form=%s', form)
      f = form.save(commit=False)
      f.created_by = self.request.user
      # if holiday or group event, we don't use this
      if employee:
        f.employee_link = self.request.user
      f.event_type = event_type
      f.save()
      # logging.debug('called f.save(), result=%s', f.employee_link)
      return True
    else:
      return False

def list_absence_types():
    absence_types = AbsenceType.objects.all().order_by('working_time')
    absence_arr = [ [i.name, i.description, i.color, i.working_time] for i in absence_types ]
    absence_arr.append(['FT', 'Feiertag', '#808b96', False])
    return absence_arr

@method_decorator(login_required, name="dispatch")
class TimeSheetView(View):
  template_name = "homeoffice/timesheet.html"

  def get(self, request):
    context = self.initcontext()
    return render(request, self.template_name, context)

  def post(self, request):
    form = FilterTimeForm(request.POST)
    if form.is_valid():
      current_year = int(form.cleaned_data["year_switch"])
      current_month = int(form.cleaned_data["month_switch"])
    context = self.initcontext(current_year, current_month)
    return render(request, self.template_name, context)

  def initcontext(self, year=None, month=None):
    absence_arr = list_absence_types()
    today = datetime.date.today()
    current_year = year or today.year
    current_month = month or today.month
    employee = Employee.objects.get(pk=self.request.user)
    cal = EventCalendar(current_year, current_month)
    time_sheet_setup = TimeSheetSetup.objects.first()
    empl_fullname = employee.user_link.first_name + " " + employee.user_link.last_name
    hours_map_dict = {
      'half': 4,
      'quarter': 2,
      'full': 8
    }

    time_sheet_row = []
    working_time_cache = DefaultWorkTime.objects.filter(employee=employee.user_link)
    cal_array = make_calendar(self, current_year, current_month, employee, cal.monthdays, cal.holidays, False)
    # holidays
    for day in cal_array['e_colors']:
      append = True
      for holiday in cal.holidays['holidays_list']:
        if day['day'] == holiday['day']:
          holiday_cell = {
            'hours': hours_map_dict[holiday['day_type']],
            'color': day['color']
          }
          time_sheet_row.append(holiday_cell)
          append = False
      if append:
          holiday_cell = {
            'hours': 0,
            'color': day['color']
          }
          time_sheet_row.append(holiday_cell)
    holidays_row = ['Feiertage (FT)', True, time_sheet_row]

    # check if a time-sheet exists, if not, create one, if we have default data
    nwt_perday = self.calc_working_time(current_year, current_month, cal.monthdays, cal.monthweekday, employee, working_time_cache, hours_map_dict)
    time_sheet = TimeSheet.objects.filter(employee=employee.user_link, year=current_year, month=current_month).first()
    ts_lines = []
    has_projects = False
    if not time_sheet and working_time_cache: 
      time_sheet = TimeSheet.objects.create(
      employee=employee.user_link,
      year=current_year,
      month=current_month,
      status='created'
      )
      ts_lines = []
      for i in cal.monthdays:
        for default_day in working_time_cache:
          if cal.monthweekday[i-1] == default_day.weekday:
            if nwt_perday[i-1] != 0:
              TimeSheetLine.objects.create(
              ts=time_sheet,
              day=i,
              start_time=getattr(default_day, 'start_time'),
              end_time=getattr(default_day, 'end_time'),
              working_time=nwt_perday[i-1],
              break_time=getattr(default_day, 'break_time')
              ) 
            else:
              TimeSheetLine.objects.create(
              ts=time_sheet,
              day=i,
              start_time=datetime.time(0,0),
              end_time=datetime.time(0,0),
              working_time=nwt_perday[i-1],
              break_time=0
              ) 
    elif time_sheet:
      ts_lines = TimeSheetLine.objects.filter(ts=time_sheet)
      ts_project_lines=TimeSheetProjectLine.objects.filter(ts=time_sheet)
      if ts_project_lines:
        projects = Project.objects.filter(timesheetprojectline__in=ts_project_lines).values_list('number', flat=True).distinct()
        has_projects = True
      else:
        has_projects = False
    # else working_time_cache is not defined, nothing to display

    # create list for absence events to display
    new_absence_list = []
    for i in absence_arr: # types of events
      if i[0] in [str(time_sheet_setup.holiday_setup), str(time_sheet_setup.study_setup), str(time_sheet_setup.illness_setup)]:
    # if type of event and a day match, we add an event to a row, but the colors are for weekends and holidays only
    # otherwise we add a day with a default color
        time_sheet_row = []
        for day in cal_array['e_colors']: # color for each day of month
          append = True
          for event in cal_array['employee_events_list']: # events for particular days
            if event['day'] == day['day'] and event['text'] == i[0]:
              cell = {
                'hours': hours_map_dict[event['day_type']],
                'color': day['color']
              }
              time_sheet_row.append(cell)
              append = False
          if append:
              holiday_cell = {
                'hours': 0,
                'color': day['color']
              }
              time_sheet_row.append(holiday_cell)
        new_absence_list.append([i[1] + " (" + i[0] + ")", not i[3], time_sheet_row])

    # for TS lines we have a value for each day
    # but for project TS lines we have values only for particular days
    if has_projects:
      project_time_line = []
      project_header = []
      # append the header 'Projects', an empty line
      for day in cal_array['e_colors']:
        cell = {
          'hours': 0,
          'color': day['color']
        }
        project_time_line.append(cell)
      project_header.append(['Projekts', True, project_time_line])

      # append the data for each project
      project_time = []
      for i in projects:
        project_time_line = []
        for day in cal_array['e_colors']:
          # first we create an empty array to add values later
          cell = {
            'hours': 0,
            'color': day['color']
          }
          project_time_line.append(cell)
        for j in ts_project_lines:
          if str(j.project) == i:
            project_time_line[j.day-1]['hours'] = j.working_time
        
        project_time.append([i, False, project_time_line])

    # create list for work data to display
    worktime_actual_tmp = [['Werkstatt allgemein', False, 'working_time'],['Verwaltung / Büro', False, 'working_time'],  ['Arbeitzeit (1)', True, 'working_time'], ['Arbeitzeit (2)', True, 'working_time'], ['Anfang', False, 'start_time'], ['Ende', False, 'end_time'], ['Pause, Min', False, 'break_time']]
    new_wt_list = []
    project_wt_list = []
    hours1_row = []
    if working_time_cache: # if the cache exists, it exists for all the days
      for i in worktime_actual_tmp:
        time_sheet_row = []
        for day in cal_array['e_colors']:
          for j, default_day in enumerate(ts_lines):
            if j+1 == day['day']:
              # write '' if start_time = end_time, just for a clear overview
              if (i[2] == 'start_time' or i[2] == 'end_time') and getattr(default_day, 'start_time') == getattr(default_day, 'end_time'):
                cell = {
                  'hours': 0,
                  'color': day['color']
                }
              else:
                if i[0] == 'Werkstatt allgemein' or i[0] == 'Verwaltung / Büro':
                  if (employee.default_time_category_is_office == True and i[0] == 'Werkstatt allgemein') or (employee.default_time_category_is_office == False and i[0] == 'Verwaltung / Büro'):
                    cell = {
                      'hours': getattr(default_day, i[2]),
                      'color': day['color']
                    }
                  else:
                    cell = {
                      'hours': 0,
                      'color': day['color']
                    }
                elif i[0] == 'Arbeitzeit (1)':
                  hours1 = getattr(default_day, i[2])
                  if has_projects:
                    for k in project_time:
                      hours1 += k[2][day['day']-1]['hours']
                  cell = {
                    'hours': hours1,
                    'color': day['color']
                  }
                  hours1_row.append(hours1)
                elif i[0] == 'Arbeitzeit (2)':
                  hours2 = self.calc_work_time2(getattr(default_day, 'start_time'), getattr(default_day, 'end_time'), getattr(default_day, 'break_time'))

                  if hours2 != hours1_row[day['day']-1]:
                    color = '#f5b7b1'
                  else:
                    color = day['color']

                  cell = {
                    'hours': hours2,
                    'color': color
                  }
                else:
                  cell = {
                    'hours': getattr(default_day, i[2]),
                    'color': day['color']
                  }
              time_sheet_row.append(cell)
        new_wt_list.append([i[0], i[1], time_sheet_row])
    if has_projects:
      first_column = [holidays_row] + new_absence_list + project_header + project_time + new_wt_list
    else:
      first_column = [holidays_row] + new_absence_list + new_wt_list
    
    form = FilterTimeForm(initial={'year_switch': current_year, 'month_switch': current_month})
    # we call the make_calendar function with False, because we don't need a color array
    # logging.debug('nwt_perday=%s', nwt_perday)
    if employee.employee_absence_group_link == None:
      agl = 'None'
    else:
      agl = employee.employee_absence_group_link.name
    context = {
      'monthdays': cal.monthdays,
      'monthweekday': cal.monthweekday,
      'e_full_name': empl_fullname,
      'e_abs_group': agl,
      'e_group': employee.employee_group_link.name,
      'month': current_month,
      'year': current_year,
      'form': form,
      'today_day': cal.today_day,
      'first_column': first_column,
      'timesheet': time_sheet.id
    }
    return context

  def calc_work_time2(self, start_time, end_time, pause):
    '''Calculate time out of start_time, end_time and pause -- it can be different from stored time, then we highlight the differences'''
    total_minutes = (end_time.hour - start_time.hour) * 60 + (end_time.minute - start_time.minute)
    working_hours = round((total_minutes - pause) / 60, 1)

    return working_hours

  def calc_working_time(self, year, month, monthdays, monthweekday, e, working_time_cache, hours_map_dict):
    '''Calculate suggested working time based on absence events and default working time'''
    working_time = [
      getattr(default_day, 'working_time') 
      for i in monthdays 
      for default_day in working_time_cache 
      if monthweekday[i-1] == default_day.weekday
    ]

    employee_events = AbsenceEvent.objects.filter(
      Q(event_type="employee_event"),
      ( 
        Q(start_date__year=year, start_date__month=month) |
        Q(end_date__year=year, end_date__month=month)
      ),
      employee_link=e.user_link # that's why we don't call events_list() function
    ).annotate(
      working_time=F('absence_type__working_time')
    ).filter(working_time=False)

    nwt_employee = [ 
    min(8, sum(hours_map_dict[event.day_type] for event in employee_events.filter(
        start_date__lte=datetime.date(year, month, day),
        end_date__gte=datetime.date(year, month, day)
    )))
    for day in monthdays
    ]

    if e.employee_absence_group_link:
      absence_group_events = AbsenceEvent.objects.filter(
        ( 
          Q(start_date__year=year, start_date__month=month) |
          Q(end_date__year=year, end_date__month=month)
        ),
        event_type="employee_group_event",
        employee_absence_group_link=e.employee_absence_group_link
      ).annotate(
        working_time=F('absence_type__working_time')
      ).filter(working_time=False)

      nwt_group = [ 
      min(8, sum(hours_map_dict[event.day_type] for event in absence_group_events.filter(
          start_date__lte=datetime.date(year, month, day),
          end_date__gte=datetime.date(year, month, day)
      )))
      for day in monthdays
      ]
    else:
      nwt_group = []

    holiday_events = AbsenceEvent.objects.filter(
      (
        Q(start_date__year=year, start_date__month=month) |
        Q(end_date__year=year, end_date__month=month)
      ),
      event_type="holiday"
      )

    nwt_holidays = [
    min(8, sum(hours_map_dict[event.day_type] for event in holiday_events.filter(
        start_date__lte=datetime.date(year, month, day),
        end_date__gte=datetime.date(year, month, day)
    )))
    for day in monthdays
    ]

    weekends_list = [8 if weekday in ("Sa", "So") else 0 for weekday in monthweekday]
    nwt_perday = []
    for i in range(len(nwt_employee)):
      if nwt_employee[i] >= 8 or nwt_group[i] >= 8 or nwt_holidays[i] >= 8 or weekends_list[i] >= 8:
        nwt_perday.append(0)
      else:
        nwt_perday.append(max(0, working_time[i] - (nwt_employee[i] + nwt_group[i] + nwt_holidays[i] + weekends_list[i])))

    return nwt_perday

@method_decorator(login_required, name="dispatch")
class DefaultTimeView(View):
  template_name = "homeoffice/default_time.html"

  def get(self, request):
    context = self.initcontext()
    return render(request, self.template_name, context)

  def post(self, request):
    form = AddWorkingTimeForm(request.POST)
    form_saved = False
    if form.is_valid():
      f = form.save(commit=False)
      f.employee = self.request.user
      form_saved = f.save()
    if form_saved:
      messages.success(request, "Die Arbeitzeit wurde hinzugefügt")
    else:
      messages.error(request, "Die Arbeitzeit wurde nicht hinzugefügt")
    context = self.initcontext()
    return render(request, self.template_name, context)

  def initcontext(self):
    employee = Employee.objects.get(pk=self.request.user)
    empl_fullname = employee.user_link.first_name + " " + employee.user_link.last_name
    if employee.employee_absence_group_link == None:
      agl = 'None'
    else:
      agl = employee.employee_absence_group_link.name
    form = AddWorkingTimeForm()
    working_time = WorkTimeSetup.objects.filter(employee=employee.user_link).order_by('start_time') or False
    weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    working_time_week = 0
    day_dict_arr = []
    for i, day in enumerate(weekdays):
      working_time_perday = 0
      pause_per_day = 0
      last_end_time = False
      times_for_tpl = []
      times = False
      # fix this!!
      add_day = True
      if working_time: 
        work_time_data = working_time.filter(weekday=str(i+1))
        if work_time_data:
          min_time = work_time_data[0].start_time
          max_time = work_time_data[0].end_time
          # logging.debug('working time data=%s', work_time_data)
          for times in work_time_data:
            working_time_perday += round(((times.end_time.hour * 60 + times.end_time.minute) - \
                         (times.start_time.hour * 60 + times.start_time.minute))/60, 1)
            if last_end_time and last_end_time < times.start_time:
              pause_per_day += round((times.start_time.hour * 60 + times.start_time.minute) - \
                (last_end_time.hour * 60 + last_end_time.minute), 0)
            last_end_time = times.end_time
            if times.start_time < min_time:
              min_time = times.start_time
            if times.end_time > max_time:
              max_time = times.end_time

            # here we create a dictionary to output into template
            link = reverse('default_time_delete', args=[times.id])
            times_for_tpl.append([times.start_time, times.end_time, link])
          working_time_week += working_time_perday
          day_dict_arr.append({
            'day': day,
            'start_time': min_time,
            'end_time': max_time,
            'times_for_tpl': times_for_tpl,
            'pause': pause_per_day,
            'working_time': working_time_perday
          })
          add_day = False
          # logging.debug('dict inside if=%s', day_dict_arr)
        #if not working_time or not work_time_data:
      if add_day:
        day_dict_arr.append({
        'day': day,
        'period': times,
        'start_time': datetime.time(0,0),
        'end_time': datetime.time(0,0),
        'times_for_tpl': [],
        'pause': 0,
        'working_time': 0,
        })

    self.save_default_work_time(employee.user_link, day_dict_arr)

    context = {
      'e_full_name': empl_fullname,
      'e_abs_group': agl,
      'e_group': employee.employee_group_link.name,
      'day_dict_arr': day_dict_arr,
      'form': form,
      'working_time_week': working_time_week
    }
    return context

  def save_default_work_time(self, employee, day_dict_arr):
    for i in day_dict_arr:
      try:
        defaults = DefaultWorkTime.objects.get(
        employee=employee,
        weekday=i['day']
        )
        if defaults.start_time != i['start_time']:
          defaults.start_time = i['start_time']
        if defaults.end_time != i['end_time']:
          defaults.end_time = i['end_time']
        if defaults.working_time != i['working_time']:
          defaults.working_time = i['working_time']
        if defaults.break_time != i['pause']:
          defaults.break_time = i['pause']
        defaults.save()
      except DefaultWorkTime.DoesNotExist:
         DefaultWorkTime.objects.create(
           employee = employee,
           weekday = day,
           start_time = start_times[i],
           end_time = end_times[i],
           working_time = working_hours[i],
           break_time = breaks[i]
           )

@login_required(login_url='index')
def default_time_delete(request, id):
  time_entry = get_object_or_404(WorkTimeSetup, id=id)
  time_entry.delete()
  messages.success(request, "Der Eintrag wurde gelöscht")
  return redirect('default_time')

@method_decorator(login_required, name="dispatch")
class AddTimeView(View):
  template_name = "homeoffice/add_time.html"

  def get(self, request, line_type, timesheet):
    form_type = self.define_form(line_type)
    form = form_type['form']()
    context = self.initcontext(form_type['pagename'], timesheet, form, line_type)
    return render(request, self.template_name, context)

  def post(self, request, line_type, timesheet):
    form_type = self.define_form(line_type)
    form = form_type['form'](request.POST)
    ts = get_object_or_404(TimeSheet, id=timesheet)
    success_messages = []
    error_messages = []

    if line_type == 'work' and form.is_valid():
      start_date = form.cleaned_data['start_date']
      end_date = form.cleaned_data['end_date']
      start_time = form.cleaned_data['start_time']
      end_time = form.cleaned_data['end_time']
      working_time = form.cleaned_data['working_time']
      break_time = form.cleaned_data['break_time']
      start_m = start_time.hour * 60 + start_time.minute
      end_m = end_time.hour * 60 + end_time.minute

      # Iterate through the days between start_date and end_date
      current_date = start_date
      while current_date <= end_date:
        time_line_saved = False
        time_line, created = TimeSheetLine.objects.get_or_create(
          ts=ts,
          day=current_date.day,
          )
        time_line.start_time = start_time
        time_line.end_time = end_time
        time_line.working_time = working_time
        time_line.break_time = break_time
        time_line_saved = time_line.save()
        current_date += datetime.timedelta(days=1)
      form = form_type['form']()

    if line_type == 'project' and form.is_valid():
      start_date = form.cleaned_data['start_date']
      end_date = form.cleaned_data['end_date']
      project = form.cleaned_data['project']
      working_time = form.cleaned_data['working_time']

      # Iterate through the days between start_date and end_date
      current_date = start_date
      while current_date <= end_date:
        project_time_line_saved = False
        project_time_line, created_ptl = TimeSheetProjectLine.objects.get_or_create(
          ts=ts,
          project=form.cleaned_data['project'],
          day=current_date.day,
          )
        project_time_line.working_time = working_time
        project_time_line_saved = project_time_line.save()
        current_date += datetime.timedelta(days=1)
        # time_line.working_time = max(0, time_line.working_time - round(form.cleaned_data['working_time'], 1))
      form = form_type['form']()

    else: # form is not valid
      form = form_type['form'](request.POST)
    context = self.initcontext(form_type['pagename'], timesheet, form, line_type)
    return render(request, self.template_name, context)

  def initcontext(self, pagename, timesheet, form, line_type):
    employee = Employee.objects.get(pk=self.request.user)
    ts = TimeSheet.objects.get(pk=timesheet)
    empl_fullname = employee.user_link.first_name + " " + employee.user_link.last_name

    context = {
      'pagename': pagename,
      'employee': empl_fullname,
      'year': ts.year,
      'month': ts.month,
      'form': form,
      'line_type': line_type,
      'timesheet': ts.id
    }
    return context

  def define_form(self, line_type):
    if line_type == "work":
      pagename = "Arbeitszeiten bearbeiten"
      form = AddTSLinesForm
    else:
      pagename = "Projektzeiten bearbeiten"
      form = AddTSProjectLinesForm
    return {
      'pagename': pagename,
      'form': form
      }

@method_decorator(login_required, name="dispatch")
class MontageCalendarView(PermissionRequiredMixin, View):
  permission_required = "homeoffice.view_task"
  template_name = "homeoffice/montage.html"

  def get(self, request):
    context = self.initcontext()
    return render(request, self.template_name, context)

  def post(self, request):
    form = FilterTimeForm(request.POST)
    if form.is_valid():
      current_year = int(form.cleaned_data["year_switch"])
      current_month = int(form.cleaned_data["month_switch"])
    context = self.initcontext(current_year, current_month)
    return render(request, self.template_name, context)

  def initcontext(self, year=None, month=None):
    today = datetime.date.today()
    current_year = year or today.year
    current_month = month or today.month
    employee = Employee.objects.get(pk=self.request.user)
    cal = EventCalendar(current_year, current_month)
    form = FilterTimeForm(initial={'year_switch': current_year, 'month_switch': current_month})
    places_open_projects = Place.objects.filter(Q(project__status=True)).distinct()
    places_closed_projects = Place.objects.filter( # places for closed projects with tasks within a month
        Q(project__status=False),
        (
          Q(place_task__start_date__year=current_year, place_task__start_date__month=current_month) |
          Q(place_task__end_date__year=current_year, place_task__end_date__month=current_month)
        )
    ).distinct()
    places = list(places_open_projects | places_closed_projects)
    week_numbers = self.get_week_info(current_year, current_month)
    task_table = self.make_calendar(current_year, current_month, cal.monthdays)
    context = {
      'monthday': cal.monthdays,
      'monthweekday': cal.monthweekday,
      'month': current_month,
      'year': current_year,
      'form': form,
      'today_day': cal.today_day,
      'holidays': cal.holidays['holidays_list'],
      'weekends': cal.holidays['weekends_list'],
      'week_numbers': week_numbers,
      'places': places,
      'tasks': task_table['task_list'],
      'free_cars': task_table['free_cars'],
      'employees': task_table['free_monteurs'],
      'absence_list': task_table['absence_list'],
      'service_list': task_table['service_list'],
    }
    return context

  def make_calendar(self, year, month, monthdays):
    tasks = Task.objects.filter(
      ( 
        Q(start_date__year=year, start_date__month=month) |
        Q(end_date__year=year, end_date__month=month)
      ))
    task_list = [
      {
        'car': event.vehicle.name,
        'worker': event.employee_link.user_link.first_name + ' ' + event.employee_link.user_link.last_name,
        'day': day,
        'place': event.place.id,
        'id': event.id
      }
      for day in monthdays
      for event in tasks.filter(
        start_date__lte=datetime.date(year, month, day),
        end_date__gte=datetime.date(year, month, day)
      )
    ]
    service = Service.objects.filter(
      ( 
        Q(start_date__year=year, start_date__month=month) |
        Q(end_date__year=year, end_date__month=month)
      ))
    service_list = [
      {
        'day': day,
        'car': event.vehicle_link,
        'id': event.id
      }
      for day in monthdays
      for event in service.filter(
        start_date__lte=datetime.date(year, month, day),
        end_date__gte=datetime.date(year, month, day)
      )
    ]
    cars = Vehicle.objects.all()
    default_montage_group = MontageSetup.objects.first().montage_group
    monteurs = Employee.objects.filter(employee_group_link=default_montage_group)
    absence_events = AbsenceEvent.objects.filter(
      # Q(employee_link__in=monteurs),
      Q(employee_link_id__in=monteurs.values_list('user_link', flat=True)),
      Q(start_date__year=year, start_date__month=month) | Q(end_date__year=year, end_date__month=month),
      event_type__in=['employee_event'],
      absence_type__working_time=False
    ).annotate(
        e_absence=F('absence_type__name')
      )
    # absence_group_events are not supported, they are used for workshop only

    free_cars = []
    free_monteurs = []
    absence_summary = defaultdict(set)
    absence_list = []
    for day in monthdays:
      absence_list_perday_tmp =  []
      current_date = datetime.date(year, month, day)
      tasks_on_date = tasks.filter(
        start_date__lte=current_date,
        end_date__gte=current_date
      )
      absence_on_date = absence_events.filter(
        start_date__lte=current_date,
        end_date__gte=current_date
      )
      service_on_date = service.filter(
        start_date__lte=current_date,
        end_date__gte=current_date
      )
      cars_on_service = service_on_date.values_list('vehicle_link', flat=True)
      cars_with_tasks = tasks_on_date.values_list('vehicle', flat=True)
      cars_without_tasks = cars.exclude(id__in=cars_with_tasks).exclude(id__in=cars_on_service)
      car_names = cars_without_tasks
      # car_names = cars_without_tasks.values_list('name', flat=True)
      free_cars.append([day, car_names])
      monteurs_with_tasks = tasks_on_date.values_list('employee_link', flat=True)
      monteurs_without_tasks = monteurs.filter(~Q(user_link__in=monteurs_with_tasks))
      monteurs_list = monteurs_without_tasks.values_list('user_link__first_name', 'user_link__last_name')
      if absence_on_date:
        absent_monteurs_on_date = absence_on_date.values_list('employee_link_id', flat=True).distinct()
        absence_summary = {}
        for event in absence_on_date:
          employee_name = event.employee_link.first_name + ' ' + event.employee_link.last_name
          if employee_name not in absence_summary:
            absence_summary[employee_name] = set()
          absence_summary[employee_name].add(event.e_absence)
        absence_list_perday_tmp = [f"{name} ({', '.join(sorted(absences))})" for name, absences in absence_summary.items()]
        monteurs_list = monteurs_list.exclude(user_link__in=absent_monteurs_on_date)
      free_monteurs.append([day, monteurs_list])
      absence_list.append([day, absence_list_perday_tmp])
    # logging.debug('service_list=%s', service_list)

    return {
      'task_list': task_list,
      'free_cars': free_cars,
      'free_monteurs': free_monteurs,
      'absence_list': absence_list,
      'service_list': service_list
    }

  def get_week_info(self, year, month):
    """ Returns a list of dictionaries containing week numbers and colspan values for a given year and month. """
    weeks = []
    num_weeks = calendar.monthcalendar(year, month)

    for week in num_weeks:
        first_day_of_week = next((day for day in week if day != 0), None)
        if first_day_of_week is not None:
            week_number = datetime.date(year, month, first_day_of_week).isocalendar()[1]
            weekday_count = len([day for day in week if day != 0])
            weeks.append({
                'week_number': week_number,
                'colspan': weekday_count
            })

    return weeks

@login_required(login_url='index')
@permission_required("homeoffice.change_task")
def service_delete_view(request, id):
  event = get_object_or_404(Service, id=id)
  event.delete()
  messages.success(request, "Der Servicedienst wurde entfernt.")
  return redirect('montage')

@login_required(login_url='index')
@permission_required("homeoffice.change_task")
def task_delete_view(request, id):
  event = get_object_or_404(Task, id=id)
  event.delete()
  messages.success(request, "Die Aufgabe wurde entfernt.")
  return redirect('montage')

@method_decorator(login_required, name="dispatch")
class MyMontageCalendarView(PermissionRequiredMixin, MyCalendarView):
  permission_required = "homeoffice.view_task"
  template_name = "homeoffice/mycal_montage.html"

  def initcontext(self, year=None, month=None):
      context = super().initcontext(year, month)
      context.pop('employee_events', None)
      employee = Employee.objects.get(pk=self.request.user)
      context['tasks'] = self.create_tasks(context['year'], context['month'], context['monthdays'], employee)
      return context

  def create_tasks(self, year, month, monthdays, employee):
    tasks = Task.objects.filter(
      ( 
        Q(start_date__year=year, start_date__month=month) |
        Q(end_date__year=year, end_date__month=month)
      ),
      employee_link=employee
    )
    task_list = [
      {
        'place': task.place,
        'car': task.vehicle.name,
        'day': day
      }
      for day in monthdays
      for task in tasks.filter(
        start_date__lte=datetime.date(year, month, day),
        end_date__gte=datetime.date(year, month, day))
    ]
    return task_list

@method_decorator(login_required, name="dispatch")
class TaskEditView(PermissionRequiredMixin, View):
  permission_required = "homeoffice.change_task"
  def get(self, request, id):
    event = get_object_or_404(Task, id=id)
    pagename = "Die Aufgabe bearbeiten"
    form = AddTaskForm(instance=event)
    context = {'form': form, 'pagename': pagename, 'posturl': 'edit_task', 'id': id}
    return render(request, "homeoffice/add_service.html", context)

  def post(self, request, id):
    event = get_object_or_404(Task, id=id)
    form = AddTaskForm(request.POST, instance=event)
    if form.is_valid():
      form.save()
      messages.success(request, "Die Aufgabe wurde geändert")
    else:
      pagename = "Die Aufgabe bearbeiten"
      context = {'form': form, 'pagename': pagename, 'posturl': 'edit_task', 'id': id}
      return render(request, "homeoffice/add_service.html", context)
    return redirect('montage')

@method_decorator(login_required, name="dispatch")
class ServiceEditView(PermissionRequiredMixin, View):
  permission_required = "homeoffice.change_task"
  def get(self, request, id):
    event = get_object_or_404(Service, id=id)
    pagename = "Der Servicedienst bearbeiten"
    form = ServiceForm(instance=event)
    context = {'form': form, 'pagename': pagename, 'posturl': 'edit_service', 'id': id}
    return render(request, "homeoffice/add_service.html", context)

  def post(self, request, id):
    event = get_object_or_404(Service, id=id)
    form = ServiceForm(request.POST, instance=event)
    if form.is_valid():
      form.save()
      messages.success(request, "Der Servicedienst wurde geändert")
    else:
      pagename = "Der Servicedienst bearbeiten"
      context = {'form': form, 'pagename': pagename, 'posturl': 'edit_service', 'id': id}
      return render(request, "homeoffice/add_service.html", context)
    return redirect('montage')

@method_decorator(login_required, name="dispatch")
class ServiceAddView(PermissionRequiredMixin, View):
  permission_required = "homeoffice.change_task"
  def get(self, request):
    pagename = "Der Servicedienst hinzufügen"
    form = ServiceForm()
    context = {'form': form, 'pagename': pagename, 'posturl': 'add_service'}
    return render(request, "homeoffice/add_service.html", context)

  def post(self, request):
    form = ServiceForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, "Der Servicedienst wurde hinzugefügt")
    else:
      pagename = "Der Servicedienst hinzufügen"
      context = {'form': form, 'pagename': pagename, 'posturl': 'add_service'}
      return render(request, "homeoffice/add_service.html", context)
    return redirect('montage')

@method_decorator(login_required, name="dispatch")
class TaskAddView(PermissionRequiredMixin, View):
  permission_required = "homeoffice.change_task"
  def get(self, request):
    pagename = "Die Aufgabe hinzufügen"
    form = AddTaskForm()
    context = {'form': form, 'pagename': pagename, 'posturl': 'add_task'}
    return render(request, "homeoffice/add_service.html", context)

  def post(self, request):
    form = AddTaskForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, "Die Aufgabe wurde hinzugefügt")
    else:
      pagename = "Die Aufgabe hinzufügen"
      context = {'form': form, 'pagename': pagename, 'posturl': 'add_task'}
      return render(request, "homeoffice/add_service.html", context)
    return redirect('montage')

@method_decorator(login_required, name="dispatch")
class TaskDateAddView(PermissionRequiredMixin, View):
  permission_required = "homeoffice.change_task"
  def get(self, request, day, month, year, place):
    pagename = "Die Aufgabe hinzufügen"

    initial_data= {
      'start_date': datetime.date(year, month, day),
      'end_date': datetime.date(year, month, day),
      'place': place
    }
    form = AddTaskForm(initial=initial_data)
    context = {'form': form, 'pagename': pagename, 'posturl': 'add_task'}
    return render(request, "homeoffice/add_service.html", context)

  def post(self, request, day, month, year, place):
    form = AddTaskForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, "Die Aufgabe wurde hinzugefügt")
    else:
      pagename = "Die Aufgabe hinzufügen"
      context = {'form': form, 'pagename': pagename, 'posturl': 'add_task'}
      return render(request, "homeoffice/add_service.html", context)
    return redirect('montage')
