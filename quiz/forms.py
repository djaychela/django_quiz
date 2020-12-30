from django import forms
from django.forms.widgets import RadioSelect, Textarea


class QuestionForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        choice_list = [x for x in question.get_answers_list()]
        self.fields["answers"] = forms.ChoiceField(choices=choice_list,
                                                   widget=RadioSelect)


class EssayForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(EssayForm, self).__init__(*args, **kwargs)
        self.fields["answers"] = forms.CharField(
            widget=Textarea(attrs={'style': 'width:100%', 'placeholder':'Your Answer', 'rows':'2'}))


class MusicForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(MusicForm, self).__init__(*args, **kwargs)
        self.fields["answers"] = forms.CharField(
            widget=Textarea(attrs={'style': 'width:100%', 'placeholder':'Artist', 'rows':'2'}))
        self.fields["answer_title"] = forms.CharField(
            widget=Textarea(attrs={'style': 'width:100%', 'placeholder':'Title', 'rows':'2'}))
