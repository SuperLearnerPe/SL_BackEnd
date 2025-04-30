from rest_framework import serializers 
from api.models import Parents

class ParentSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Parents 
        fields = [ 
            'id', 'name', 'last_name', 'email', 'phone', 'address', 
            'city', 'country', 'nationality', 'document_type', 'status',
            'document_id', 'birthdate', 'gender', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_email(self, value):
        """Convierte string vacía a None para el campo email"""
        if value == '':
            return None
        return value

class ParentDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Parents
        fields = [
            'id',
            'name',
            'last_name',
            'email',
            'phone',
            'address',
            'city',
            'country',
            'nationality',
            'document_type',
            'document_id',
            'birthdate',
            'gender',
            'status',
            'created_at',
            'updated_at'
        ]

    def validate_email(self, value):
        """Convierte string vacía a None para el campo email"""
        if value == '':
            return None
        return value
