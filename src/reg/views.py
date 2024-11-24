from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib import messages
from reg.models import Issue, IssuePic, IssueComment
from reg.forms import DefectForm, DangerForm, SuggestForm, PicsForm, FilterIssuesForm, IssueCommentsForm
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.db.models import F
from django.contrib.auth.models import User
from django.views import View
from django.urls import reverse
from datetime import date

# If user is logged in, redirect to menu, otherwise to index
def index(request):
  if request.user.is_authenticated:
    return redirect('menu')
  return render(request, "reg/index.html")

@login_required(login_url='index')
def menu(request):
  return render(request, "reg/menu.html")

decorators = []

# we get issue type and issue_id in url
# to delete we get pic_id or comment_id in url, with issue_id to redirect to the right page
# page names are equal here and in the next class, but it may change in the future
# @login_required(login_url='index')
@method_decorator(login_required, name="dispatch")
# @permission_required("reg_add.issue")
class AddIssue(PermissionRequiredMixin, View):
  permission_required = "reg.add_issue"

  def get(self, request, *args, **kwargs):
    issue_type = self.kwargs['issue_type']
    form_name = form_name_type(issue_type)
    form = form_name['formtype']()
    pagename = form_name['pagename']
    imageform = PicsForm()
    issue_add = reverse('issue_add', args=[issue_type]) # define url
    context = { 'form': form, 'imageform': imageform, 'pagename': pagename, 'issue_add': issue_add }
    return render(request, "reg/issue.html", context)

  def post(self, request, *args, **kwargs):
    issue_type=self.kwargs["issue_type"]
    match issue_type:
      case "defect":
        form = DefectForm(request.POST)
        if form.is_valid():
          f = form.save(commit=False)
          f.created_by = request.user
      case "danger":
        form = DangerForm(request.POST)
        if form.is_valid():
          f = form.save(commit=False)
          f.created_by = request.user
          f.project = 'None'
      case "suggest":
        form = SuggestForm(request.POST)
        if form.is_valid():
          f = form.save(commit=False)
          f.created_by = request.user
          f.date = date.today()
          f.project = 'None'
    if form.is_valid(): # again, because we checked inside match
      f.issue_type = issue_type
      f.save()
      images = request.FILES.getlist('pics')
      if images:
        for image in images:
          IssuePic.objects.create(issue=f, pic=image)
      messages.success(request, "Die Meldung wurde hinzugefügt")
      return redirect('menu')
# add 'return' when form is not valid?

@method_decorator(login_required, name="dispatch")
# @login_required(login_url='index')
# I don't understand how to vary form constructors argument, so I use 'case' in every function
# the request.POST itself is a dictionary and it seems that it's not kwargs

class UpdateIssue(PermissionRequiredMixin, View):
  permission_required = "reg.change_issue"
  
  def get(self, request, *args, **kwargs):
    self.id=self.kwargs["id"]
    issue_form = initvars(self, True) # define pagename and create the form
    form = issue_form['form']
    issue = issue_form['issue']
    pagename = issue_form['pagename']
    imageform = PicsForm()
    listurl = reverse('issue_list', args=[issue.issue_type])
    context = {'form': form, 'imageform': imageform, 'pagename': pagename, 'listurl': listurl, 'issue_type': issue.issue_type, 'issue_id': self.id}
    return render(request, "reg/issue_update.html", context)

  def post(self, request, *args, **kwargs):
    self.id=self.kwargs["id"]
    issue_form = initvars(self, True) # define pagename and create the form
    form = issue_form['form']
    issue = issue_form['issue']
    if form.is_valid():
      f = form.save()
      images = request.FILES.getlist('pics')
      for image in images:
        IssuePic.objects.create(issue=f, pic=image)
      messages.success(request, "Die Daten wurden aktualisiert")
      return redirect('issue_list', issue.issue_type)
# add something when the form is not valid?

@method_decorator(login_required, name="dispatch")
# @login_required(login_url='index')
class ViewDetailedIssue(View):
  template_name = "reg/issue_detailed_view.html"
  permission_required = "reg.view_issue"

  def get(self, request, *args, **kwargs):
    self.id=self.kwargs["id"]
    issue_form = initvars(self, False)
    self.issue = issue_form['issue']
    self.formtype = form_name_type(self.issue.issue_type) # define pagename and formtype, but we don't use formtype here
    context = self.initcontext()
    return render(request, self.template_name, context)

  def post(self, request, *args, **kwargs):
    self.id=self.kwargs["id"]
    issue_form = initvars(self, False)
    self.issue = issue_form['issue']
    self.formtype = form_name_type(self.issue.issue_type) # define pagename and formtype, but we don't use formtype here
    form = IssueCommentsForm(request.POST)
    if form.is_valid():
      comment = form.cleaned_data["comment"]
      IssueComment.objects.create(comment=comment, issue=self.issue, created_by=request.user)
      messages.success(request, "Der Kommentar wurde hinzugefügt")
    context = self.initcontext()
    return render(request, self.template_name, context)

  def initcontext(self):
    listurl = reverse('issue_list', args=[self.issue.issue_type])
    form = IssueCommentsForm()
    context = {
      'form': form,
      'issue': self.issue,
      'listurl': listurl,
      'pagename': self.formtype['pagename']
      }
    pics = list(IssuePic.objects.filter(issue=self.id))
    if pics:
      context['pics'] = pics
    comments = list(IssueComment.objects.filter(issue=self.id).annotate(last_name=F('created_by__last_name'), first_name=F('created_by__first_name')))
    if comments:
      context['comments'] = comments
    return context

@login_required(login_url='index')
@permission_required("reg.delete_issuepic")
def issue_delete_pic_view(request, pic_id, issue_id):
  issue_pic = get_object_or_404(IssuePic, id=pic_id)
  issue_pic.delete()
  messages.success(request, "Das Bild wurde gelöscht")
  return redirect('issue_detailed', issue_id)

@login_required(login_url='index')
@permission_required("reg.delete_issuecomment")
def issue_delete_comment_view(request, comment_id, issue_id):
  issue_comment = get_object_or_404(IssueComment, id=comment_id)
  issue_comment.delete()
  messages.success(request, "Der Kommentar wurde gelöscht")
  return redirect('issue_detailed', issue_id)

@login_required(login_url='index')
@permission_required("reg.delete_issue")
def issue_delete_view(request, id):
  issue = get_object_or_404(Issue, id=id)
  issue_type = issue.issue_type
  issue.delete()
  messages.success(request, "Die Meldung wurde gelöscht")
  return redirect('issue_list', issue_type)

@login_required(login_url='index')
# no special permissions required
def satisfied_view(request):
  return render(request, "reg/satisfied.html")

@login_required(login_url='index')
@permission_required("reg.change_issue")
def issue_status_change_view(request, id):
  issue = get_object_or_404(Issue, id=id)
  issue_type = issue.issue_type
  match issue.status:
    case "open":
      issue.status = "closed"
    case "closed":
      issue.status = "open"
  issue.save()
  messages.success(request, "Der Meldungsstatus wurde geändert")
  return redirect('issue_list', issue.issue_type)

# @login_required(login_url='index')
@method_decorator(login_required, name="dispatch")
class IssueList(PermissionRequiredMixin, View):
  template_name = "reg/issue_list_view.html"
  permission_required = "reg.view_issue"

  def get(self, request, *args, **kwargs):
    self.issue_type = self.kwargs["issue_type"]
    self.form = FilterIssuesForm(initial={'type_filter': self.issue_type})
    self.issues = Issue.objects.filter(status="open", issue_type=self.issue_type).annotate(last_name=F('created_by__last_name'), first_name=F('created_by__first_name')).order_by('created')
    context = self.initcontext()
    return render(request, self.template_name, context)

  def post(self, request, *args, **kwargs):
    self.issue_type = self.kwargs["issue_type"]
    self.form = FilterIssuesForm(request.POST, initial={'type_filter': self.issue_type})
    if self.form.is_valid():
      status_filter = self.form.cleaned_data["data_filter"]
      type_filter = self.form.cleaned_data["type_filter"]
      self.issues = Issue.objects.all().annotate(last_name=F('created_by__last_name'), first_name=F('created_by__first_name')).order_by('created')
      # we can annotate initial query as queries are lazy - it's not executed until it's used
      if status_filter and (status_filter != "all"):
        self.issues = self.issues.filter(status=status_filter)
      if type_filter and (type_filter != "all"):
        self.issues = self.issues.filter(issue_type=type_filter)
        self.issue_type = type_filter
    context = self.initcontext()
    messages.success(request, "Das Filter wurde angewendet, um die Daten zu filtern")
    return render(request, self.template_name, context)

  def initcontext(self):
    form_name = form_name_type(self.issue_type)
    labelform = form_name['formtype']()
    listurl = reverse('issue_list', args=[self.issue_type])
    context = {
      'issues': self.issues,
      'form': self.form,
      'pagename': form_name['pagename'],
      'labelform': labelform,
      'listurl': listurl,
      'issue_type': self.issue_type
      }
    return context

def form_name_type(issue_type):
  match issue_type:
    case "defect":
      pagename = 'Defect'
      formtype = DefectForm
    case "danger":
      pagename = 'Unsafe situation'
      formtype = DangerForm
    case "suggest":
      pagename = 'Suggestion'
      formtype = SuggestForm
  return { 'pagename': pagename, 'formtype': formtype }

def initvars(self, createform):
  queryset = Issue.objects.all().annotate(last_name=F('created_by__last_name'), first_name=F('created_by__first_name'))
  issue = get_object_or_404(queryset, id=self.id)

  if createform:
    if self.request.method == 'POST':
      args = {
        'data': self.request.POST,
        'instance': issue
      }
    else:
      args = {
        'instance': issue
      }
    formtype = form_name_type(issue.issue_type)
    form = formtype['formtype'](**args)
    pagename = formtype['pagename']
    return { 'form': form, 'issue': issue, 'pagename': pagename }
  else:
    return { 'issue': issue }
