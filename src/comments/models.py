from django.contrib.auth.models import User
from django.db import models

from posts.models import Post

# Create your models here.
class Comment(models.Model):
    content = models.CharField(max_length=280)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)
