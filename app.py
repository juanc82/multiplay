import random
from flask import Flask, render_template, request, redirect, url_for, session, jsonify # Importar jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # ¡Cámbiala por una cadena aleatoria y segura!

# Almacenamiento de resultados (en memoria para este ejemplo)
user_scores = {
    'Paula': {'correctas': 0, 'incorrectas': 0},
    'Sofia': {'correctas': 0, 'incorrectas': 0}
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/select_profile', methods=['POST'])
def select_profile():
    profile = request.form.get('profile')
    if profile in user_scores:
        session['current_profile'] = profile
        # Inicializar preguntas si no existen al seleccionar perfil
        session['all_questions'] = generate_all_multiplications()
        random.shuffle(session['all_questions'])
        session['current_question_index'] = 0
        session['questions_answered'] = [None] * len(session['all_questions'])
        return redirect(url_for('game'))
    return redirect(url_for('index'))

@app.route('/game')
def game():
    if 'current_profile' not in session:
        return redirect(url_for('index'))

    # Asegurarse de que las preguntas están inicializadas (esto también se hace en select_profile)
    if 'all_questions' not in session or not session.get('all_questions'):
        session['all_questions'] = generate_all_multiplications()
        random.shuffle(session['all_questions'])
        session['current_question_index'] = 0
        session['questions_answered'] = [None] * len(session['all_questions'])

    current_question_data = get_next_question_data()

    if not current_question_data:
        # Todas las preguntas han sido respondidas o error
        return redirect(url_for('results'))

    return render_template('game.html',
                           profile=session['current_profile'],
                           num1=current_question_data['num1'],
                           num2=current_question_data['num2'],
                           options=current_question_data['options'],
                           correct_answer=current_question_data['correct_answer'],
                           question_id=current_question_data['question_id'])

# NUEVA RUTA para manejar respuestas AJAX
@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if 'current_profile' not in session:
        return jsonify({'error': 'No profile selected'}), 401

    data = request.get_json() # Obtener los datos JSON de la solicitud
    user_answer = data.get('answer')
    correct_answer = data.get('correct_answer')
    question_id = data.get('question_id')

    # Actualizar la puntuación
    if user_answer == correct_answer:
        session['questions_answered'][question_id] = True
        user_scores[session['current_profile']]['correctas'] += 1
    else:
        session['questions_answered'][question_id] = False
        user_scores[session['current_profile']]['incorrectas'] += 1

    # Obtener la siguiente pregunta
    next_question_data = get_next_question_data()

    if not next_question_data:
        # Si no hay más preguntas, indicar al cliente que redirija a resultados
        return jsonify({'redirect_to_results': url_for('results')})
    else:
        # Devolver los datos de la siguiente pregunta
        return jsonify({'next_question': next_question_data})


def get_next_question_data():
    """
    Función auxiliar para encontrar la próxima pregunta no respondida
    y preparar sus datos para el cliente.
    """
    if 'all_questions' not in session or 'questions_answered' not in session:
        return None

    current_question_index = session.get('current_question_index', 0)
    all_questions = session['all_questions']
    questions_answered = session['questions_answered']

    next_q = None
    next_q_id = current_question_index

    # Buscar la próxima pregunta no respondida
    while next_q_id < len(all_questions):
        if questions_answered[next_q_id] is None:
            next_q = all_questions[next_q_id]
            break
        next_q_id += 1

    session['current_question_index'] = next_q_id # Actualizar el índice para la próxima búsqueda

    if not next_q:
        return None # No hay más preguntas

    num1, num2 = next_q['factors']
    correct_result = num1 * num2
    options = generate_options(correct_result)

    return {
        'num1': num1,
        'num2': num2,
        'options': options,
        'correct_answer': correct_result,
        'question_id': next_q_id
    }

@app.route('/results')
def results():
    if 'current_profile' not in session:
        return redirect(url_for('index'))

    profile_scores = user_scores[session['current_profile']]
    correctas = profile_scores['correctas']
    incorrectas = profile_scores['incorrectas']
    total_preguntas = correctas + incorrectas

    # Resetear las preguntas para la próxima vez que juegue
    session.pop('all_questions', None)
    session.pop('current_question_index', None)
    session.pop('questions_answered', None)
    # No resetear los contadores de user_scores aquí, ya que se mantienen por perfil
    user_scores[session['current_profile']]['correctas'] = 0
    user_scores[session['current_profile']]['incorrectas'] = 0


    return render_template('results.html',
                           profile=session['current_profile'],
                           correctas=correctas,
                           incorrectas=incorrectas,
                           total_preguntas=total_preguntas)

def generate_all_multiplications():
    questions = []
    for i in range(10): # Tablas del 0 al 9
        for j in range(10):
            questions.append({'factors': (i, j)})
    return questions

def generate_options(correct_answer):
    options = [correct_answer]
    while len(options) < 4:
        # Generar opciones aleatorias que no sean la correcta y no estén duplicadas
        deviation = random.randint(-5, 5) # Pequeña desviación para las opciones
        # Asegurarse de que no genere números negativos para multiplicaciones.
        if correct_answer + deviation < 0:
            option = random.randint(correct_answer - 5, correct_answer + 5)
        else:
            option = correct_answer + deviation
        
        # Asegurarse de que la opción sea al menos 0 (para multiplicaciones)
        option = max(0, option)

        if option != correct_answer and option not in options:
            options.append(option)
    random.shuffle(options)
    return options

if __name__ == '__main__':
    app.run(debug=True)