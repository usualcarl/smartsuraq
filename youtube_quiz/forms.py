from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class YouTubeLinkForm(forms.Form):
    youtube_url = forms.URLField(label="Ссылка на YouTube видео", required=True)
    num_questions = forms.IntegerField(
        label="Количество вопросов",
        min_value=1,
        max_value=50,
        initial=10
    )
    num_answers = forms.ChoiceField(
        label="Количество вариантов ответа",
        choices=[(i, i) for i in range(3, 7)], 
        initial=4  
    )

