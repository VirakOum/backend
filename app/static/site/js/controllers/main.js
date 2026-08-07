/**
 * MyTravel Public Website Controller (MVC - Controller)
 * Handles user interactions, fare estimation logic, bilingual i18n rendering,
 * and dynamic UI events.
 */

document.addEventListener('DOMContentLoaded', () => {
    const data = window.MyTravelData;
    let currentLang = 'en';
    let selectedVehicleId = 'sedan';

    // UI DOM Elements
    const langBtn = document.getElementById('lang-toggle-btn');
    const originSelect = document.getElementById('select-origin');
    const destSelect = document.getElementById('select-dest');
    const vehicleGrid = document.getElementById('vehicle-grid');
    const estDistanceEl = document.getElementById('est-distance');
    const estUsdEl = document.getElementById('est-usd');
    const estKhrEl = document.getElementById('est-khr');
    const faqContainer = document.getElementById('faq-container');
    const statsBanner = document.getElementById('stats-banner');

    // Initialize Page
    function init() {
        populateProvinceDropdowns();
        renderVehicleCards();
        renderStats();
        renderFAQs();
        updateLanguage('en');
        calculateEstimate();
        bindEvents();
    }

    // Populate Province Select Dropdowns
    function populateProvinceDropdowns() {
        originSelect.innerHTML = '';
        destSelect.innerHTML = '';

        data.PROVINCES.forEach((p, idx) => {
            const optOrigin = document.createElement('option');
            optOrigin.value = p.id;
            optOrigin.textContent = currentLang === 'km' ? p.name_km : p.name_en;
            if (idx === 0) optOrigin.selected = true; // Phnom Penh
            originSelect.appendChild(optOrigin);

            const optDest = document.createElement('option');
            optDest.value = p.id;
            optDest.textContent = currentLang === 'km' ? p.name_km : p.name_en;
            if (idx === 1) optDest.selected = true; // Siem Reap
            destSelect.appendChild(optDest);
        });
    }

    // Render Vehicle Selection Cards
    function renderVehicleCards() {
        vehicleGrid.innerHTML = '';
        data.VEHICLES.forEach(v => {
            const card = document.createElement('div');
            card.className = `vehicle-card ${v.id === selectedVehicleId ? 'active' : ''}`;
            card.dataset.id = v.id;

            const badgeText = currentLang === 'km' ? v.badge_km : v.badge_en;
            const nameText = currentLang === 'km' ? v.name_km : v.name_en;

            card.innerHTML = `
                <div class="vehicle-badge">${badgeText}</div>
                <i class="fa-solid ${v.icon} vehicle-icon"></i>
                <div class="vehicle-name">${nameText}</div>
                <div class="vehicle-cap">${v.capacity}</div>
            `;

            card.addEventListener('click', () => {
                selectedVehicleId = v.id;
                document.querySelectorAll('.vehicle-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                calculateEstimate();
            });

            vehicleGrid.appendChild(card);
        });
    }

    // Calculate Route Distance & Fare Estimate
    function calculateEstimate() {
        const orig = originSelect.value;
        const dest = destSelect.value;

        let distanceKm = 150; // Default distance fallback
        if (orig === dest) {
            distanceKm = 15; // Intra-city route estimate
        } else {
            const key1 = `${orig}-${dest}`;
            const key2 = `${dest}-${orig}`;
            if (data.DISTANCE_MATRIX[key1]) {
                distanceKm = data.DISTANCE_MATRIX[key1];
            } else if (data.DISTANCE_MATRIX[key2]) {
                distanceKm = data.DISTANCE_MATRIX[key2];
            } else {
                distanceKm = 220; // Default inter-city distance
            }
        }

        const vehicle = data.VEHICLES.find(v => v.id === selectedVehicleId) || data.VEHICLES[0];
        const costUsd = vehicle.base_usd + (distanceKm * vehicle.per_km_usd);
        const costKhr = Math.round(costUsd * data.KHR_RATE / 100) * 100;

        estDistanceEl.textContent = `${distanceKm} km`;
        estUsdEl.textContent = `$${costUsd.toFixed(2)}`;
        estKhrEl.textContent = `៛${costKhr.toLocaleString('en-US')}`;
    }

    // Render Telemetry Stats Banner
    function renderStats() {
        statsBanner.innerHTML = '';
        data.STATS.forEach(s => {
            const item = document.createElement('div');
            item.className = 'stat-item';
            const label = currentLang === 'km' ? s.label_km : s.label_en;
            item.innerHTML = `
                <div class="stat-num">${s.count}</div>
                <div class="stat-lbl">${label}</div>
            `;
            statsBanner.appendChild(item);
        });
    }

    // Render FAQs Accordion
    function renderFAQs() {
        faqContainer.innerHTML = '';
        data.FAQS.forEach((faq, idx) => {
            const q = currentLang === 'km' ? faq.q_km : faq.q_en;
            const a = currentLang === 'km' ? faq.a_km : faq.a_en;

            const item = document.createElement('div');
            item.className = `faq-item ${idx === 0 ? 'open' : ''}`;
            item.innerHTML = `
                <div class="faq-header">
                    <span>${q}</span>
                    <i class="fa-solid fa-chevron-down faq-icon"></i>
                </div>
                <div class="faq-body">${a}</div>
            `;

            item.querySelector('.faq-header').addEventListener('click', () => {
                item.classList.toggle('open');
            });

            faqContainer.appendChild(item);
        });
    }

    // Toggle Language (EN / KM)
    function updateLanguage(lang) {
        currentLang = lang;
        const dict = data.I18N[lang] || data.I18N.en;

        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (dict[key]) {
                el.textContent = dict[key];
            }
        });

        langBtn.innerHTML = lang === 'en' 
            ? '<i class="fa-solid fa-globe"></i> <span>ភាសាខ្មែរ</span>' 
            : '<i class="fa-solid fa-globe"></i> <span>English</span>';

        populateProvinceDropdowns();
        renderVehicleCards();
        renderStats();
        renderFAQs();
        calculateEstimate();
    }

    // Event Bindings
    function bindEvents() {
        langBtn.addEventListener('click', () => {
            const newLang = currentLang === 'en' ? 'km' : 'en';
            updateLanguage(newLang);
        });

        originSelect.addEventListener('change', calculateEstimate);
        destSelect.addEventListener('change', calculateEstimate);
    }

    init();
});
