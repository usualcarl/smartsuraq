import json
import os
import re
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Quiz, Question, UserAnswer
from .forms import YouTubeLinkForm
from yt_dlp import YoutubeDL
import whisper
from openai import OpenAI


def download_audio_from_youtube(url):
    output_dir = "/tmp"
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        audio_file = ydl.prepare_filename(info).replace('.webm', '.mp3')
    return audio_file

def transcribe_audio(audio_file):
    model = whisper.load_model("base")
    print("Начинается транскрибация...")
    result = model.transcribe(audio_file)
    print("Транскрибация завершена!")
    return result['text']

def extract_json_from_message(content):
    match = re.search(r"```json\s*(\[.*?\])\s*```", content, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Ошибка декодирования JSON: {e}")
            return None
    else:
        print("JSON не найден в тексте.")
        return None

def generate_quiz(text, num_questions, num_answers):
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("API ключ не найден. Проверьте .env")

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    )

    completion = client.chat.completions.create(
        model="qwen-plus-2025-04-28",
        messages=[
            {
                "role": "user",
                "content": f"""
На основе предоставленного текста создай тест из {num_questions} вопросов в академически-образовательном стиле, не переводя английские термины.

Каждый вопрос должен быть в формате JSON со следующими полями:
- type: тип вопроса (например, single_choice)
- text: текст вопроса
- weight: вес вопроса (например, 1)
- subject: тема вопроса
- answer1, answer2, ..., answer{num_answers}: варианты ответов
- correct_1_to_{num_answers}: номер правильного ответа (от 1 до {num_answers})

Ответь только JSON-списком без обрамления ``` и пояснений.

Текст для анализа:
{text}
                """
            }
        ],
    )

    message_content = completion.choices[0].message.content

    try:
        quiz_data = json.loads(message_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка при декодировании JSON из message_content: {e}")

    if not quiz_data:
        raise ValueError("Не удалось извлечь ни одного корректного вопроса из ответа модели.")

    return quiz_data

def index(request):
    if request.method == 'POST':
        form = YouTubeLinkForm(request.POST)
        action = request.POST.get('action')  

        if form.is_valid():
            youtube_url = form.cleaned_data['youtube_url']
            num_questions = form.cleaned_data['num_questions']
            num_answers = int(form.cleaned_data['num_answers'])

            try:
                audio_file = download_audio_from_youtube(youtube_url)
                logging.debug(f"Аудиофайл загружен: {audio_file}")

                text = transcribe_audio(audio_file)
                logging.debug(f"Транскрибированный текст: {text}")

                if action == 'quiz':
                    quiz_data = generate_quiz(text, num_questions, num_answers)
                    logging.debug(f"Сгенерированный тест: {quiz_data}")

                    quiz = Quiz.objects.create(title=f"Quiz from {youtube_url}",)

                    for q in quiz_data:
                        answers = {f'answer{i}': q.get(f'answer{i}', '') for i in range(1, num_answers + 1)}
                        correct_answer_key = f'correct_1_to_{num_answers}'
                        if correct_answer_key not in q:
                            raise ValueError(f"Отсутствует поле '{correct_answer_key}' в данных вопроса.")
                        Question.objects.create(
                            quiz=quiz,
                            type=q['type'],
                            text=q['text'],
                            weight=q['weight'],
                            subject=q['subject'],
                            correct_answer=q[correct_answer_key],
                            **answers
                        )
                    return redirect('quiz_detail', quiz_id=quiz.id)

            except Exception as e:
                logging.error(f"Произошла ошибка: {e}")
                return render(request, 'error.html', {'error_message': str(e)})
    else:
        form = YouTubeLinkForm()

    return render(request, 'index.html', {'form': form})

def quiz_detail(request, quiz_id):
    quiz = Quiz.objects.get(id=quiz_id)
    questions = quiz.questions.all()
    return render(request, 'quiz_detail.html', {'quiz': quiz, 'questions': questions})

def submit_answers(request, quiz_id):
    if request.method == 'POST':
        quiz = Quiz.objects.get(id=quiz_id)
        questions = quiz.questions.all()
        score = 0
        results = []
        incorrect_questions = []

        for question in questions:
            selected_answer = int(request.POST.get(f'question_{question.id}'))
            correct_answer = question.correct_answer
            is_correct = (selected_answer == correct_answer)

            UserAnswer.objects.create(
                user="Anonymous",
                question=question,
                selected_answer=selected_answer,
                correct_answer=correct_answer,
                is_correct=is_correct
            )

            results.append({
                'question': question.text,
                'selected_answer': getattr(question, f'answer{selected_answer}'),
                'correct_answer': getattr(question, f'answer{correct_answer}'),
                'is_correct': is_correct
            })

            if not is_correct:
                incorrect_questions.append(question.text)
            if is_correct:
                score += question.weight

        return render(request, 'quiz_results.html', {
            'score': score,
            'total': len(questions),
            'results': results,
            'incorrect_questions_json': json.dumps(incorrect_questions)
        })

@csrf_exempt
def get_recommendation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            incorrect_questions = data.get('incorrect_questions', [])

            if not incorrect_questions:
                return JsonResponse({'recommendation': 'Нет неправильных ответов. Вы молодец!'})

            prompt = f"""
На основе следующих вопросов, на которые пользователь ответил неправильно, составьте персональную рекомендацию о том, какие темы стоит повторить.
Также предложите несколько источников (например, статьи, видео или книги) для изучения этих тем.
Вопросы:
{', '.join(incorrect_questions)}
            """

            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("API ключ не найден. Проверьте .env")

            client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            )
            completion = client.chat.completions.create(
                model="qwen-plus-2025-04-28",
                messages=[
                    {'role': 'user', 'content': prompt}
                ],
            )

            recommendation = completion.choices[0].message.content.strip()
            recommendation = clean_text(recommendation)
            recommendation = make_links_clickable(recommendation)
            recommendation = format_recommendation(recommendation)

            return JsonResponse({'recommendation': recommendation})
        except Exception as e:
            return JsonResponse({'recommendation': f'Ошибка при получении рекомендации: {str(e)}'})
    return JsonResponse({'recommendation': 'Метод не поддерживается.'})

def clean_text(text):
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'[^\s]+">', '', text)
    text = re.sub(r'^\s*#.*$', '', text, flags=re.MULTILINE)
    text = text.replace('**', '')
    return text.strip()

def make_links_clickable(text):
    markdown_link_pattern = re.compile(r'([^>\s]+)\s*">\s*(https?://[^\s\)]+)\s*">\s*([^<]+)')
    text = markdown_link_pattern.sub(r'<a href="\2">\3</a>', text)
    url_pattern = re.compile(r'(https?://[^\s\)]+)')
    text = url_pattern.sub(r'<a href="\1">\1</a>', text)
    return text

def format_recommendation(text):
    lines = text.split('\n')
    formatted_lines = []
    for line in lines:
        if re.match(r'^\d+\.', line):
            formatted_lines.append(f"<li>{line.strip()}</li>")
        elif line.strip():
            formatted_lines.append(f"<p>{line.strip()}</p>")

    formatted_text = '\n'.join(formatted_lines)

    if '<li>' in formatted_text:
        formatted_text = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', formatted_text, flags=re.DOTALL)

    return formatted_text


