// static/js/progress_modal.js

document.addEventListener('DOMContentLoaded', () => {
    const detailModal = document.getElementById('detailModal');
    const closeButton = document.querySelector('.close-button');
    const modalTableNumber = document.getElementById('modalTableNumber');
    const multiplicationList = document.getElementById('multiplicationList');
    const progressTable = document.querySelector('.progress-table');

    const currentProfileNameElement = document.getElementById('currentProfileName');
    const profileName = currentProfileNameElement ? currentProfileNameElement.value : null;

    console.log("PROGRESS_MODAL DEBUG: detailModal found:", detailModal);
    console.log("PROGRESS_MODAL DEBUG: closeButton found:", closeButton);
    console.log("PROGRESS_MODAL DEBUG: progressTable found:", progressTable);
    console.log("PROGRESS_MODAL DEBUG: currentProfileName (from HTML):", profileName);


    // Abrir el modal cuando se hace clic en un número de tabla
    if (progressTable && detailModal && modalTableNumber && multiplicationList && profileName) {
        progressTable.addEventListener('click', async (event) => {
            const clickedCell = event.target.closest('.clickable-table-num');
            if (clickedCell) {
                const tableNum = parseInt(clickedCell.textContent); // Obtener el número de la tabla (como número)
                
                modalTableNumber.textContent = tableNum; // Actualizar el título del modal

                try {
                    const response = await fetch(`/progreso_detalle/${profileName}/${tableNum}`);
                    if (!response.ok) {
                        const errorText = await response.text();
                        console.error('PROGRESS_MODAL ERROR: Error al obtener detalles de la tabla:', response.status, errorText);
                        multiplicationList.innerHTML = `<li>Error al cargar detalles.</li>`;
                        detailModal.style.display = 'flex'; // Mostrar el modal incluso con error
                        return;
                    }
                    const data = await response.json();
                    console.log(`PROGRESS_MODAL DEBUG: Datos recibidos para la tabla ${tableNum}:`, data);

                    multiplicationList.innerHTML = ''; // Limpiar lista anterior

                    const detailsMap = new Map(); // Para un acceso rápido a los detalles existentes
                    if (data.detalles) {
                        data.detalles.forEach(detail => {
                            // Usamos una clave única para cada multiplicación, por ejemplo "num1_num2"
                            detailsMap.set(`${detail.factores[0]}x${detail.factores[1]}`, detail.correcta);
                        });
                    }
                    
                    // Generar todas las 10 multiplicaciones para la tabla actual (0 a 9)
                    for (let i = 0; i < 10; i++) {
                        const num1 = tableNum;
                        const num2 = i;
                        const multiplicationKey = `${num1}x${num2}`;
                        const listItem = document.createElement('li');
                        const isDone = detailsMap.has(multiplicationKey);
                        const isCorrect = isDone ? detailsMap.get(multiplicationKey) : null; // null si no se ha hecho

                        let iconHtml = ''; // Inicializar vacío por defecto

                        if (isDone) {
                            if (isCorrect === true) { // Si es CORRECTA
                                iconHtml = '<i class="fas fa-check-circle result-icon correct-icon"></i>';
                            } else { // Si es INCORRECTA
                                iconHtml = '<i class="fas fa-times-circle result-icon incorrect-icon"></i>';
                            }
                        }
                        // Si !isDone, iconHtml permanece vacío, como se desea

                        listItem.innerHTML = `
                            <span class="multiplication-text-detail">${num1} x ${num2} = ${num1 * num2}</span>
                            <span>${iconHtml}</span>
                        `;
                        multiplicationList.appendChild(listItem);
                    }

                    detailModal.style.display = 'flex'; // Mostrar el modal

                } catch (error) {
                    console.error('PROGRESS_MODAL ERROR: Error fetching table details:', error);
                    multiplicationList.innerHTML = `<li>Error de conexión.</li>`;
                    detailModal.style.display = 'flex'; // Mostrar el modal incluso con error
                }
            }
        });
    } else {
        console.warn("PROGRESS_MODAL WARNING: Elementos del modal o nombre de perfil no encontrados. Posiblemente no estamos en la página de progreso o hay un error.");
    }


    // Cerrar el modal cuando se hace clic en la X
    if (closeButton && detailModal) {
        closeButton.addEventListener('click', () => {
            detailModal.style.display = 'none';
            console.log("PROGRESS_MODAL DEBUG: Modal closed by close button.");
        });
    }

    // Cerrar el modal cuando se hace clic fuera de él
    if (detailModal) {
        window.addEventListener('click', (event) => {
            if (event.target == detailModal) {
                detailModal.style.display = 'none';
                console.log("PROGRESS_MODAL DEBUG: Modal closed by clicking outside.");
            }
        });
    }
});