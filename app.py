import random
import os # Se mantiene os para leer SECRET_KEY desde las variables de entorno
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

# Flask-SQLAlchemy y los modelos de la DB (models.py) ya NO se usarán en esta versión.
# Las funciones de manipulación de JSON (json, os.makedirs, etc.) tampoco.

app = Flask(__name__)

# Configuración de la clave secreta de Flask (leída de las variables de entorno)
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    # En desarrollo local, puedes establecer una por defecto o asegurar que .env la tenga.
    # En producción (Vercel), DEBES configurar SECRET_KEY en sus variables de entorno.
    print("ADVERTENCIA: SECRET_KEY no está configurada. Usando una por defecto (NO SEGURO PARA PRODUCCIÓN REAL).")
    app.secret_key = 'super_secreta_clave_por_defecto' # ¡Cámbiala en producción!
else:
    app.secret_key = secret_key

PROFILES = ['Paula', 'Sofia'] # Perfiles válidos

# Función para inicializar la estructura de progreso en memoria
def initialize_table_progress_in_memory():
    """Inicializa la estructura de progreso en memoria para todas las tablas (0-9)."""
    progress = {}
    for i in range(10): # Tablas del 0 al 9
        progress[str(i)] = {'correctas': 0, 'incorrectas': 0, 'detalles': []}
    return progress

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/select_profile', methods=['POST'])
def select_profile():
    profile = request.form.get('profile')
    if profile in PROFILES:
        session['current_profile'] = profile
        
        # El progreso persistente ahora es solo en memoria para la sesión actual
        session['persistent_profile_progress'] = initialize_table_progress_in_memory()
        print(f"DEBUG: Progreso inicializado en memoria para {profile}: {session['persistent_profile_progress']}")

        # Inicializar preguntas para la ronda de juego actual
        session['all_questions'] = generate_all_multiplications()
        random.shuffle(session['all_questions'])
        session['current_question_index'] = 0
        session['questions_answered'] = [None] * len(session['all_questions'])

        # Reiniciar los contadores de la ronda actual
        session['current_round_scores'] = {'correctas': 0, 'incorrectas': 0}

        return redirect(url_for('game'))
    return redirect(url_for('index'))

@app.route('/game')
def game():
    if 'current_profile' not in session:
        return redirect(url_for('index'))

    # Asegurarse de que las preguntas y el progreso en memoria estén inicializados
    if 'all_questions' not in session or not session.get('all_questions'):
        # Si no están, redirigir a select_profile para reinicializar la sesión
        return redirect(url_for('select_profile', _method='POST', profile=session['current_profile']))
    
    if 'persistent_profile_progress' not in session:
        # Esto debería haber sido inicializado en select_profile, pero como fallback
        session['persistent_profile_progress'] = initialize_table_progress_in_memory()

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
        print("DEBUG: No profile selected in session (submit_answer).")
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
    # Acceder al progreso en memoria de la sesión
    persistent_progress = session.get('persistent_profile_progress')

    if persistent_progress is None:
        # Fallback si el progreso no está en sesión (debería estar)
        print(f"ADVERTENCIA: persistent_profile_progress no encontrado en sesión para {profile}. Inicializando en memoria.")
        persistent_progress = initialize_table_progress_in_memory()
        session['persistent_profile_progress'] = persistent_progress
        session.modified = True


    # Determinar la tabla (como string para claves de diccionario)
    if num1 == 0 or num2 == 0:
        table_number = '0'
    else:
        table_number = str(max(num1, num2))

    # Asegurarse de que la tabla exista en la estructura de progreso
    if table_number not in persistent_progress:
        persistent_progress[table_number] = {'correctas': 0, 'incorrectas': 0, 'detalles': []}

    # Registrar detalle de multiplicación
    multiplication_detail = {
        'factores': [num1, num2],
        'correcta': (user_answer == correct_answer)
    }
    persistent_progress[table_number]['detalles'].append(multiplication_detail)

    # Actualizar contadores de la tabla
    if user_answer == correct_answer:
        session['questions_answered'][question_id] = True
        session['current_round_scores']['correctas'] += 1
        persistent_progress[table_number]['correctas'] += 1
    else:
        session['questions_answered'][question_id] = False
        session['current_round_scores']['incorrectas'] += 1
        persistent_progress[table_number]['incorrectas'] += 1
    
    # Es crucial para que Flask guarde los cambios en el diccionario de la sesión
    session.modified = True

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
    # Cargamos el progreso directamente de la sesión (es solo en memoria)
    progress_data = session.get('persistent_profile_progress', initialize_table_progress_in_memory())
    
    return render_template('progress.html', profile=profile, progress_data=progress_data)

@app.route('/progreso_detalle/<profile_name>/<int:table_num>')
def get_table_details(profile_name, table_num):
    if profile_name not in PROFILES:
        return jsonify({'error': 'Perfil no válido'}), 404
    
    if session.get('current_profile') != profile_name:
        return jsonify({'error': 'Acceso no autorizado al perfil'}), 403

    # Obtenemos el progreso de la sesión actual
    progress = session.get('persistent_profile_progress', initialize_table_progress_in_memory())
    
    table_details = progress.get(str(table_num), {'correctas': 0, 'incorrectas': 0, 'detalles': []})
    
    return jsonify(table_details)

# La ruta para reiniciar el progreso (borrado de ficheros/DB) YA NO ES NECESARIA.
# Si el usuario quiere "reiniciar", la acción más simple es que seleccione un nuevo perfil
# o inicie una nueva ronda, lo que reiniciará el progreso de la sesión.

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