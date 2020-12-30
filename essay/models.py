from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.db import models
from quiz.models import Question
from fuzzywuzzy import fuzz


@python_2_unicode_compatible
class Essay_Question(Question):

    def check_if_correct(self, guess):
        answers = Essay_Answer.objects.filter(question=self)
        for answer in answers:
            if fuzz.partial_ratio(str(answer).lower(), guess.lower()) > 90:
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
        verbose_name = _("Essay style question")
        verbose_name_plural = _("Essay style questions")


class Essay_Answer(models.Model):
    question = models.ForeignKey(Essay_Question, verbose_name=_("Question"), on_delete=models.CASCADE)

    correct_answer = models.CharField(max_length=1000,
                               blank=False,
                               help_text=_("Enter the correct answer"),
                               verbose_name=_("Correct Answer"))

    def __str__(self):
        return self.correct_answer

    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")    
