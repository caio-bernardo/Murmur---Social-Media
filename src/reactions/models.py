from django.db import models
from django.contrib.auth.models import User
from posts.models import Post

# Create your models here.
class ReactionType(models.TextChoices):
    LIKE = 'like', 'Like'
    DISLIKE = 'dislike', 'Dislike'

class Reaction(models.Model):
    """
    Reaction model for storing user reactions (likes/dislikes) to posts.
    Each user can have only one reaction per post.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    reaction_type = models.CharField(
        max_length=10,
        choices=ReactionType.choices,
        default=ReactionType.LIKE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Ensure that a user can only have one reaction per post.
        """
        unique_together = ('user', 'post')
        indexes = [
            models.Index(fields=['post', 'reaction_type']),
            models.Index(fields=['user', 'post'])
        ]

    def __str__(self):
        return f"{self.user.username} {self.reaction_type} {self.post.pk}"
