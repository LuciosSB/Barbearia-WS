document.addEventListener('DOMContentLoaded', () => {
    // =========================================
    // 1. ELEMENTOS E CONFIGURAÇÕES
    // =========================================
    const modal = document.getElementById('booking-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalRecap = document.getElementById('modal-recap');
    const bookingForm = document.getElementById('booking-form');
    const dateSelector = document.getElementById('date-selector');
    const horariosGrid = document.getElementById('horarios-grid');
    const inputTelefone = document.getElementById('modal-telefone');

    let slotSelecionado = { data: null, horario: null };

    // =========================================
    // 2. SISTEMA DE NOTIFICAÇÃO (TOAST)
    // =========================================
    function showToast(mensagem, tipo = 'success') {
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
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // =========================================
    // 3. MÁSCARA DE TELEFONE
    // =========================================
    if (inputTelefone) {
        inputTelefone.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 11) value = value.slice(0, 11);

            if (value.length > 6) {
                value = `(${value.slice(0, 2)}) ${value.slice(2, 7)}-${value.slice(7)}`;
            } else if (value.length > 2) {
                value = `(${value.slice(0, 2)}) ${value.slice(2)}`;
            }
            e.target.value = value;
        });
    }

    // =========================================
    // 4. LÓGICA DO MODAL DE AGENDAMENTO
    // =========================================
    window.abrirModal = function(data, horario) {
        slotSelecionado.data = data;
        slotSelecionado.horario = horario;
        const dataFormatada = data.split('-').reverse().join('/');

        if(modalRecap) modalRecap.innerText = `Agendando para: ${dataFormatada} às ${horario}`;
        if(modal) modal.classList.add('show');
    };

    function fecharModal() {
        if(modal) modal.classList.remove('show');
        if(bookingForm) bookingForm.reset();
    }

    if (modalCloseBtn) modalCloseBtn.addEventListener('click', fecharModal);

    if (bookingForm) {
        bookingForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const nome = document.getElementById('modal-nome').value;
            const telefone = document.getElementById('modal-telefone').value;
            const observacoes = document.getElementById('modal-obs').value;

            if (telefone.length < 14) {
                showToast('Por favor, digite um telefone válido.', 'error');
                return;
            }

            const payload = {
                data: slotSelecionado.data,
                horario: slotSelecionado.horario,
                nome: nome,
                telefone: telefone,
                observacoes: observacoes
            };

            try {
                const response = await fetch('/agendar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await response.json();

                if (result.sucesso) {
                    showToast(`Agendamento Confirmado!`, 'success');
                    fecharModal();
                    carregarHorarios(slotSelecionado.data);
                } else {
                    showToast(result.mensagem, 'error');
                }
            } catch (error) {
                showToast('Erro de conexão com o servidor.', 'error');
            }
        });
    }

    // =========================================
    // 5. GRID DE HORÁRIOS (INTELIGENTE)
    // =========================================
    async function carregarHorarios(dataSelecionada) {
        if(!horariosGrid) return;
        horariosGrid.innerHTML = '<p style="color:gray">Verificando agenda...</p>';
        try {
            const response = await fetch(`/api/horarios/${dataSelecionada}`);
            const dados = await response.json();

            const slotsDoDia = dados.slots || [];
            const ocupados = dados.ocupados || [];

            if (slotsDoDia.length === 0) {
                horariosGrid.innerHTML = '<p style="color:#dc143c; grid-column: 1/-1; text-align:center;">Não abrimos neste dia.</p>';
                return;
            }

            renderizarGrid(dataSelecionada, slotsDoDia, ocupados);
        } catch (error) {
            horariosGrid.innerHTML = '<p style="color:red">Erro ao carregar.</p>';
        }
    }

    function renderizarGrid(dataSelecionada, slotsPossiveis, listaOcupados) {
        if(!horariosGrid) return;
        horariosGrid.innerHTML = '';

        const agora = new Date();
        const ano = agora.getFullYear();
        const mes = String(agora.getMonth() + 1).padStart(2, '0');
        const dia = String(agora.getDate()).padStart(2, '0');
        const dataAtualStr = `${ano}-${mes}-${dia}`;
        const horaAtual = agora.getHours();
        const minutoAtual = agora.getMinutes();
        const isHoje = (dataSelecionada === dataAtualStr);

        slotsPossiveis.forEach(horario => {
            const btn = document.createElement('button');
            btn.classList.add('horario-slot');
            btn.innerText = horario;
            const [horaBtnStr, minutoBtnStr] = horario.split(':');
            const horaBtn = parseInt(horaBtnStr);
            const minutoBtn = parseInt(minutoBtnStr);
            let bloqueado = false;
            if (listaOcupados.includes(horario)) bloqueado = true;
            if (isHoje) {
                if (horaBtn < horaAtual || (horaBtn === horaAtual)) {
                    bloqueado = true;
                }
            }
            if (bloqueado) {
                btn.classList.add('ocupado');
                btn.disabled = true;
            } else {
                btn.classList.add('livre');
                btn.onclick = () => window.abrirModal(dataSelecionada, horario);
            }
            horariosGrid.appendChild(btn);
        });
    }

    if (dateSelector) {
        const hojeObj = new Date();
        const ano = hojeObj.getFullYear();
        const mes = String(hojeObj.getMonth() + 1).padStart(2, '0');
        const dia = String(hojeObj.getDate()).padStart(2, '0');
        const hojeStr = `${ano}-${mes}-${dia}`;
        const maxObj = new Date();
        maxObj.setMonth(maxObj.getMonth() + 1);
        const maxStr = maxObj.toISOString().split('T')[0];
        dateSelector.value = hojeStr;
        dateSelector.min = hojeStr;
        dateSelector.max = maxStr;
        dateSelector.addEventListener('change', (e) => carregarHorarios(e.target.value));
        carregarHorarios(hojeStr);
    }

    // =========================================
    // 6. SLIDER COM SWIPE
    // =========================================
    const slides = document.querySelectorAll('.slide');
    const nextBtn = document.getElementById('slide-next');
    const prevBtn = document.getElementById('slide-prev');
    const dotsContainer = document.getElementById('slider-dots');

    if (slides.length > 0) {
        let currentSlide = 0;
        let slideInterval;
        function createDots() {
            if(!dotsContainer) return;
            dotsContainer.innerHTML = '';
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
            const dots = document.querySelectorAll('.slider-dot');
            if(dots[currentSlide]) dots[currentSlide].classList.remove('active');
            currentSlide = index;
            slides[currentSlide].classList.add('active');
            if(dots[currentSlide]) dots[currentSlide].classList.add('active');
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

        if(nextBtn) nextBtn.addEventListener('click', () => { nextSlide(); resetInterval(); });
        if(prevBtn) prevBtn.addEventListener('click', () => { prevSlide(); resetInterval(); });

        let touchStartX = 0;
        let touchEndX = 0;
        const sliderContainer = document.querySelector('.slider');
        if (sliderContainer) {
            sliderContainer.addEventListener('touchstart', (e) => {
                touchStartX = e.changedTouches[0].screenX;
            }, {passive: true});
            sliderContainer.addEventListener('touchend', (e) => {
                touchEndX = e.changedTouches[0].screenX;
                handleSwipe();
            }, {passive: true});
        }

        function handleSwipe() {
            const diff = touchStartX - touchEndX;
            const threshold = 50;
            if (Math.abs(diff) > threshold) {
                if (diff > 0) nextSlide(); else prevSlide();
                resetInterval();
            }
        }
        createDots();
        startInterval();
    }

    // =========================================
    // 7. MENU MOBILE
    // =========================================
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const navLinks = document.getElementById('nav-links');
    if (hamburgerBtn && navLinks) {
        hamburgerBtn.addEventListener('click', () => {
            hamburgerBtn.classList.toggle('active');
            navLinks.classList.toggle('active');
        });
    }
});

// =========================================
// 8. FUNÇÕES GLOBAIS (FORA DO DOMContentLoaded)
// =========================================

window.fecharMenu = function() {
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const navLinks = document.getElementById('nav-links');
    if (hamburgerBtn && navLinks) {
        hamburgerBtn.classList.remove('active');
        navLinks.classList.remove('active');
    }
};

window.comprar = function(produto) {
    const telefoneBarbearia = "5582987126184";

    const texto = `Olá! Gostaria de comprar o produto: *${produto}*. Como faço para retirar?`;
    const url = `https://wa.me/${telefoneBarbearia}?text=${encodeURIComponent(texto)}`;

    window.open(url, '_blank');
};

