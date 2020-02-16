from django.db import models
from django.db.models import Q
# Create your models here.


class AnswerType(models.IntegerChoices):
    YOUNGER = -1
    EQUAL = 0
    OLDER = 1

    @staticmethod
    def one_hot(value):
        """Returns a one-hot encoding of the answer."""
        encoding = [0, 0, 0]
        encoding[value + 1] = 1

        return encoding

    @staticmethod
    def readable(value):
        if value == -1:
            return "Prima foto"
        elif value == 0:
            return "Stessa età"
        else:
            return "Seconda foto"

class User(models.Model):
    # No personal info is saved in the DB but the current chat, in order to be able to reply to the current user.
    # The user can /stop the bot at any time and this becomes meaningless.
    chat_id = models.IntegerField(primary_key=True)


class ImagePair(models.Model):
    pair_index = models.PositiveIntegerField(primary_key=True)  # The index refers to the same position in the test set. For now it is assumed that they are a ordered sequence.

    image0 = models.ImageField()
    image1 = models.ImageField()

    ai_answer = models.IntegerField(choices=AnswerType.choices)
    correct_answer = models.IntegerField(choices=AnswerType.choices)


class Challenge(models.Model):

    pair_to_analyze = models.ForeignKey(ImagePair, on_delete=models.CASCADE, null=True)
    completed = models.BooleanField(default=False)  # only polls with the whole dataset examined will be considered.

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=(Q(pair_to_analyze__isnull=True) & Q(completed=True)) |
                                         (Q(pair_to_analyze__isnull=False) & Q(completed=False)),
                                   name="check_completed_if_nothing_to_analyze")
        ]

class Answer(models.Model):

    value = models.IntegerField(choices=AnswerType.choices)

    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    image_pair = models.ForeignKey(ImagePair, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['challenge', 'image_pair'], name='unique_answer')
        ]
