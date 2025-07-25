# Generated by Django 5.2.4 on 2025-07-25 09:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=50)),
                ('text', models.TextField()),
                ('weight', models.IntegerField(default=1)),
                ('subject', models.CharField(max_length=255)),
                ('answer1', models.CharField(max_length=255)),
                ('answer2', models.CharField(max_length=255)),
                ('answer3', models.CharField(max_length=255)),
                ('answer4', models.CharField(blank=True, max_length=255, null=True)),
                ('answer5', models.CharField(blank=True, max_length=255, null=True)),
                ('answer6', models.CharField(blank=True, max_length=255, null=True)),
                ('correct_answer', models.IntegerField()),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='youtube_quiz.quiz')),
            ],
        ),
        migrations.CreateModel(
            name='UserAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.CharField(max_length=255)),
                ('selected_answer', models.IntegerField()),
                ('correct_answer', models.IntegerField(default=1)),
                ('is_correct', models.BooleanField(default=False)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='youtube_quiz.question')),
            ],
        ),
    ]
