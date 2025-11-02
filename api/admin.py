from django.contrib import admin
from api.models import AttendanceStudent, AuthtokenToken, BirthParents, Class, Parents, StudentClass, Students, Session, VolunteerClass, Volunteers, AuthRole, AuthUserRoles

# Register your models here.
admin.site.register(AttendanceStudent)
admin.site.register(BirthParents)
admin.site.register(AuthtokenToken)
admin.site.register(Class)
admin.site.register(Parents)
admin.site.register(StudentClass)
admin.site.register(Students)
admin.site.register(Session)
admin.site.register(VolunteerClass)
admin.site.register(Volunteers)
admin.site.register(AuthRole)
admin.site.register(AuthUserRoles)

