from django.contrib import admin
from .models import Question, Quiz, UserAnswer

admin.site.register(Question)
admin.site.register(Quiz)
admin.site.register(UserAnswer)


# Register your models here.
