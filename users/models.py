from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class CustomerDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True,blank=True)
    mobile_number = models.CharField(max_length=10,null=True)
    profile_picture = models.FileField(null=True,blank=True,upload_to='Users/Profile_Picture')
    user_type = models.CharField(default='DirectUser',max_length=10,blank=True)
    refferal_code = models.CharField(max_length=200,blank=True,null=True)
    reffered_user = models.CharField(max_length=200,blank=True,null=True)

    @property
    def ImageURL(self):
        try:
           url = self.profile_picture.url
        except:
            url = ''
        return url


