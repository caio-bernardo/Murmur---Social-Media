from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class Post(models.Model):
    content = models.CharField(max_length=280)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")

    created_at = models.DateTimeField(auto_now_add=True)
