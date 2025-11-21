document.addEventListener('DOMContentLoaded', () => {
    // Elementos
    const modal = document.getElementById('booking-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalRecap = document.getElementById('modal-recap');
    const bookingForm = document.getElementById('booking-form');
    const dateSelector = document.getElementById('date-selector');
    const horariosGrid = document.getElementById('horarios-grid');
    const inputTelefone = document.getElementById('modal-telefone'); // Novo seletor

    const horariosFuncionamento = [
        "09:00", "10:00", "11:00", "12:00",
        "14:00", "15:00", "16:00", "17:00", "18:00"
    ];
    let slotSelecionado = { data: null, horario: null };

    // --- 1. SISTEMA DE NOTIFICAÇÃO (TOAST) ---
    function showToast(mensagem, tipo = 'success') {
        // Cria o container se não existir
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast ${tipo}`;
        toast.innerText = mensagem;

        container.appendChild(toast);

        // Animação de entrada
        setTimeout(() => toast.classList.add('show'), 10);

        // Remove depois de 4 segundos
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // --- 2. MÁSCARA DE TELEFONE (Input Mask) ---
    // Formata: (XX) XXXXX-XXXX
    inputTelefone.addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, ''); // Remove tudo que não é número

        if (value.length > 11) value = value.slice(0, 11); // Limita tamanho

        if (value.length > 6) {
            value = `(${value.slice(0,2)}) ${value.slice(2,7)}-${value.slice(7)}`;
        } else if (value.length > 2) {
            value = `(${value.slice(0,2)}) ${value.slice(2)}`;
        }

        e.target.value = value;
    });

    // --- FUNÇÕES DO MODAL ---
    function abrirModal(data, horario) {
        slotSelecionado.data = data;
        slotSelecionado.horario = horario;
        const dataFormatada = data.split('-').reverse().join('/');
        modalRecap.innerText = `Agendando para: ${dataFormatada} às ${horario}`;
        modal.classList.add('show');
    }

    function fecharModal() {
        modal.classList.remove('show');
        bookingForm.reset();
    }

    // --- COMUNICAÇÃO COM PYTHON ---
    bookingForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const nome = document.getElementById('modal-nome').value;
        const telefone = document.getElementById('modal-telefone').value;

        // Validação extra no Frontend antes de enviar
        if(telefone.length < 14) { // (XX) XXXXX-XXXX tem 15 chars ou (XX) XXXX-XXXX tem 14
            showToast('Por favor, digite um telefone válido.', 'error');
            return;
        }

        const payload = {
            data: slotSelecionado.data,
            horario: slotSelecionado.horario,
            nome: nome,
            telefone: telefone
        };

        try {
            const response = await fetch('/agendar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (result.sucesso) {
                showToast(`Agendamento Confirmado, ${nome.split(' ')[0]}!`, 'success');
                fecharModal();
                carregarHorarios(slotSelecionado.data);
            } else {
                showToast(result.mensagem, 'error');
            }
        } catch (error) {
            showToast('Erro de conexão com o servidor.', 'error');
        }
    });

    async function carregarHorarios(dataSelecionada) {
        horariosGrid.innerHTML = '<p style="color:gray">Verificando disponibilidade...</p>';
        try {
            const response = await fetch(`/api/horarios/${dataSelecionada}`);
            const dados = await response.json();
            renderizarGrid(dataSelecionada, dados.ocupados || []);
        } catch (error) {
            horariosGrid.innerHTML = '<p style="color:red">Erro ao carregar.</p>';
        }
    }

    function renderizarGrid(dataSelecionada, listaOcupados) {
        horariosGrid.innerHTML = '';

        // Pega data e hora atuais do computador do usuário
        const agora = new Date();
        const dataAtualStr = agora.toLocaleDateString('en-CA'); // Formato YYYY-MM-DD igual ao do input
        const horaAtual = agora.getHours();
        const minutoAtual = agora.getMinutes();

        // Verifica se o usuário está vendo a agenda de "Hoje"
        const isHoje = (dataSelecionada === dataAtualStr);

        horariosFuncionamento.forEach(horario => {
            const btn = document.createElement('button');
            btn.classList.add('horario-slot');
            btn.innerText = horario;

            // Extrai a hora do botão (Ex: "09:00" -> 9)
            const [horaBtnStr, minutoBtnStr] = horario.split(':');
            const horaBtn = parseInt(horaBtnStr);
            const minutoBtn = parseInt(minutoBtnStr);

            let bloqueado = false;

            // 1. Bloqueia se estiver na lista de ocupados (Hash)
            if (listaOcupados.includes(horario)) {
                bloqueado = true;
            }

            // 2. Bloqueia se for Hoje E o horário já passou
            if (isHoje) {
                // Ex: Se agora são 14:00, bloqueia 09, 10, 11, 12...
                // Se for 14:30, bloqueia o botão das 14:00 também
                if (horaBtn < horaAtual || (horaBtn === horaAtual && minutoBtn < minutoAtual)) {
                    bloqueado = true;
                }
            }

            if (bloqueado) {
                btn.classList.add('ocupado');
                btn.disabled = true;
                btn.title = "Indisponível";
            } else {
                btn.classList.add('livre');
                btn.onclick = () => abrirModal(dataSelecionada, horario);
            }

            horariosGrid.appendChild(btn);
        });
    }

    // --- INICIALIZAÇÃO ---
    if (dateSelector) {
        const hojeObj = new Date();
        const hojeStr = hojeObj.toLocaleDateString('en-CA'); // YYYY-MM-DD

        // Calcula data máxima (Hoje + 1 Mês)
        const maxObj = new Date();
        maxObj.setMonth(maxObj.getMonth() + 1);
        const maxStr = maxObj.toLocaleDateString('en-CA');

        dateSelector.value = hojeStr;
        dateSelector.min = hojeStr;
        dateSelector.max = maxStr; // AQUI A MÁGICA: Bloqueia o calendário

        dateSelector.addEventListener('change', (e) => carregarHorarios(e.target.value));
        carregarHorarios(hojeStr);
    }

    // --- CÓDIGO DO SLIDER (Mantido igual) ---
    const slides = document.querySelectorAll('.slide');
    const nextBtn = document.getElementById('slide-next');
    const prevBtn = document.getElementById('slide-prev');
    const dotsContainer = document.getElementById('slider-dots');

    if(slides.length > 0) {
        let currentSlide = 0;
        let slideInterval;

        function createDots() {
            slides.forEach((_, index) => {
                const dot = document.createElement('button');
                dot.classList.add('slider-dot');
                if (index === 0) dot.classList.add('active');
                dot.addEventListener('click', () => {
                    goToSlide(index);
                    resetInterval();
                });
                dotsContainer.appendChild(dot);
            });
        }

        function goToSlide(index) {
            slides[currentSlide].classList.remove('active');
            document.querySelectorAll('.slider-dot')[currentSlide].classList.remove('active');
            currentSlide = index;
            slides[currentSlide].classList.add('active');
            document.querySelectorAll('.slider-dot')[currentSlide].classList.add('active');
        }

        function nextSlide() {
            let newSlide = (currentSlide + 1) % slides.length;
            goToSlide(newSlide);
        }

        function prevSlide() {
            let newSlide = (currentSlide - 1 + slides.length) % slides.length;
            goToSlide(newSlide);
        }

        function startInterval() { slideInterval = setInterval(nextSlide, 5000); }
        function resetInterval() { clearInterval(slideInterval); startInterval(); }

        nextBtn.addEventListener('click', () => { nextSlide(); resetInterval(); });
        prevBtn.addEventListener('click', () => { prevSlide(); resetInterval(); });

        createDots();
        startInterval();
    }
});