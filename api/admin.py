from django.contrib import admin
from api.models import AttendanceStudent, AuthtokenToken, BirthParents, Courses, Parents, StudentCourses, Students, Session, VolunteerCourses, Volunteers, AuthRole, AuthUserRoles

# Register your models here.
admin.site.register(AttendanceStudent)
admin.site.register(BirthParents)
admin.site.register(AuthtokenToken)
admin.site.register(Courses)
admin.site.register(Parents)
admin.site.register(StudentCourses)
admin.site.register(Students)
admin.site.register(Session)
admin.site.register(Volunteers)
admin.site.register(AuthRole)
admin.site.register(AuthUserRoles)
admin.site.register(VolunteerCourses)