from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.db import models
from quiz.models import Question
from fuzzywuzzy import fuzz


@python_2_unicode_compatible
class Music_Question(Question):

    def check_if_correct(self, guess):
        answers = Music_Answer.objects.filter(question=self)
        for answer in answers:
            if fuzz.partial_ratio(str(answer.correct_artist).lower(), guess.lower()) > 90:
                return True
        return False

    def check_title_correct(self, guess):
        answers = Music_Answer.objects.filter(question=self)
        for answer in answers:
            if fuzz.partial_ratio(str(answer.correct_title).lower(), guess.lower()) > 90:
                return True
        return False

    def get_answers(self):
        return False

    def get_answers_list(self):
        return False

    def answer_choice_to_string(self, guess):
        return str(guess)

    def __str__(self):
        return self.content

    class Meta:
        verbose_name = _("Music Question")
        verbose_name_plural = _("Music questions")


class Music_Answer(models.Model):
    question = models.ForeignKey(Music_Question, verbose_name=_("Question"), on_delete=models.CASCADE)

    correct_artist = models.CharField(max_length=1000,
                               blank=False,
                               help_text=_("Enter the Artist"),
                               verbose_name=_("Correct Artist"))

    correct_title = models.CharField(max_length=1000,
                               blank=False,
                               help_text=_("Enter the Title"),
                               verbose_name=_("Correct Title"))

    def __str__(self):
        return f"{self.correct_artist} - {self.correct_title}"

    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")    
