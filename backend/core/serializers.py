from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
'''
This is for creating additional fields in userregistration
Now this serializer will represent our UserRegistration Page
We create this serializer here because it is only for this project
'''
class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id','username','password','email','first_name','last_name']
# For adding more fields to user/me end point
class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields= ['id','username','email','first_name','last_name']
        