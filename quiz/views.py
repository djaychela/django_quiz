import enum
import random
import re

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, TemplateView, FormView
from django.utils.text import slugify

from random import randint

from .forms import QuestionForm, EssayForm, MusicForm
from .models import Quiz, Category, Progress, Sitting, Question, Score
from essay.models import Essay_Question
from music.models import Music_Question


class QuizMarkerMixin(object):
    @method_decorator(login_required)
    @method_decorator(permission_required("quiz.view_sittings"))
    def dispatch(self, *args, **kwargs):
        return super(QuizMarkerMixin, self).dispatch(*args, **kwargs)


class SittingFilterTitleMixin(object):
    def get_queryset(self):
        queryset = super(SittingFilterTitleMixin, self).get_queryset()
        quiz_filter = self.request.GET.get("quiz_filter")
        if quiz_filter:
            queryset = queryset.filter(quiz__title__icontains=quiz_filter)

        return queryset


class QuizListView(ListView):
    model = Quiz

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        scores_dict = {}

        try:
            round_scores = Score.objects.filter(user=user).all()
            for round in round_scores:
                if round.round in scores_dict.keys():
                    scores_dict[round.round] += round.score
                else:
                    scores_dict[round.round] = round.score
        except TypeError:
            # user is not signed in, so remove all quizzes
            context['quiz_list'] = None
            pass
        
        context["scores_dict"] = scores_dict
        return context

    def get_queryset(self):
        queryset = super(QuizListView, self).get_queryset()
        # filter by score present?
        
        return queryset.filter(draft=False)


class QuizDetailView(DetailView):
    model = Quiz
    slug_field = "url"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.draft and not request.user.has_perm("quiz.change_quiz"):
            raise PermissionDenied

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class CategoriesListView(ListView):
    model = Category


class ViewQuizListByCategory(ListView):
    model = Quiz
    template_name = "view_quiz_category.html"

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(
            Category, category=self.kwargs["category_name"]
        )

        return super(ViewQuizListByCategory, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ViewQuizListByCategory, self).get_context_data(**kwargs)

        context["category"] = self.category
        return context

    def get_queryset(self):
        queryset = super(ViewQuizListByCategory, self).get_queryset()
        return queryset.filter(category=self.category, draft=False)



class ProgressViewNew(TemplateView):
    template_name = "progress_new.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        round_list = Quiz.objects.filter(draft=False).all().order_by("title")
        round_names = [slugify(quiz) for quiz in Quiz.objects.filter(draft=False).all().order_by("title")]

        user_stats_list = []
        current_user = {}
        current_user["name"] = user
        user_score_total = 0
        for idx, round in enumerate(Quiz.objects.filter(draft=False).all().order_by("title")):
            round_num = int(str(round)[-1:])
            user_round_scores = (
                Score.objects.filter(user=user).filter(round=round_num).all()
            )
            this_round_score = 0
            for user_score in user_round_scores:
                this_round_score += user_score.score

            current_user[round_names[idx]] = this_round_score
            user_score_total += this_round_score

        current_user["total"] = user_score_total
        user_stats_list.append(current_user)

        context["user_stats_list"] = user_stats_list
        context["round_list"] = round_list
        context["round_names"] = round_names
        return context


class LeaderboardNew(TemplateView):
    template_name = "leaderboard_new.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        User = get_user_model()
        user_list = User.objects.all()
        round_list = Quiz.objects.filter(draft=False).all()
        round_names = [slugify(quiz) for quiz in Quiz.objects.filter(draft=False).all().order_by("title")]

        user_stats_list = []
        max_scores = {}
        for user in user_list:
            current_user = {}
            current_user["name"] = user
            user_score_total = 0
            for idx, round in enumerate(Quiz.objects.filter(draft=False).all().order_by("title")):
                round_num = int(str(round)[-1:])
                round_name = slugify(round)
                user_round_scores = (
                    Score.objects.filter(user=user).filter(round=round_num).all()
                )
                this_round_score = 0
                for user_score in user_round_scores:
                    this_round_score += user_score.score

                current_user[round_names[idx]] = this_round_score
                user_score_total += this_round_score

                if round_name in max_scores.keys():
                    if this_round_score > max_scores[round_name]:
                        max_scores[round_name] = this_round_score
                else:
                    max_scores[round_name] = this_round_score

            current_user["total"] = user_score_total
            user_stats_list.append(current_user)

        # sort user_stats_list by total score
        user_stats_list = sorted(user_stats_list, key=lambda k: k['total'], reverse=True)

        context["max_scores"] = max_scores
        context["user_stats_list"] = user_stats_list
        context["round_list"] = round_list
        context["round_names"] = round_names
        return context


class QuizUserFinalProgressView(TemplateView):
    template_name = "final_progress.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(QuizUserFinalProgressView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(QuizUserFinalProgressView, self).get_context_data(**kwargs)
        progress, c = Progress.objects.get_or_create(user=self.request.user)
        context["cat_scores"] = progress.list_all_cat_scores
        context["exams"] = progress.show_exams()
        return context


class QuizMarkingList(QuizMarkerMixin, SittingFilterTitleMixin, ListView):
    model = Sitting

    def get_queryset(self):
        queryset = super(QuizMarkingList, self).get_queryset().filter(complete=True)

        user_filter = self.request.GET.get("user_filter")
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)

        return queryset


class QuizMarkingDetail(QuizMarkerMixin, DetailView):
    model = Sitting

    def post(self, request, *args, **kwargs):
        sitting = self.get_object()

        q_to_toggle = request.POST.get("qid", None)
        if q_to_toggle:
            q = Question.objects.get_subclass(id=int(q_to_toggle))
            if int(q_to_toggle) in sitting.get_incorrect_questions:
                sitting.remove_incorrect_question(q)
            else:
                sitting.add_incorrect_question(q)

        return self.get(request)

    def get_context_data(self, **kwargs):
        context = super(QuizMarkingDetail, self).get_context_data(**kwargs)
        context["questions"] = context["sitting"].get_questions(with_answers=True)
        return context


class QuizTake(FormView):
    form_class = QuestionForm
    template_name = "question.html"
    result_template_name = "result.html"
    single_complete_template_name = "single_complete.html"

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, url=self.kwargs["quiz_name"])
        if self.quiz.draft and not request.user.has_perm("quiz.change_quiz"):
            raise PermissionDenied

        try:
            self.logged_in_user = self.request.user.is_authenticated()
        except TypeError:
            self.logged_in_user = self.request.user.is_authenticated

        if self.logged_in_user:
            self.sitting = Sitting.objects.user_sitting(request.user, self.quiz)
        else:
            self.sitting = self.anon_load_sitting()

        if self.sitting is False:
            return render(request, self.single_complete_template_name)

        return super(QuizTake, self).dispatch(request, *args, **kwargs)

    def get_form(self, *args, **kwargs):
        if self.logged_in_user:
            self.question = self.sitting.get_first_question()
            self.progress = self.sitting.progress()
        else:
            self.question = self.anon_next_question()
            self.progress = self.anon_sitting_progress()

        if self.question.__class__ is Essay_Question:
            form_class = EssayForm
        elif self.question.__class__ is Music_Question:
            form_class = MusicForm
        else:
            form_class = self.form_class

        # print(f"form class:{form_class}")

        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        kwargs = super(QuizTake, self).get_form_kwargs()

        return dict(kwargs, question=self.question)

    def form_valid(self, form):
        # print("form valid called...")
        if self.logged_in_user:
            self.form_valid_user(form)
            if self.sitting.get_first_question() is False:
                return self.final_result_user()
        else:
            self.form_valid_anon(form)
            if not self.request.session[self.quiz.anon_q_list()]:
                return self.final_result_anon()

        self.request.POST = {}

        return super(QuizTake, self).get(self, self.request)

    def get_context_data(self, **kwargs):
        context = super(QuizTake, self).get_context_data(**kwargs)
        context["question"] = self.question
        context["quiz"] = self.quiz
        if hasattr(self, "previous"):
            context["previous"] = self.previous
        if hasattr(self, "progress"):
            context["progress"] = self.progress
        return context

    def form_valid_user(self, form):
        progress, c = Progress.objects.get_or_create(user=self.request.user)
        # print("Form valid user called...")

        # check for silent value for music quiz questions, mark accordingly.
        music_guess = None
        try:
            music_guess = form.cleaned_data["answer_title"]
        except:
            pass

        guess = form.cleaned_data["answers"]
        is_correct = self.question.check_if_correct(guess)

        if is_correct is True:
            self.sitting.add_to_score(1)
            progress.update_score(self.question, 1, 1)
        else:
            self.sitting.add_incorrect_question(self.question)
            progress.update_score(self.question, 0, 1)

        if self.quiz.answers_at_end is not True:
            self.previous = {
                "previous_answer": guess,
                "previous_outcome": is_correct,
                "previous_question": self.question,
                "answers": self.question.get_answers(),
                "question_type": {self.question.__class__.__name__: True},
            }
        else:
            self.previous = {}

        score = 0
        if music_guess:
            # music question, so 0.5 for each part right...
            # check first part
            if is_correct:
                score = 0.5
            # check second part
            if self.question.check_title_correct(music_guess):
                score += 0.5

        else:
            # normal marking
            if is_correct:
                score = 1

        quiz_round = str(self.question)
        round = int(quiz_round.split()[0][1:])
        question = int(quiz_round.split()[1][1:])

        # add score to database...
        question_score = Score()
        question_score.user = self.request.user
        question_score.round = round
        question_score.question = question
        question_score.score = score
        question_score.save()

        self.sitting.add_user_answer(self.question, guess)
        self.sitting.remove_first_question()

    def final_result_user(self):
        results = {
            "quiz": self.quiz,
            "score": self.sitting.get_current_score,
            "max_score": self.sitting.get_max_score,
            "percent": self.sitting.get_percent_correct,
            "sitting": self.sitting,
            "previous": self.previous,
            "incorrect": self.sitting.get_incorrect_questions_list,
        }

        self.sitting.mark_quiz_complete()

        if self.quiz.answers_at_end:
            results["questions"] = self.sitting.get_questions(with_answers=True)
            results["incorrect_questions"] = self.sitting.get_incorrect_questions

        if self.quiz.exam_paper is False:
            self.sitting.delete()

        return render(self.request, self.result_template_name, results)

    def anon_load_sitting(self):
        if self.quiz.single_attempt is True:
            return False

        if self.quiz.anon_q_list() in self.request.session:
            return self.request.session[self.quiz.anon_q_list()]
        else:
            return self.new_anon_quiz_session()

    def new_anon_quiz_session(self):
        """
        Sets the session variables when starting a quiz for the first time
        as a non signed-in user
        """
        self.request.session.set_expiry(259200)  # expires after 3 days
        questions = self.quiz.get_questions()
        question_list = [question.id for question in questions]

        if self.quiz.random_order is True:
            random.shuffle(question_list)

        if self.quiz.max_questions and (self.quiz.max_questions < len(question_list)):
            question_list = question_list[: self.quiz.max_questions]

        # session score for anon users
        self.request.session[self.quiz.anon_score_id()] = 0

        # session list of questions
        self.request.session[self.quiz.anon_q_list()] = question_list

        # session list of question order and incorrect questions
        self.request.session[self.quiz.anon_q_data()] = dict(
            incorrect_questions=[],
            order=question_list,
        )

        return self.request.session[self.quiz.anon_q_list()]

    def anon_next_question(self):
        next_question_id = self.request.session[self.quiz.anon_q_list()][0]
        return Question.objects.get_subclass(id=next_question_id)

    def anon_sitting_progress(self):
        total = len(self.request.session[self.quiz.anon_q_data()]["order"])
        answered = total - len(self.request.session[self.quiz.anon_q_list()])
        return (answered, total)

    def form_valid_anon(self, form):
        guess = form.cleaned_data["answers"]
        is_correct = self.question.check_if_correct(guess)

        if is_correct:
            self.request.session[self.quiz.anon_score_id()] += 1
            anon_session_score(self.request.session, 1, 1)
        else:
            anon_session_score(self.request.session, 0, 1)
            self.request.session[self.quiz.anon_q_data()]["incorrect_questions"].append(
                self.question.id
            )

        self.previous = {}
        if self.quiz.answers_at_end is not True:
            self.previous = {
                "previous_answer": guess,
                "previous_outcome": is_correct,
                "previous_question": self.question,
                "answers": self.question.get_answers(),
                "question_type": {self.question.__class__.__name__: True},
            }

        self.request.session[self.quiz.anon_q_list()] = self.request.session[
            self.quiz.anon_q_list()
        ][1:]

    def final_result_anon(self):
        score = self.request.session[self.quiz.anon_score_id()]
        q_order = self.request.session[self.quiz.anon_q_data()]["order"]
        max_score = len(q_order)
        percent = int(round((float(score) / max_score) * 100))
        session, session_possible = anon_session_score(self.request.session)
        if score is 0:
            score = "0"

        results = {
            "score": score,
            "max_score": max_score,
            "percent": percent,
            "session": session,
            "possible": session_possible,
        }

        del self.request.session[self.quiz.anon_q_list()]

        if self.quiz.answers_at_end:
            results["questions"] = sorted(
                self.quiz.question_set.filter(id__in=q_order).select_subclasses(),
                key=lambda q: q_order.index(q.id),
            )

            results["incorrect_questions"] = self.request.session[
                self.quiz.anon_q_data()
            ]["incorrect_questions"]

        else:
            results["previous"] = self.previous

        del self.request.session[self.quiz.anon_q_data()]

        return render(self.request, "result.html", results)


def anon_session_score(session, to_add=0, possible=0):
    """
    Returns the session score for non-signed in users.
    If number passed in then add this to the running total and
    return session score.

    examples:
        anon_session_score(1, 1) will add 1 out of a possible 1
        anon_session_score(0, 2) will add 0 out of a possible 2
        x, y = anon_session_score() will return the session score
                                    without modification

    Left this as an individual function for unit testing
    """
    if "session_score" not in session:
        session["session_score"], session["session_score_possible"] = 0, 0

    if possible > 0:
        session["session_score"] += to_add
        session["session_score_possible"] += possible

    return session["session_score"], session["session_score_possible"]
