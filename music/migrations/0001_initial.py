# Generated by Django 2.2 on 2020-12-28 18:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('quiz', '0002_auto_20201219_1419'),
    ]

    operations = [
        migrations.CreateModel(
            name='Music_Question',
            fields=[
                ('question_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='quiz.Question')),
            ],
            options={
                'verbose_name': 'Music Question',
                'verbose_name_plural': 'Music questions',
            },
            bases=('quiz.question',),
        ),
        migrations.CreateModel(
            name='Music_Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('correct_artist', models.CharField(help_text='Enter the Artist', max_length=1000, verbose_name='Correct Artist')),
                ('correct_title', models.CharField(help_text='Enter the Title', max_length=1000, verbose_name='Correct Title')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='music.Music_Question', verbose_name='Question')),
            ],
            options={
                'verbose_name': 'Answer',
                'verbose_name_plural': 'Answers',
            },
        ),
    ]