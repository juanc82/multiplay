import random
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Ruta donde se guardarán los archivos de progreso
DATA_FOLDER = 'data'
if not os.path.exists(DATA_FOLDER):
    try:
        os.makedirs(DATA_FOLDER)
        print(f"DEBUG: Carpeta de datos '{DATA_FOLDER}' creada en: {os.path.abspath(DATA_FOLDER)}")
    except OSError as e:
        print(f"ERROR: No se pudo crear la carpeta de datos '{DATA_FOLDER}'. Motivo: {e}")
        raise

PROFILES = ['Paula', 'Sofia']

def get_progress_file_path(profile_name):
    return os.path.join(DATA_FOLDER, f"{profile_name.lower()}_progress.json")

# --- MODIFICADO: initialize_table_progress para incluir "detalles" ---
def initialize_table_progress():
    progress = {}
    for i in range(10):
        progress[str(i)] = {'correctas': 0, 'incorrectas': 0, 'detalles': []}
    return progress

def load_profile_progress(profile_name):
    file_path = get_progress_file_path(profile_name)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Asegurarse de que "detalles" exista para tablas antiguas sin él
                for i in range(10):
                    tabla_str = str(i)
                    if tabla_str in data and 'detalles' not in data[tabla_str]:
                        data[tabla_str]['detalles'] = []
                return data
        except json.JSONDecodeError as e:
            print(f"ADVERTENCIA: Error al leer el archivo JSON para '{profile_name}': {e}. Se inicializará el progreso.")
            return initialize_table_progress()
    else:
        print(f"DEBUG: No se encontró archivo de progreso para '{profile_name}'. Inicializando nuevo progreso.")
        return initialize_table_progress()

def save_profile_progress(profile_name, progress_data):
    file_path = get_progress_file_path(profile_name)
    try:
        with open(file_path, 'w') as f:
            json.dump(progress_data, f, indent=4)
        print(f"DEBUG: Progreso guardado con éxito para '{profile_name}' en {file_path}")
    except Exception as e:
        print(f"ERROR: Fallo al guardar el progreso para '{profile_name}' en {file_path}. Error: {e}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/select_profile', methods=['POST'])
def select_profile():
    profile = request.form.get('profile')
    if profile in PROFILES:
        session['current_profile'] = profile
        session['persistent_profile_progress'] = load_profile_progress(profile)
        session['all_questions'] = generate_all_multiplications()
        random.shuffle(session['all_questions'])
        session['current_question_index'] = 0
        session['questions_answered'] = [None] * len(session['all_questions'])
        session['current_round_scores'] = {'correctas': 0, 'incorrectas': 0}
        return redirect(url_for('game'))
    return redirect(url_for('index'))

@app.route('/game')
def game():
    if 'current_profile' not in session:
        return redirect(url_for('index'))
    if 'all_questions' not in session or not session.get('all_questions'):
        return redirect(url_for('select_profile', _method='POST', profile=session['current_profile']))
    if 'persistent_profile_progress' not in session:
        session['persistent_profile_progress'] = load_profile_progress(session['current_profile'])

    current_question_data = get_next_question_data()

    if not current_question_data:
        return redirect(url_for('results'))

    return render_template('game.html',
                           profile=session['current_profile'],
                           num1=current_question_data['num1'],
                           num2=current_question_data['num2'],
                           options=current_question_data['options'],
                           correct_answer=current_question_data['correct_answer'],
                           question_id=current_question_data['question_id'])

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if 'current_profile' not in session:
        return jsonify({'error': 'No profile selected'}), 401

    data = request.get_json()
    user_answer = data.get('answer')
    correct_answer = data.get('correct_answer')
    question_id = data.get('question_id')
    num1 = data.get('num1')
    num2 = data.get('num2')

    if num1 is None or num2 is None:
        print(f"ERROR: num1 or num2 is None. num1={num1}, num2={num2}. Check frontend sending.")
        return jsonify({'error': 'Missing or invalid num1/num2 data'}), 400

    profile = session['current_profile']
    persistent_progress = session.get('persistent_profile_progress')

    if persistent_progress is None:
        persistent_progress = load_profile_progress(profile)
        session['persistent_profile_progress'] = persistent_progress
        session.modified = True

    if num1 == 0 or num2 == 0:
        table_number = '0'
    else:
        table_number = str(max(num1, num2))

    # --- MODIFICADO: Actualizar detalles de la multiplicación ---
    # Asegurarse de que la tabla exista en el progreso
    if table_number not in persistent_progress:
        persistent_progress[table_number] = {'correctas': 0, 'incorrectas': 0, 'detalles': []}

    multiplication_detail = {
        'factores': [num1, num2],
        'correcta': (user_answer == correct_answer)
    }
    persistent_progress[table_number]['detalles'].append(multiplication_detail)
    # --- FIN MODIFICADO ---

    if user_answer == correct_answer:
        session['questions_answered'][question_id] = True
        session['current_round_scores']['correctas'] += 1
        persistent_progress[table_number]['correctas'] += 1
    else:
        session['questions_answered'][question_id] = False
        session['current_round_scores']['incorrectas'] += 1
        persistent_progress[table_number]['incorrectas'] += 1
    
    session.modified = True # Crucial para que Flask guarde los cambios en la sesión
    save_profile_progress(profile, persistent_progress)

    next_question_data = get_next_question_data()

    if not next_question_data:
        return jsonify({'redirect_to_results': url_for('results')})
    else:
        return jsonify({'next_question': next_question_data})


def get_next_question_data():
    if 'all_questions' not in session or 'questions_answered' not in session:
        return None
    current_question_index = session.get('current_question_index', 0)
    all_questions = session['all_questions']
    questions_answered = session['questions_answered']
    next_q = None
    next_q_id = current_question_index
    while next_q_id < len(all_questions):
        if questions_answered[next_q_id] is None:
            next_q = all_questions[next_q_id]
            break
        next_q_id += 1
    session['current_question_index'] = next_q_id
    if not next_q:
        return None
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
    current_round_scores = session.get('current_round_scores', {'correctas': 0, 'incorrectas': 0})
    correctas = current_round_scores['correctas']
    incorrectas = current_round_scores['incorrectas']
    total_preguntas = correctas + incorrectas
    session.pop('all_questions', None)
    session.pop('current_question_index', None)
    session.pop('questions_answered', None)
    session.pop('current_round_scores', None)
    return render_template('results.html',
                           profile=session['current_profile'],
                           correctas=correctas,
                           incorrectas=incorrectas,
                           total_preguntas=total_preguntas)

@app.route('/progreso')
def show_progress():
    if 'current_profile' not in session:
        return redirect(url_for('index'))
    profile = session['current_profile']
    progress_data = load_profile_progress(profile)
    session['persistent_profile_progress'] = progress_data
    session.modified = True
    return render_template('progress.html', profile=profile, progress_data=progress_data)

# --- NUEVA RUTA para obtener detalles de tabla ---
@app.route('/progreso_detalle/<profile_name>/<int:table_num>')
def get_table_details(profile_name, table_num):
    if profile_name not in PROFILES:
        return jsonify({'error': 'Perfil no válido'}), 404
    
    # Asegúrate de que el usuario actual esté autorizado a ver este perfil
    if session.get('current_profile') != profile_name:
        # Esto podría ser una redirección a la página de inicio o un error de autorización
        return jsonify({'error': 'Acceso no autorizado al perfil'}), 403

    progress = load_profile_progress(profile_name)
    
    # Asegúrate de que la tabla exista en el progreso
    table_details = progress.get(str(table_num), {'correctas': 0, 'incorrectas': 0, 'detalles': []})
    
    return jsonify(table_details)
# --- FIN NUEVA RUTA ---


def generate_all_multiplications():
    questions = []
    for i in range(10): # Tablas del 0 al 9
        for j in range(10):
            questions.append({'factors': (i, j)})
    return questions

def generate_options(correct_answer):
    options = [correct_answer]
    while len(options) < 4:
        deviation = random.randint(-5, 5)
        option = correct_answer + deviation
        option = max(0, option)
        if option != correct_answer and option not in options:
            options.append(option)
    random.shuffle(options)
    return options

if __name__ == '__main__':
    app.run(debug=True)