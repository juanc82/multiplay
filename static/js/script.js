// static/js/script.js

document.addEventListener('DOMContentLoaded', () => {
    const optionsGrid = document.getElementById('options-grid');
    const feedbackMessage = document.getElementById('feedback-message');
    const gameContent = document.getElementById('game-content');

    // Obtener referencias a los elementos de audio
    const correctSound = document.getElementById('correctSound');
    const incorrectSound = document.getElementById('incorrectSound');

    if (optionsGrid) {
        optionsGrid.addEventListener('click', async (event) => {
            const clickedButton = event.target.closest('.option-btn');

            if (clickedButton) {
                // Deshabilitar todos los botones de opción para evitar clics múltiples
                Array.from(optionsGrid.children).forEach(button => {
                    button.disabled = true;
                });

                const userAnswer = parseInt(clickedButton.dataset.answer);
                const correctAnswer = parseInt(document.getElementById('correct_answer').value);
                const questionId = parseInt(document.getElementById('question_id').value);

                let isCorrect;
                if (userAnswer === correctAnswer) {
                    isCorrect = true;
                    feedbackMessage.textContent = '¡Correcto!';
                    feedbackMessage.style.backgroundColor = '#32CD32'; // Verde
                    clickedButton.style.border = '3px solid #32CD32'; // Resaltar el botón correcto
                    if (correctSound) {
                        correctSound.currentTime = 0; // Reiniciar el sonido por si se reproduce rápido
                        correctSound.play();
                    }
                } else {
                    isCorrect = false;
                    feedbackMessage.textContent = '¡Incorrecto!';
                    feedbackMessage.style.backgroundColor = '#FF6347'; // Rojo
                    clickedButton.style.border = '3px solid #FF6347'; // Resaltar el botón incorrecto

                    if (incorrectSound) {
                        incorrectSound.currentTime = 0; // Reiniciar el sonido
                        incorrectSound.play();
                    }

                    // Opcional: Resaltar la respuesta correcta si se equivocó
                    Array.from(optionsGrid.children).forEach(button => {
                        if (parseInt(button.dataset.answer) === correctAnswer) {
                            button.style.border = '3px solid #FFD700'; // Dorado para la correcta
                        }
                    });
                }

                feedbackMessage.style.display = 'block'; // Mostrar el mensaje de feedback

                // Enviar la respuesta al servidor Flask
                const response = await fetch('/submit_answer', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        answer: userAnswer,
                        correct_answer: correctAnswer,
                        question_id: questionId
                    }),
                });

                const data = await response.json();

                // Esperar un poco antes de pasar a la siguiente pregunta
                setTimeout(() => {
                    feedbackMessage.style.display = 'none'; // Ocultar el mensaje

                    if (data.redirect_to_results) {
                        window.location.href = data.redirect_to_results; // Redirigir a resultados
                    } else {
                        // Cargar la siguiente pregunta
                        updateGameContent(data.next_question);
                        // Habilitar los botones de nuevo y quitar resaltados
                        Array.from(optionsGrid.children).forEach(button => {
                            button.disabled = false;
                            button.style.border = 'none'; // Quitar el borde de resaltado
                        });
                    }
                }, 1500); // 1.5 segundos de retraso
            }
        });
    }

    function updateGameContent(nextQuestion) {
        if (!nextQuestion) {
            return;
        }
        
        // Actualizar la pregunta
        document.getElementById('num1').textContent = nextQuestion.num1;
        document.getElementById('num2').textContent = nextQuestion.num2;
        
        // Actualizar las opciones
        optionsGrid.innerHTML = ''; // Limpiar opciones anteriores
        nextQuestion.options.forEach((option, index) => {
            const button = document.createElement('button');
            button.classList.add('btn', 'option-btn', `option-color-${(index % 4) + 1}`);
            button.dataset.answer = option;
            button.textContent = option;
            optionsGrid.appendChild(button);
        });

        // Actualizar los valores ocultos
        document.getElementById('correct_answer').value = nextQuestion.correct_answer;
        document.getElementById('question_id').value = nextQuestion.question_id;
    }
});