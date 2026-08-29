/**
 * MyTravel Public Website Controller (MVC - Controller)
 * Handles user interactions, fare estimation logic, bilingual i18n rendering,
 * and dynamic UI events.
 */

document.addEventListener('DOMContentLoaded', () => {
    const data = window.MyTravelData;
    let currentLang = 'en';
    let selectedVehicleId = 'sedan';
    let tripBookingMode = 'shared'; // 'shared' or 'charter'

    // UI DOM Elements
    const langBtn = document.getElementById('lang-toggle-btn');
    const originSelect = document.getElementById('select-origin');
    const destSelect = document.getElementById('select-dest');
    const vehicleGrid = document.getElementById('vehicle-grid');
    const btnModeShared = document.getElementById('btn-mode-shared');
    const btnModeCharter = document.getElementById('btn-mode-charter');
    const btnSwapRoute = document.getElementById('btn-swap-route');
    const estRouteText = document.getElementById('route-text');
    const estHighwayTag = document.getElementById('est-highway-tag');
    const estDistanceEl = document.getElementById('est-distance');
    const estDurationEl = document.getElementById('est-duration');
    const estPriceModeLabel = document.getElementById('est-price-mode-label');
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
        loadAndRenderNews();
        updateLanguage('en');
        calculateEstimate();
        bindEvents();
    }

    const newsGrid = document.getElementById('news-grid');

    // Fetch and Render Live News Articles
    async function loadAndRenderNews() {
        if (!newsGrid) return;
        let articles = data.NEWS || [];

        try {
            const response = await fetch('/v1/api/travel/news');
            if (response.ok) {
                const resData = await response.json();
                if (resData.articles && resData.articles.length > 0) {
                    articles = resData.articles;
                }
            }
        } catch (err) {
            console.log('Using static news data fallback');
        }

        renderNewsCards(articles);
    }

    function renderNewsCards(articles) {
        if (!newsGrid) return;
        newsGrid.innerHTML = '';

        if (!articles || articles.length === 0) {
            newsGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 2rem;">No news articles available.</div>';
            return;
        }

        articles.forEach(art => {
            const card = document.createElement('div');
            card.className = 'news-card';

            const titleText = currentLang === 'km' ? (art.title_kh || art.title) : art.title;
            const summaryText = currentLang === 'km' ? (art.summary_kh || art.summary || '') : (art.summary || '');
            const categoryText = art.category || 'News';
            const breakingText = currentLang === 'km' ? 'ព័ត៌មានទាន់ហេតុការណ៍' : 'BREAKING NEWS';

            const breakingBadgeHtml = art.is_breaking ? `
                <div class="news-breaking-badge">
                    <span class="pulse-dot"></span> ${breakingText}
                </div>
            ` : '';

            card.innerHTML = `
                <div class="news-thumb-wrapper">
                    <img src="${art.image_url}" alt="${escapeHtml(titleText)}" class="news-thumb-img" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?q=80&w=800&auto=format&fit=crop'">
                    ${breakingBadgeHtml}
                    <div class="news-category-chip">${escapeHtml(categoryText)}</div>
                </div>
                <div class="news-body">
                    <h3 class="news-title">${escapeHtml(titleText)}</h3>
                    <p class="news-summary">${escapeHtml(summaryText)}</p>
                    <div class="news-footer">
                        <span class="news-source"><i class="fa-solid fa-newspaper" style="color: var(--accent-taxi); margin-right: 0.35rem;"></i> ${escapeHtml(art.source_name || 'MyTravel')}</span>
                        <a href="#download" class="news-link-btn">
                            <span>${currentLang === 'km' ? 'កក់សំបុត្រ' : 'Book Ride'}</span>
                            <i class="fa-solid fa-arrow-right"></i>
                        </a>
                    </div>
                </div>
            `;

            newsGrid.appendChild(card);
        });
    }

    function escapeHtml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Populate Province Select Dropdowns
    function populateProvinceDropdowns() {
        const currentOrig = originSelect ? originSelect.value : 'PP';
        const currentDest = destSelect ? destSelect.value : 'SR';

        originSelect.innerHTML = '';
        destSelect.innerHTML = '';

        data.PROVINCES.forEach((p, idx) => {
            const optOrigin = document.createElement('option');
            optOrigin.value = p.id;
            optOrigin.textContent = currentLang === 'km' ? p.name_km : p.name_en;
            if (p.id === currentOrig || (!currentOrig && idx === 0)) optOrigin.selected = true;
            originSelect.appendChild(optOrigin);

            const optDest = document.createElement('option');
            optDest.value = p.id;
            optDest.textContent = currentLang === 'km' ? p.name_km : p.name_en;
            if (p.id === currentDest || (!currentDest && idx === 1)) optDest.selected = true;
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
        const origId = originSelect.value;
        const destId = destSelect.value;

        const origP = data.PROVINCES.find(p => p.id === origId) || data.PROVINCES[0];
        const destP = data.PROVINCES.find(p => p.id === destId) || data.PROVINCES[1];

        const origName = currentLang === 'km' ? origP.name_km : origP.name_en;
        const destName = currentLang === 'km' ? destP.name_km : destP.name_en;

        if (estRouteText) {
            estRouteText.textContent = `${origName} ➔ ${destName}`;
        }
        if (estHighwayTag) {
            estHighwayTag.textContent = origP.hwy || "NR Highway";
        }

        const distanceKm = data.calculateRouteDistance(origId, destId);
        const durationText = data.calculateRouteDuration(distanceKm);

        if (estDistanceEl) estDistanceEl.textContent = `${distanceKm} km`;
        if (estDurationEl) estDurationEl.textContent = durationText;

        const vehicle = data.VEHICLES.find(v => v.id === selectedVehicleId) || data.VEHICLES[0];

        let costUsd = 0;
        if (tripBookingMode === 'shared') {
            costUsd = vehicle.seat_base_usd + (distanceKm * vehicle.seat_per_km_usd);
            if (estPriceModeLabel) {
                estPriceModeLabel.textContent = currentLang === 'km' 
                    ? `តម្លៃសំបុត្រ (${vehicle.name_km})` 
                    : `Per Seat Price (${vehicle.name_en})`;
            }
        } else {
            costUsd = vehicle.charter_base_usd + (distanceKm * vehicle.charter_per_km_usd);
            if (estPriceModeLabel) {
                estPriceModeLabel.textContent = currentLang === 'km' 
                    ? `តម្លៃកក់មួយឡាន (${vehicle.name_km})` 
                    : `Full Private Charter (${vehicle.name_en})`;
            }
        }

        const costKhr = Math.round(costUsd * data.KHR_RATE / 100) * 100;

        if (estUsdEl) estUsdEl.textContent = `$${costUsd.toFixed(2)}`;
        if (estKhrEl) estKhrEl.textContent = `(៛${costKhr.toLocaleString('en-US')})`;
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
        loadAndRenderNews();
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

        if (btnModeShared && btnModeCharter) {
            btnModeShared.addEventListener('click', () => {
                tripBookingMode = 'shared';
                btnModeShared.classList.add('active');
                btnModeCharter.classList.remove('active');
                calculateEstimate();
            });

            btnModeCharter.addEventListener('click', () => {
                tripBookingMode = 'charter';
                btnModeCharter.classList.add('active');
                btnModeShared.classList.remove('active');
                calculateEstimate();
            });
        }

        if (btnSwapRoute) {
            btnSwapRoute.addEventListener('click', () => {
                const temp = originSelect.value;
                originSelect.value = destSelect.value;
                destSelect.value = temp;
                calculateEstimate();
            });
        }

        const tabPassenger = document.getElementById('tab-btn-passenger');
        const tabDriver = document.getElementById('tab-btn-driver');
        const passengerPanel = document.getElementById('passenger-steps-panel');
        const driverPanel = document.getElementById('driver-steps-panel');

        if (tabPassenger && tabDriver) {
            tabPassenger.addEventListener('click', () => {
                tabPassenger.classList.add('active');
                tabDriver.classList.remove('active');
                passengerPanel.style.display = 'grid';
                driverPanel.style.display = 'none';
            });

            tabDriver.addEventListener('click', () => {
                tabDriver.classList.add('active');
                tabPassenger.classList.remove('active');
                driverPanel.style.display = 'grid';
                passengerPanel.style.display = 'none';
            });
        }

        // Mobile Menu Toggle
        const mobileMenuBtn = document.getElementById('mobile-menu-btn');
        const navLinks = document.getElementById('nav-links');

        if (mobileMenuBtn && navLinks) {
            mobileMenuBtn.addEventListener('click', () => {
                navLinks.classList.toggle('active');
                const isOpen = navLinks.classList.contains('active');
                mobileMenuBtn.innerHTML = isOpen 
                    ? '<i class="fa-solid fa-xmark"></i>' 
                    : '<i class="fa-solid fa-bars"></i>';
            });
        }

        // Smooth Scrolling for Header & Navigation Links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                const targetId = this.getAttribute('href');
                if (targetId === '#' || !targetId) return;
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    const navHeight = document.querySelector('.navbar')?.offsetHeight || 70;
                    const elementPosition = targetElement.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - navHeight - 12;

                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });

                    // Auto-close mobile menu on selection
                    if (navLinks && navLinks.classList.contains('active')) {
                        navLinks.classList.remove('active');
                        if (mobileMenuBtn) {
                            mobileMenuBtn.innerHTML = '<i class="fa-solid fa-bars"></i>';
                        }
                    }
                }
            });
        });
    }

    init();
});

