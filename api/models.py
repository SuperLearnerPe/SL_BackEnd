# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import User

class AttendanceStudent(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_student = models.ForeignKey('Students', models.CASCADE, db_column='id_student')
    id_volunteer = models.ForeignKey('Volunteers', models.CASCADE, db_column='id_volunteer')
    id_session = models.ForeignKey('Session', on_delete=models.CASCADE, db_column='id_session')
    created_date = models.DateTimeField(blank=True, null=True)
    attendance = models.CharField(max_length=11, blank=True, null=True)
 
    
    class Meta:
        managed = False
        db_table = 'attendance_student'

class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()
    

    class Meta:
        managed = False
        db_table = 'auth_user'
        permissions = [
            ("permiso_especial", "Descripción del permiso especial"),
        ]


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class AuthtokenToken(models.Model):
    key = models.CharField(primary_key=True, max_length=40)
    created = models.DateTimeField()
    user = models.OneToOneField(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'authtoken_token'


class BirthParents(models.Model):
    id = models.BigAutoField(primary_key=True, db_comment='Unique identifier for birth_parents')
    id_parent = models.ForeignKey('Parents', models.DO_NOTHING, db_column='id_parent', blank=True, null=True, db_comment='Uniquer')
    city = models.CharField(max_length=255, blank=True, null=True)
    state_department = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'birth_parents'


class BirthStudents(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_student = models.ForeignKey('Students', models.DO_NOTHING, db_column='id_student', blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'birth_students'


class Class(models.Model):
    id = models.BigAutoField(primary_key=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    day = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=100, blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'class'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Parents(models.Model):
    id = models.BigAutoField(primary_key=True, db_comment='Unique identifier for the parents')
    name = models.CharField(max_length=255, blank=True, null=True, db_comment='Names of the parent')
    last_name = models.CharField(max_length=255, blank=True, null=True, db_comment='Last names of the parent')
    email = models.CharField(unique=True, max_length=255, blank=True, null=True, db_comment='Email of the parent')
    phone = models.CharField(unique=True, max_length=255, blank=True, null=True, db_comment='Phone number of the parent including the country calling code')
    address = models.CharField(max_length=255, blank=True, null=True, db_comment='Current residential address of the parent')
    city = models.CharField(max_length=255, blank=True, null=True, db_comment='Current city of the parent')
    country = models.CharField(max_length=255, blank=True, null=True, db_comment='Current country of the parent')
    nationality = models.CharField(max_length=255, blank=True, null=True, db_comment='Current nationality of the parent')
    document_type = models.CharField(max_length=255, blank=True, null=True, db_comment='Type of national identification document of the parent')
    document_id = models.CharField(unique=True, max_length=255, blank=True, null=True, db_comment='Identification number of the national identification document of the parent')
    birthdate = models.DateField(blank=True, null=True, db_comment='Date of birth of the parent')
    gender = models.CharField(max_length=50, blank=True, null=True, db_comment='Gender of the parent')
    status = models.IntegerField(blank=True, null=True, db_comment='Indicates whether the parent is active or inactive')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        managed = False
        db_table = 'parents'
        db_table_comment = 'This table store basic information of the parent'


class StudentClass(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_class = models.ForeignKey(Class, models.CASCADE, db_column='id_class')
    id_student = models.ForeignKey('Students', models.CASCADE, db_column='id_student')
    
    class Meta:
        managed = False
        db_table = 'student_class'

class Students(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    parent = models.ForeignKey(Parents, models.DO_NOTHING, blank=True, null=True)
    nationality = models.CharField(max_length=255, blank=True, null=True)
    document_type = models.CharField(max_length=255, blank=True, null=True)
    document_id = models.CharField(unique=True, max_length=255, blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=50, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'students'
        
class Session(models.Model):
    id_session = models.BigAutoField(primary_key=True)
    id_class = models.ForeignKey(Class, on_delete=models.CASCADE, db_column='id_class')
    date = models.DateTimeField(null=True, blank=True)
    num_session = models.IntegerField(null=True, blank=True) 

    class Meta:
        db_table = 'sessions'


class VolunteerClass(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_class = models.ForeignKey(Class, models.CASCADE, db_column='id_class')
    id_volunteer = models.ForeignKey('Volunteers', models.CASCADE, db_column='id_volunteer')
    
    class Meta:
        managed = False
        db_table = 'volunteer_class' 


class Volunteers(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    personal_email = models.CharField(unique=True, max_length=255, blank=True, null=True)
    phone = models.CharField(unique=True, max_length=255, blank=True, null=True)
    photo = models.CharField(max_length=255, blank=True, null=True )
    nationality = models.CharField(max_length=255, blank=True, null=True)
    document_type = models.CharField(max_length=255, blank=True, null=True)
    document_id = models.CharField(unique=True, max_length=255, blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=50, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now=True )
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    user = models.ForeignKey(AuthUser,  on_delete=models.CASCADE,  blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'volunteers'

class AuthRole(models.Model):
    
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'auth_role'
        

class AuthUserRoles(models.Model):
    id = models.BigAutoField(primary_key=True)  # Para BIGINT NOT NULL AUTO_INCREMENT
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # user_id como clave foránea
    role = models.ForeignKey('AuthRole', on_delete=models.CASCADE)  # role_id como clave foránea

    class Meta:
        managed = False  # Indica que Django no manejará la creación de la tabla
        db_table = 'auth_user_roles'  # Nombre de la tabla