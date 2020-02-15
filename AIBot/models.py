from django.db import models
# Create your models here.


class AnswerType(models.IntegerChoices):
    YOUNGER = -1
    EQUAL = 0
    OLDER = 1

    @property
    def one_hot(self):
        """Returns a one-hot encoding of the answer."""
        encoding = [0, 0, 0]
        encoding[self.value + 1] = 1

        return encoding


class User(models.Model):
    # No personal info is saved in the DB but the current chat, in order to be able to reply to the current user.
    # The user can /stop the bot at any time and this becomes meaningless.
    chat_id = models.IntegerField(primary_key=True)


class ImagePair(models.Model):
    pair_index = models.PositiveIntegerField(primary_key=True)  # The index refers to the same position in the test set

    image0 = models.ImageField()
    image1 = models.ImageField()

    ai_answer = models.IntegerField(choices=AnswerType.choices)


class Answer(models.Model):

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'image_pair'], name='unique_answer')
        ]

    value = models.IntegerField(choices=AnswerType.choices)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image_pair = models.ForeignKey(ImagePair, on_delete=models.PROTECT)





