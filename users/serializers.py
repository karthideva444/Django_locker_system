from django.contrib.auth import authenticate
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
  email = serializers.EmailField(
    required=True,
    validators=[UniqueValidator(queryset=User.objects.all())]
  )
  password = serializers.CharField(
    write_only=True, required=True, validators=[validate_password])
  
  class Meta:
    model = User
    fields = ('username','password', 'email')

  def validate(self, attrs):
    if len(attrs['password']) < 8:
      raise serializers.ValidationError(
        {"password": "Password should be equal or greater than 8 characters."})
    return attrs
  
#   def create(self, validated_data):
#     user = User.objects.create(
#       username=validated_data['username'],
#       email=validated_data['email'],
#     )
#     user.set_password(validated_data['password'])
#     user.save()
#     return user
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')