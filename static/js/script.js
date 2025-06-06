// static/js/script.js

document.addEventListener('DOMContentLoaded', () => {
    // ... (código existente para el juego, feedback, sonidos) ...
    const optionsGrid = document.getElementById('options-grid');
    const feedbackMessage = document.getElementById('feedback-message');
    const correctSound = document.getElementById('correctSound');
    const incorrectSound = document.getElementById('incorrectSound');

    const playSound = (audioElement) => {
        if (audioElement) {
            audioElement.currentTime = 0;
            audioElement.play().catch(e => console.error("Error playing sound:", e));
        }
    };

    if (optionsGrid) { // Lógica solo si estamos en la página del juego
        optionsGrid.addEventListener('click', async (event) => {
            const clickedButton = event.target.closest('.option-btn');

            if (clickedButton) {
                Array.from(optionsGrid.children).forEach(button => {
                    button.disabled = true;
                });

                const userAnswer = parseInt(clickedButton.dataset.answer);
                const correctAnswer = parseInt(document.getElementById('correct_answer').value);
                const questionId = parseInt(document.getElementById('question_id').value);
                const num1Element = document.getElementById('num1');
                const num2Element = document.getElementById('num2');
                const num1 = num1Element && num1Element.value ? parseInt(num1Element.value) : null;
                const num2 = num2Element && num2Element.value ? parseInt(num2Element.value) : null;

                console.log("JS DEBUG: User answered:", userAnswer, "Correct:", correctAnswer, "QID:", questionId, "Num1 (from JS):", num1, "Num2 (from JS):", num2); 

                let isCorrect;
                if (userAnswer === correctAnswer) {
                    isCorrect = true;
                    feedbackMessage.textContent = '¡Correcto!';
                    feedbackMessage.style.backgroundColor = '#32CD32';
                    clickedButton.style.border = '3px solid #32CD32';
                    playSound(correctSound);
                } else {
                    isCorrect = false;
                    feedbackMessage.textContent = '¡Incorrecto!';
                    feedbackMessage.style.backgroundColor = '#FF6347';
                    clickedButton.style.border = '3px solid #FF6347'; 
                    playSound(incorrectSound);

                    Array.from(optionsGrid.children).forEach(button => {
                        if (parseInt(button.dataset.answer) === correctAnswer) {
                            button.style.border = '3px solid #FFD700'; 
                        }
                    });
                }

                feedbackMessage.style.display = 'block'; 

                try {
                    const response = await fetch('/submit_answer', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            answer: userAnswer,
                            correct_answer: correctAnswer,
                            question_id: questionId,
                            num1: num1,
                            num2: num2  
                        }),
                    });

                    if (!response.ok) { 
                        const errorText = await response.text();
                        console.error('JS ERROR: Server responded with non-OK status:', response.status, errorText);
                        feedbackMessage.textContent = 'Error: No se pudo avanzar.';
                        feedbackMessage.style.backgroundColor = 'orange'; 
                        return;
                    }

                    const data = await response.json();
                    console.log("JS DEBUG: Server response:", data); 

                    setTimeout(() => {
                        feedbackMessage.style.display = 'none';

                        if (data.redirect_to_results) {
                            window.location.href = data.redirect_to_results;
                        } else if (data.next_question) {
                            updateGameContent(data.next_question);
                            Array.from(optionsGrid.children).forEach(button => {
                                button.disabled = false;
                                button.style.border = 'none';
                            });
                        } else {
                             console.error("JS ERROR: Server response does not contain next_question or redirect_to_results:", data);
                             feedbackMessage.textContent = 'Error: Respuesta inesperada del servidor.';
                             feedbackMessage.style.backgroundColor = 'orange';
                        }
                    }, 1500); 

                } catch (error) {
                    console.error('JS ERROR: Error sending answer to server:', error);
                    feedbackMessage.textContent = 'Error de conexión. Intenta de nuevo.';
                    feedbackMessage.style.backgroundColor = 'orange';
                    Array.from(optionsGrid.children).forEach(button => {
                        button.disabled = false;
                        button.style.border = 'none';
                    });
                }
            }
        });
    }

    function updateGameContent(nextQuestion) {
        if (!nextQuestion) {
            console.warn("JS WARNING: updateGameContent called with no nextQuestion data.");
            return;
        }
        document.getElementById('num1-display').textContent = nextQuestion.num1;
        document.getElementById('num2-display').textContent = nextQuestion.num2;
        optionsGrid.innerHTML = '';
        nextQuestion.options.forEach((option, index) => {
            const button = document.createElement('button');
            button.classList.add('btn', 'option-btn', `option-color-${(index % 4) + 1}`);
            button.dataset.answer = option;
            button.textContent = option;
            optionsGrid.appendChild(button);
        });
        document.getElementById('correct_answer').value = nextQuestion.correct_answer;
        document.getElementById('question_id').value = nextQuestion.question_id;
        document.getElementById('num1').value = nextQuestion.num1; 
        document.getElementById('num2').value = nextQuestion.num2; 
        console.log("JS DEBUG: Game content updated. New num1:", nextQuestion.num1, "New num2:", nextQuestion.num2);
    }
	
	
	/*
    // --- Lógica NUEVA para el MODAL de Progreso ---
    const detailModal = document.getElementById('detailModal');
    const closeButton = document.querySelector('.close-button');
    const modalTableNumber = document.getElementById('modalTableNumber');
    const multiplicationList = document.getElementById('multiplicationList');
    const progressTable = document.querySelector('.progress-table'); // La tabla de progreso

	    // Debugging: Comprobar si los elementos se encuentran
    console.log("JS DEBUG: detailModal found:", detailModal); //debug
    console.log("JS DEBUG: closeButton found:", closeButton); //debug

    // Abrir el modal cuando se hace clic en un número de tabla
    if (progressTable) { // Solo si estamos en la página de progreso
        progressTable.addEventListener('click', async (event) => {
            const clickedCell = event.target.closest('.clickable-table-num');
            if (clickedCell) {
                const tableNum = clickedCell.textContent; // Obtener el número de la tabla
                const profileName = "{{ profile }}"; // Obtener el nombre del perfil de Jinja (Flask)

                modalTableNumber.textContent = tableNum; // Actualizar el título del modal

                try {
                    const response = await fetch(`/progreso_detalle/${profileName}/${tableNum}`);
                    if (!response.ok) {
                        const errorText = await response.text();
                        console.error('Error al obtener detalles de la tabla:', response.status, errorText);
                        multiplicationList.innerHTML = `<li>Error al cargar detalles.</li>`;
                        return;
                    }
                    const data = await response.json();
                    console.log(`DEBUG: Detalles de la tabla ${tableNum}:`, data);

                    multiplicationList.innerHTML = ''; // Limpiar lista anterior

                    if (data.detalles && data.detalles.length > 0) {
                        data.detalles.forEach(detail => {
                            const listItem = document.createElement('li');
                            const correctClass = detail.correcta ? 'correct-detail' : 'incorrect-detail';
                            const checkIcon = detail.correcta ? '<i class="fas fa-check-circle correct-detail"></i>' : '<i class="fas fa-times-circle incorrect-detail"></i>';

                            listItem.innerHTML = `
                                <span class="multiplication-text-detail">${detail.factores[0]} x ${detail.factores[1]} = ${detail.factores[0] * detail.factores[1]}</span>
                                <span class="${correctClass}">${checkIcon}</span>
                            `;
                            multiplicationList.appendChild(listItem);
                        });
                    } else {
                        multiplicationList.innerHTML = '<li>No hay detalles aún para esta tabla. ¡Sigue practicando!</li>';
                    }

                    detailModal.style.display = 'flex'; // Mostrar el modal

                } catch (error) {
                    console.error('Error fetching table details:', error);
                    multiplicationList.innerHTML = `<li>Error de conexión.</li>`;
                    detailModal.style.display = 'flex'; // Mostrar el modal incluso con error
                }
            }
        });
    }

    // Cerrar el modal cuando se hace clic en la X
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            detailModal.style.display = 'none';
			 console.log("JS DEBUG: Modal closed by close button."); // Debug
        });
    }

    // Cerrar el modal cuando se hace clic fuera de él
    if (detailModal) {
        window.addEventListener('click', (event) => {
            if (event.target == detailModal) {
                detailModal.style.display = 'none';
				console.log("JS DEBUG: Modal closed by clicking outside."); // Debug
            }
        });
    }
    // --- FIN Lógica NUEVA para el MODAL de Progreso ---
	*/
});