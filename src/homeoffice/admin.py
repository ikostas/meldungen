from django.contrib import admin

# Register your models here.
from .models import EmployeeAbsenceGroup, AbsenceType, EmployeeGroup, Employee,  WorkTimeSetup, Project, TimeSheetSetup, TimeSheet, TimeSheetLine, TimeSheetProjectLine, Place, Vehicle, Task, MontageSetup

admin.site.register(EmployeeAbsenceGroup)
admin.site.register(AbsenceType)
admin.site.register(EmployeeGroup)
admin.site.register(Employee)
admin.site.register(Project)
admin.site.register(WorkTimeSetup)
admin.site.register(TimeSheetSetup)
admin.site.register(TimeSheet)
admin.site.register(Place)
admin.site.register(Vehicle)
admin.site.register(MontageSetup)
