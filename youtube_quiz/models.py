from django.db import models


class Quiz(models.Model):
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    type = models.CharField(max_length=50)
    text = models.TextField()
    weight = models.IntegerField(default=1)
    subject = models.CharField(max_length=255)
    answer1 = models.CharField(max_length=255)
    answer2 = models.CharField(max_length=255)
    answer3 = models.CharField(max_length=255)
    answer4 = models.CharField(max_length=255, blank=True, null=True)
    answer5 = models.CharField(max_length=255, blank=True, null=True)
    answer6 = models.CharField(max_length=255, blank=True, null=True)
    correct_answer = models.IntegerField()

    def __str__(self):
        return self.text
    


class UserAnswer(models.Model):
    user = models.CharField(max_length=255)  
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.IntegerField()  
    correct_answer = models.IntegerField(default=1)  
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.question.text}"