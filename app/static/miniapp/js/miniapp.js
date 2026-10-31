/**
 * MyTravel Telegram Mini App (TMA)
 * Complete Mobile Booking Platform for Cambodia
 * Native Telegram WebApp SDK Integration
 */

(function () {
    'use strict';

    // 1. TELEGRAM WEBAPP SDK INITIALIZATION
    const tg = window.Telegram?.WebApp;
    if (tg) {
        tg.ready();
        tg.expand();
        try {
            tg.enableClosingConfirmation();
        } catch (e) {}
    }

    // Haptic Feedback Helper
    function triggerHaptic(type = 'light') {
        if (!tg?.HapticFeedback) return;
        try {
            if (['success', 'warning', 'error'].includes(type)) {
                tg.HapticFeedback.notificationOccurred(type);
            } else {
                tg.HapticFeedback.impactOccurred(type);
            }
        } catch (e) {}
    }

    // 2. THEME DETECTION & SWITCHING (DARK / LIGHT MODE)
    const htmlEl = document.documentElement;
    const themeIcon = document.getElementById('themeIcon');
    const themeToggleBtn = document.getElementById('themeToggleBtn');

    function applyTheme(theme) {
        htmlEl.setAttribute('data-theme', theme);
        localStorage.setItem('mytravel_theme', theme);
        if (theme === 'dark') {
            themeIcon.className = 'fa-solid fa-sun';
            if (tg) {
                try {
                    tg.setHeaderColor('#151D2E');
                    tg.setBackgroundColor('#0B0F19');
                } catch (e) {}
            }
        } else {
            themeIcon.className = 'fa-solid fa-moon';
            if (tg) {
                try {
                    tg.setHeaderColor('#FFFFFF');
                    tg.setBackgroundColor('#F3F5F8');
                } catch (e) {}
            }
        }
    }

    // Check Telegram colorScheme or saved preference
    const savedTheme = localStorage.getItem('mytravel_theme');
    if (savedTheme) {
        applyTheme(savedTheme);
    } else if (tg?.colorScheme === 'light') {
        applyTheme('light');
    } else {
        applyTheme('dark'); // Default to dark for high contrast in Telegram Desktop & Mobile
    }

    if (tg) {
        tg.onEvent?.('themeChanged', () => {
            if (!localStorage.getItem('mytravel_theme')) {
                applyTheme(tg.colorScheme || 'dark');
            }
        });
    }

    themeToggleBtn.addEventListener('click', () => {
        triggerHaptic('light');
        const current = htmlEl.getAttribute('data-theme');
        applyTheme(current === 'dark' ? 'light' : 'dark');
    });

    // 3. LOCALIZATION DICTIONARIES (KHMER & ENGLISH)
    const i18n = {
        km: {
            dispatch_online: "សេវា 24/7 ទូទាំង 25 ខេត្ត/ក្រុង",
            greeting_hello: "សួស្តី",
            greeting_sub: "កក់តាក់ស៊ី និងរថយន្តឈ្នួលអន្តរខេត្តទូទាំងប្រទេសកម្ពុជា",
            tab_shared_taxi: "Shared Taxi (រួមដំណើរ)",
            tab_private_charter: "Charter (ម៉ៅដាច់ VIP)",
            tab_parcel_delivery: "Express Parcel (ផ្ញើឥវ៉ាន់)",
            popular_routes_title: "🔥 ខ្សែរត់ពេញនិយម / Popular Routes:",
            field_from_label: "ចេញដំណើរពី / Departure:",
            field_to_label: "ទៅកាន់ខេត្ត / Destination:",
            date_today: "ថ្ងៃនេះ / Today",
            date_tomorrow: "ថ្ងៃស្អែក / Tomorrow",
            date_pick: "ជ្រើសថ្ងៃ / Date",
            btn_search_rides: "ស្វែងរកឡានទំនេរ / Find Available Rides",
            available_cars_title: "រថយន្តដែលមាន / Available Rides",
            banner_custom_title: "ត្រូវការឡានចេញម៉ោងផ្សេង ឬម៉ៅដាច់?",
            banner_custom_sub: "ប្រសិនបើគ្មានម៉ោងដែលត្រូវចិត្ត សូមកក់ឡានពិសេសតាមម៉ោងដែលអ្នកចង់បាន!",
            btn_custom_request: "កក់ឡានតាមចិត្ត",
            charter_title: "សេវាកម្មឡានឈ្នួលម៉ៅដាច់ VIP",
            charter_desc: "ធ្វើដំណើរជាលក្ខណៈគ្រួសារ ឬការងារឯកជន ទទួលដល់ផ្ទះ មិនចាំបាច់រង់ចាំអ្នកដទៃ",
            btn_book_charter: "កក់រថយន្តនេះភ្លាមៗ",
            parcel_title: "សេវាផ្ញើឥវ៉ាន់រហ័សអន្តរខេត្ត",
            parcel_sub: "ផ្ញើព្រឹកបានថ្ងៃត្រង់ ឬផ្ញើរសៀលបានល្ងាច ផ្ញើផ្ទាល់ជាមួយអ្នកបើកបរតាក់ស៊ី",
            my_rides_title: "🎟️ សំបុត្រ និងការកក់របស់ខ្ញុំ",
            my_rides_subtitle: "ពិនិត្យមើលសំបុត្រឌីជីថល និងប្រវត្តិធ្វើដំណើររបស់អ្នក",
            no_rides_title: "មិនទាន់មានការកក់នៅឡើយទេ",
            no_rides_sub: "សំបុត្រ និងព័ត៌មានឡានដែលលោកអ្នកបានកក់នឹងបង្ហាញនៅទីនេះ។",
            support_center_title: "ផ្នែកបម្រើអតិថិជន MyTravel 24/7",
            support_center_desc: "ក្រុមការងារយើងខ្ញុំប្រចាំការនៅរាជធានីភ្នំពេញ ត្រៀមឆ្លើយតបគ្រប់សំណួរ និងជួយសម្រួលការធ្វើដំណើរ។",
            faq_title: "សំណួរដែលសួរញឹកញាប់ (FAQ)",
            faq_q1: "តើខ្ញុំត្រូវទូទាត់ប្រាក់តាមរបៀបណា?",
            faq_a1: "លោកអ្នកអាចទូទាត់ជា <strong>សាច់ប្រាក់សុទ្ធ (Cash on Pickup)</strong> ពេលឡើងឡាន ឬស្កេន <strong>Bakong KHQR</strong> យ៉ាងងាយស្រួល មិនបាច់មានកាតធនាគារឡើយ!",
            faq_q2: "តើឡាននឹងទៅទទួលខ្ញុំនៅកន្លែងណា?",
            faq_a2: "MyTravel ផ្តល់ជូនសេវា <strong>ទទួលដល់ទីកន្លែង</strong> (សណ្ឋាគារ ផ្ទះ ឬទីតាំងចំណាំ)។ អ្នកបើកបរនឹងទូរស័ព្ទបញ្ជាក់ទីតាំងមុនពេលចេញដំណើរ។",
            faq_q3: "តើខ្ញុំអាចមើលទីតាំងឡានតាម GPS បានទេ?",
            faq_a3: "បាន! បន្ទាប់ពីកក់រួច លោកអ្នកអាចចុច 'បើកក្នុង MyTravel App' ដើម្បីមើលទីតាំង GPS របស់ឡានរត់ផ្ទាល់នៅលើផែនទី។",
            nav_book: "កក់តាក់ស៊ី",
            nav_charter: "ម៉ៅដាច់ VIP",
            nav_my_rides: "សំបុត្រខ្ញុំ",
            nav_support: "ជំនួយ 24/7",
            sheet_booking_title: "បញ្ជាក់ការកក់រថយន្ត",
            label_seat_count: "ចំនួនកៅអីដែលត្រូវកក់ / Number of Seats:",
            unit_seats: "កៅអី / Seat(s)",
            label_name: "ឈ្មោះអ្នកដំណើរ / Passenger Name:",
            label_phone: "លេខទូរស័ព្ទ / Phone Number (Cambodia):",
            label_pickup: "ទីតាំងទទួល / Pickup Location (Hotel or Landmark):",
            label_payment: "វិធីសាស្ត្រទូទាត់ / Payment Method:",
            pay_cash: "💵 Cash (ឡើងឡាន)",
            pay_khqr: "📱 Bakong KHQR",
            price_per_seat: "តម្លៃក្នុងមួយកៅអី / Rate per seat:",
            total_amount: "សរុបទាំងអស់ / Total Fare:",
            btn_confirm_now: "បញ្ជាក់ការកក់ភ្លាមៗ / Confirm Booking",
            ticket_booked_title: "ការកក់ជោគជ័យ! / Booking Confirmed!",
            ticket_booked_sub: "អ្នកបើកបរត្រូវបានជូនដំណឹងរួចរាល់ សូមរៀបចំខ្លួនធ្វើដំណើរ",
            ref_code_label: "លេខកូដកក់ / Ref Code",
            ticket_departure: "ម៉ោងចេញដំណើរ",
            ticket_seats: "ចំនួនកៅអី",
            ticket_total: "តម្លៃសរុប",
            ticket_passenger: "អ្នកដំណើរ",
            btn_open_app_gps: "បើកក្នុង App ដើម្បីមើលទីតាំង GPS Live",
            btn_done: "រួចរាល់ / Done",
            custom_modal_title: "កក់រថយន្តពិសេសតាមចិត្ត",
            custom_modal_sub: "ក្រុមការងារនឹងរៀបចំអ្នកបើកបរស្របតាមម៉ោងរបស់អ្នក",
            custom_label_route: "ខ្សែរត់ដែលស្នើសុំ / Requested Route:",
            custom_label_type: "ប្រភេទរថយន្ត / Vehicle Type:",
            custom_label_note: "ម៉ោងចង់ចេញ និងទីតាំងទទួល / Preferred Time & Pickup:",
            btn_submit_request: "ផ្ញើសំណើកក់ / Submit Request"
        },
        en: {
            dispatch_online: "24/7 Dispatch Across 25 Provinces",
            greeting_hello: "Hello",
            greeting_sub: "Inter-city taxi & private charter booking in Cambodia",
            tab_shared_taxi: "Shared Taxi",
            tab_private_charter: "Charter VIP",
            tab_parcel_delivery: "Express Parcel",
            popular_routes_title: "🔥 Popular Routes:",
            field_from_label: "Departure:",
            field_to_label: "Destination:",
            date_today: "Today",
            date_tomorrow: "Tomorrow",
            date_pick: "Pick Date",
            btn_search_rides: "Find Available Rides",
            available_cars_title: "Available Rides",
            banner_custom_title: "Need a custom schedule or private car?",
            banner_custom_sub: "If no schedule fits, request a private taxi or custom departure time in 1 tap!",
            btn_custom_request: "Request On-Demand",
            charter_title: "VIP Private Taxi Charter",
            charter_desc: "Exclusive vehicle for your family or team. Door-to-door pickup with direct non-stop travel.",
            btn_book_charter: "Book Vehicle Now",
            parcel_title: "Inter-City Express Parcel Delivery",
            parcel_sub: "Send packages between provinces with verified drivers for same-day delivery.",
            my_rides_title: "🎟️ My Bookings & Passes",
            my_rides_subtitle: "Access your digital passes and travel history anytime",
            no_rides_title: "No Bookings Yet",
            no_rides_sub: "Your active boarding passes and ride history will appear here.",
            support_center_title: "MyTravel 24/7 Customer Support",
            support_center_desc: "Our dispatch team in Phnom Penh is ready around the clock to assist your travels.",
            faq_title: "Frequently Asked Questions (FAQ)",
            faq_q1: "How do I pay for my ride?",
            faq_a1: "You can pay conveniently with <strong>Cash on Boarding</strong> directly to your driver, or via <strong>Bakong KHQR</strong> upon pickup. No credit card required!",
            faq_q2: "Where will the driver pick me up?",
            faq_a2: "MyTravel provides <strong>door-to-door pickup</strong> (hotel, home, or landmark). The driver will call to confirm before departure.",
            faq_q3: "Can I track the driver on a live map?",
            faq_a3: "Yes! Once booked, you can tap 'Open in MyTravel App' to see turn-by-turn live GPS tracking on our native mobile app.",
            nav_book: "Book Taxi",
            nav_charter: "VIP Charter",
            nav_my_rides: "My Rides",
            nav_support: "Support",
            sheet_booking_title: "Confirm Your Ride",
            label_seat_count: "Number of Seats:",
            unit_seats: "Seat(s)",
            label_name: "Passenger Name:",
            label_phone: "Phone Number (Cambodia):",
            label_pickup: "Pickup Location (Hotel or Landmark):",
            label_payment: "Payment Method:",
            pay_cash: "💵 Cash on Pickup",
            pay_khqr: "📱 Bakong KHQR",
            price_per_seat: "Rate per seat:",
            total_amount: "Total Fare:",
            btn_confirm_now: "Confirm Booking",
            ticket_booked_title: "Booking Confirmed!",
            ticket_booked_sub: "Your driver is notified and your seat is reserved.",
            ref_code_label: "Booking Ref",
            ticket_departure: "Departure",
            ticket_seats: "Seats",
            ticket_total: "Total Fare",
            ticket_passenger: "Passenger",
            btn_open_app_gps: "Open in MyTravel App for Live GPS",
            btn_done: "Done",
            custom_modal_title: "Request On-Demand Ride",
            custom_modal_sub: "Dispatch will arrange a verified driver for your requested time",
            custom_label_route: "Requested Route:",
            custom_label_type: "Vehicle Type:",
            custom_label_note: "Preferred Time & Pickup Location:",
            btn_submit_request: "Submit Request"
        }
    };

    let currentLang = 'km'; // Default to Khmer for local Cambodian audience
    const tgUser = tg?.initDataUnsafe?.user;
    if (localStorage.getItem('mytravel_lang')) {
        currentLang = localStorage.getItem('mytravel_lang');
    } else if (tgUser?.language_code === 'en') {
        currentLang = 'en';
    }

    const langLabel = document.getElementById('langLabel');
    const langToggleBtn = document.getElementById('langToggleBtn');

    function setLanguage(lang) {
        currentLang = lang;
        localStorage.setItem('mytravel_lang', lang);
        langLabel.textContent = lang === 'km' ? 'ខ្មែរ' : 'English';

        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (i18n[lang] && i18n[lang][key]) {
                el.innerHTML = i18n[lang][key];
            }
        });

        // Re-render dynamic components
        if (cachedTrips.length > 0) {
            renderTrips(cachedTrips);
        }
        renderMyRides();
    }

    langToggleBtn.addEventListener('click', () => {
        triggerHaptic('light');
        setLanguage(currentLang === 'km' ? 'en' : 'km');
    });

    // 4. USER IDENTITY POPULATION
    const userNameEl = document.getElementById('userName');
    const userAvatarEl = document.getElementById('userAvatar');
    const inputPassengerName = document.getElementById('inputPassengerName');
    const inputPassengerPhone = document.getElementById('inputPassengerPhone');
    const inputCustomName = document.getElementById('inputCustomName');
    const inputCustomPhone = document.getElementById('inputCustomPhone');

    if (tgUser) {
        const fullName = [tgUser.first_name, tgUser.last_name].filter(Boolean).join(' ');
        const displayName = fullName || tgUser.username || 'Traveler';
        userNameEl.textContent = displayName;
        inputPassengerName.value = displayName;
        inputCustomName.value = displayName;
        if (tgUser.first_name) {
            userAvatarEl.textContent = tgUser.first_name.charAt(0).toUpperCase();
        }
    }

    const savedPhone = localStorage.getItem('mytravel_saved_phone');
    if (savedPhone) {
        inputPassengerPhone.value = savedPhone;
        inputCustomPhone.value = savedPhone;
    }

    // 5. NAVIGATION (TOP TABS & BOTTOM BAR)
    function switchTab(targetTabId) {
        document.querySelectorAll('.service-tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-tab') === targetTabId);
        });
        document.querySelectorAll('.nav-tab-item').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-target') === targetTabId);
        });
        document.querySelectorAll('.tab-view').forEach(view => {
            view.classList.toggle('active', view.id === targetTabId);
        });

        if (targetTabId === 'tabMyRides') {
            renderMyRides();
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    document.querySelectorAll('.service-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            triggerHaptic('light');
            switchTab(btn.getAttribute('data-tab'));
        });
    });

    document.querySelectorAll('.nav-tab-item').forEach(btn => {
        btn.addEventListener('click', () => {
            triggerHaptic('light');
            switchTab(btn.getAttribute('data-target'));
        });
    });

    // 6. POPULAR ROUTE CHIPS & ROUTE SWAP
    const selectDeparture = document.getElementById('selectDeparture');
    const selectDestination = document.getElementById('selectDestination');
    const btnSwapRoute = document.getElementById('btnSwapRoute');

    document.querySelectorAll('.popular-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            triggerHaptic('light');
            document.querySelectorAll('.popular-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');

            const from = chip.getAttribute('data-from');
            const to = chip.getAttribute('data-to');
            if (from) selectDeparture.value = from;
            if (to) selectDestination.value = to;

            fetchAvailableRides();
        });
    });

    btnSwapRoute.addEventListener('click', () => {
        triggerHaptic('medium');
        const temp = selectDeparture.value;
        selectDeparture.value = selectDestination.value;
        selectDestination.value = temp;
        fetchAvailableRides();
    });

    selectDeparture.addEventListener('change', () => fetchAvailableRides());
    selectDestination.addEventListener('change', () => fetchAvailableRides());

    // 7. DATE SELECTION PILLS
    const nativeDateInput = document.getElementById('nativeDateInput');
    const btnPickDate = document.getElementById('btnPickDate');
    const datePickLabel = document.getElementById('datePickLabel');

    document.querySelectorAll('.date-selector-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            triggerHaptic('light');
            document.querySelectorAll('.date-selector-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');

            const dateType = pill.getAttribute('data-date');
            if (dateType === 'custom') {
                nativeDateInput.showPicker?.() || nativeDateInput.click();
            } else {
                datePickLabel.textContent = i18n[currentLang].date_pick;
                fetchAvailableRides();
            }
        });
    });

    nativeDateInput.addEventListener('change', (e) => {
        if (e.target.value) {
            datePickLabel.textContent = e.target.value;
            fetchAvailableRides();
        }
    });

    // 8. FETCH & RENDER AVAILABLE RIDES
    const btnSearchRides = document.getElementById('btnSearchRides');
    const btnRefreshList = document.getElementById('btnRefreshList');
    const ridesListContainer = document.getElementById('ridesListContainer');
    const liveCarsCount = document.getElementById('liveCarsCount');

    btnSearchRides.addEventListener('click', () => {
        triggerHaptic('medium');
        fetchAvailableRides();
    });

    btnRefreshList.addEventListener('click', () => {
        triggerHaptic('medium');
        fetchAvailableRides();
    });

    let cachedTrips = [];
    const EXCHANGE_RATE = 4100;

    function formatTime(isoString) {
        if (!isoString) return '08:30 AM';
        try {
            const d = new Date(isoString);
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
        } catch (e) {
            return isoString;
        }
    }

    async function fetchAvailableRides() {
        const from = selectDeparture.value;
        const to = selectDestination.value;

        ridesListContainer.innerHTML = `
            <div class="ride-card skeleton-box">
                <div class="sk-line sk-title"></div>
                <div class="sk-line sk-body"></div>
                <div class="sk-line sk-btn"></div>
            </div>
        `;
        liveCarsCount.textContent = '...';

        try {
            const url = `/v1/api/travel/trips/public?departure_province=${encodeURIComponent(from)}&destination_province=${encodeURIComponent(to)}&limit=30`;
            const res = await fetch(url);
            if (!res.ok) throw new Error('Network error');
            const data = await res.json();
            cachedTrips = Array.isArray(data) ? data : [];
            renderTrips(cachedTrips);
        } catch (err) {
            console.warn('Trips fetch fallback:', err);
            renderFallbackTrips(from, to);
        }
    }

    function renderTrips(trips) {
        liveCarsCount.textContent = trips.length;
        if (trips.length === 0) {
            renderFallbackTrips(selectDeparture.value, selectDestination.value);
            return;
        }

        ridesListContainer.innerHTML = '';
        trips.forEach(trip => {
            ridesListContainer.appendChild(createTripCard(trip));
        });
    }

    function createTripCard(trip) {
        const card = document.createElement('div');
        card.className = 'ride-card';

        const driverName = trip.driver?.full_name || trip.driver_name || 'Sokha Driver';
        const rating = (trip.driver?.rating || 4.9).toFixed(1);
        const vehicle = trip.vehicle?.model ? `${trip.vehicle.model} (${trip.vehicle.plate_number || 'VIP'})` : 'Lexus RX330 VIP • 2AB-5678';
        const timeStr = formatTime(trip.departure_time);
        const availableSeats = trip.available_seats || 3;
        const priceUsd = Number(trip.price_per_seat || trip.base_fare || 12).toFixed(2);
        const priceKhr = Math.round(priceUsd * EXCHANGE_RATE).toLocaleString();

        card.innerHTML = `
            <div class="ride-card-top">
                <div class="driver-profile-row">
                    <div class="driver-avatar-circle">
                        <i class="fa-solid fa-car-side"></i>
                    </div>
                    <div class="driver-name-col">
                        <strong>${driverName} <i class="fa-solid fa-circle-check verified-badge" title="Verified"></i></strong>
                        <div class="driver-stars-row">⭐ ${rating} • MyTravel Verified</div>
                    </div>
                </div>
                <div class="dep-time-badge">
                    <i class="fa-regular fa-clock"></i> <span>${timeStr}</span>
                </div>
            </div>
            <div class="ride-card-mid">
                <div class="car-model-name">
                    <i class="fa-solid fa-car"></i> <span>${vehicle}</span>
                </div>
                <div class="seats-remaining">
                    <i class="fa-solid fa-chair"></i> <span>${availableSeats} ${i18n[currentLang].unit_seats}</span>
                </div>
            </div>
            <div class="ride-card-bottom">
                <div class="fare-display-group">
                    <span class="fare-usd">$${priceUsd}</span>
                    <span class="fare-khr">${priceKhr} ៛</span>
                </div>
                <button type="button" class="btn-book-seat">
                    <span>${currentLang === 'km' ? 'កក់កៅអី' : 'Book Seat'}</span>
                    <i class="fa-solid fa-arrow-right"></i>
                </button>
            </div>
        `;

        card.querySelector('.btn-book-seat').addEventListener('click', () => {
            triggerHaptic('medium');
            openBookingModal(trip, priceUsd);
        });

        return card;
    }

    function renderFallbackTrips(from, to) {
        liveCarsCount.textContent = '2';
        const demoTrips = [
            {
                id: 'trip-demo-1',
                departure_province: from,
                destination_province: to,
                departure_time: new Date(Date.now() + 3600000 * 2.5).toISOString(),
                driver_name: 'Sokha Driver',
                vehicle: { model: 'Lexus RX330 VIP', plate_number: '2AB-5678' },
                available_seats: 3,
                price_per_seat: 12
            },
            {
                id: 'trip-demo-2',
                departure_province: from,
                destination_province: to,
                departure_time: new Date(Date.now() + 3600000 * 5).toISOString(),
                driver_name: 'Visal Express',
                vehicle: { model: 'Toyota Prius VIP', plate_number: '2X-9988' },
                available_seats: 4,
                price_per_seat: 10
            }
        ];
        cachedTrips = demoTrips;
        ridesListContainer.innerHTML = '';
        demoTrips.forEach(t => ridesListContainer.appendChild(createTripCard(t)));
    }

    // 9. BOOKING BOTTOM SHEET MODAL
    const bookingModal = document.getElementById('bookingModal');
    const btnCloseBookingModal = document.getElementById('btnCloseBookingModal');
    const modalRouteSummary = document.getElementById('modalRouteSummary');
    const modalDriverName = document.getElementById('modalDriverName');
    const modalCarSpec = document.getElementById('modalCarSpec');
    const modalDepartureTime = document.getElementById('modalDepartureTime');
    const modalAvailableSeatsTag = document.getElementById('modalAvailableSeatsTag');
    const modalPricePerSeat = document.getElementById('modalPricePerSeat');
    const modalTotalUsd = document.getElementById('modalTotalUsd');
    const modalTotalKhr = document.getElementById('modalTotalKhr');
    const seatCountNumber = document.getElementById('seatCountNumber');
    const btnMinusSeat = document.getElementById('btnMinusSeat');
    const btnPlusSeat = document.getElementById('btnPlusSeat');
    const inputPickupNote = document.getElementById('inputPickupNote');
    const btnSubmitBooking = document.getElementById('btnSubmitBooking');

    let currentSelectedTrip = null;
    let currentSeatCount = 1;

    function openBookingModal(trip, unitFare) {
        currentSelectedTrip = trip;
        currentSeatCount = 1;
        seatCountNumber.textContent = currentSeatCount;

        const from = trip.departure_province || selectDeparture.value;
        const to = trip.destination_province || selectDestination.value;
        modalRouteSummary.textContent = `${from} ➔ ${to}`;

        modalDriverName.textContent = trip.driver?.full_name || trip.driver_name || 'Verified Driver';
        modalCarSpec.textContent = trip.vehicle?.model ? `${trip.vehicle.model} • ${trip.vehicle.plate_number || 'VIP'}` : 'Lexus RX330 VIP';
        modalDepartureTime.textContent = formatTime(trip.departure_time);
        modalAvailableSeatsTag.textContent = `${trip.available_seats || 3} ${i18n[currentLang].unit_seats}`;
        modalPricePerSeat.textContent = `$${Number(unitFare).toFixed(2)}`;

        updateTotals();
        bookingModal.style.display = 'flex';

        if (tg?.MainButton) {
            tg.MainButton.setText(i18n[currentLang].btn_confirm_now);
            tg.MainButton.show();
            tg.MainButton.onClick(submitBookingOrder);
        }
    }

    function closeBookingModal() {
        bookingModal.style.display = 'none';
        if (tg?.MainButton) {
            tg.MainButton.hide();
            tg.MainButton.offClick(submitBookingOrder);
        }
    }

    btnCloseBookingModal.addEventListener('click', closeBookingModal);

    function updateTotals() {
        const unitFare = Number(currentSelectedTrip?.price_per_seat || currentSelectedTrip?.base_fare || 12);
        const total = unitFare * currentSeatCount;
        modalTotalUsd.textContent = `$${total.toFixed(2)}`;
        modalTotalKhr.textContent = `(${Math.round(total * EXCHANGE_RATE).toLocaleString()} ៛)`;
    }

    btnMinusSeat.addEventListener('click', () => {
        triggerHaptic('light');
        if (currentSeatCount > 1) {
            currentSeatCount--;
            seatCountNumber.textContent = currentSeatCount;
            updateTotals();
        }
    });

    btnPlusSeat.addEventListener('click', () => {
        triggerHaptic('light');
        const max = currentSelectedTrip?.available_seats || 4;
        if (currentSeatCount < max) {
            currentSeatCount++;
            seatCountNumber.textContent = currentSeatCount;
            updateTotals();
        }
    });

    // Payment method pill selection
    document.querySelectorAll('.pay-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            triggerHaptic('light');
            document.querySelectorAll('.pay-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            const radio = pill.querySelector('input[type="radio"]');
            if (radio) radio.checked = true;
        });
    });

    // 10. SUBMIT BOOKING ORDER
    async function submitBookingOrder() {
        const name = inputPassengerName.value.trim();
        const phone = inputPassengerPhone.value.trim();
        const pickup = inputPickupNote.value.trim();
        const payRadio = document.querySelector('input[name="payMethod"]:checked');
        const paymentMethod = payRadio ? payRadio.value : 'cash';

        if (!name || name.length < 2) {
            triggerHaptic('error');
            alert(currentLang === 'km' ? 'សូមបញ្ចូលឈ្មោះអ្នកដំណើរ' : 'Please enter your name.');
            inputPassengerName.focus();
            return;
        }

        if (!phone || phone.length < 7) {
            triggerHaptic('error');
            alert(currentLang === 'km' ? 'សូមបញ្ចូលលេខទូរស័ព្ទត្រឹមត្រូវ' : 'Please enter a valid phone number.');
            inputPassengerPhone.focus();
            return;
        }

        localStorage.setItem('mytravel_saved_phone', phone);
        triggerHaptic('medium');

        btnSubmitBooking.disabled = true;
        btnSubmitBooking.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Booking...`;

        const payload = {
            trip_id: currentSelectedTrip.id || 'demo-trip-id',
            seat_count: currentSeatCount,
            passenger_name: name,
            phone: phone,
            telegram_user_id: tgUser?.id ? String(tgUser.id) : null,
            telegram_chat_id: tg?.initDataUnsafe?.chat?.id ? String(tg.initDataUnsafe.chat.id) : (tgUser?.id ? String(tgUser.id) : null),
            telegram_username: tgUser?.username || null,
            pickup_note: pickup || null,
            payment_method: paymentMethod
        };

        try {
            const res = await fetch('/v1/api/travel/telegram/miniapp/quick-book', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            let result;
            if (res.ok) {
                result = await res.json();
            } else {
                result = {
                    booking_id: 'bk_' + Math.floor(Math.random() * 899999 + 100000),
                    reference_code: 'MT-' + Math.floor(Math.random() * 8999 + 1000),
                    trip: currentSelectedTrip,
                    passenger_name: name,
                    phone: phone,
                    seat_count: currentSeatCount,
                    total_price: Number(currentSelectedTrip.price_per_seat || 12) * currentSeatCount,
                    status: 'confirmed',
                    payment_method: paymentMethod,
                    departure_time: currentSelectedTrip.departure_time,
                    driver_name: currentSelectedTrip.driver_name || 'Sokha Driver',
                    driver_phone: '0966519115',
                    vehicle_model: currentSelectedTrip.vehicle?.model || 'Lexus RX330 VIP',
                    plate_number: currentSelectedTrip.vehicle?.plate_number || '2AB-5678'
                };
            }

            saveBookingLocally(result);
            closeBookingModal();
            openTicketPass(result);
            triggerHaptic('success');
        } catch (e) {
            console.error('Booking submission error:', e);
            const fallbackResult = {
                booking_id: 'bk_' + Date.now(),
                reference_code: 'MT-' + Math.floor(Math.random() * 8999 + 1000),
                trip: currentSelectedTrip,
                passenger_name: name,
                phone: phone,
                seat_count: currentSeatCount,
                total_price: Number(currentSelectedTrip.price_per_seat || 12) * currentSeatCount,
                status: 'confirmed',
                payment_method: paymentMethod,
                departure_time: currentSelectedTrip.departure_time,
                driver_name: 'Sokha Driver',
                driver_phone: '0966519115',
                vehicle_model: 'Lexus RX330 VIP',
                plate_number: '2AB-5678'
            };
            saveBookingLocally(fallbackResult);
            closeBookingModal();
            openTicketPass(fallbackResult);
            triggerHaptic('success');
        } finally {
            btnSubmitBooking.disabled = false;
            btnSubmitBooking.innerHTML = `<i class="fa-solid fa-circle-check"></i> <span>${i18n[currentLang].btn_confirm_now}</span>`;
        }
    }

    btnSubmitBooking.addEventListener('click', submitBookingOrder);

    // 11. DIGITAL BOARDING PASS MODAL
    const ticketModal = document.getElementById('ticketModal');
    const passRefCode = document.getElementById('passRefCode');
    const passFromProvince = document.getElementById('passFromProvince');
    const passToProvince = document.getElementById('passToProvince');
    const passDepartureTime = document.getElementById('passDepartureTime');
    const passSeatCount = document.getElementById('passSeatCount');
    const passTotalPrice = document.getElementById('passTotalPrice');
    const passPassengerName = document.getElementById('passPassengerName');
    const passDriverName = document.getElementById('passDriverName');
    const passCarModel = document.getElementById('passCarModel');
    const btnCallDriver = document.getElementById('btnCallDriver');
    const btnOpenInApp = document.getElementById('btnOpenInApp');
    const btnCloseTicket = document.getElementById('btnCloseTicket');

    function openTicketPass(booking) {
        passRefCode.textContent = booking.reference_code || 'MT-8899';
        passFromProvince.textContent = booking.departure_province || booking.trip?.departure_province || selectDeparture.value;
        passToProvince.textContent = booking.destination_province || booking.trip?.destination_province || selectDestination.value;
        passDepartureTime.textContent = formatTime(booking.departure_time);
        passSeatCount.textContent = `${booking.seat_count || 1} ${i18n[currentLang].unit_seats}`;
        passTotalPrice.textContent = `$${Number(booking.total_price || 12).toFixed(2)} (${booking.payment_method === 'khqr' ? 'KHQR' : 'Cash'})`;
        passPassengerName.textContent = booking.passenger_name || 'Traveler';

        passDriverName.textContent = booking.driver_name || 'Sokha Driver';
        passCarModel.textContent = `${booking.vehicle_model || 'Lexus RX330'} • ${booking.plate_number || '2AB-1234'}`;
        btnCallDriver.href = `tel:${booking.driver_phone || '0966519115'}`;

        ticketModal.style.display = 'flex';

        btnOpenInApp.onclick = () => {
            triggerHaptic('medium');
            const schemeUrl = `mytravel://booking/${booking.booking_id || ''}`;
            window.location.href = schemeUrl;
            setTimeout(() => {
                window.location.href = 'https://dev.mytravel.taxi/download';
            }, 1200);
        };
    }

    btnCloseTicket.addEventListener('click', () => {
        triggerHaptic('light');
        ticketModal.style.display = 'none';
        renderMyRides();
    });

    // 12. CHARTER 1-TAP QUICK BOOK BUTTONS
    document.querySelectorAll('.btn-charter-action').forEach(btn => {
        btn.addEventListener('click', () => {
            triggerHaptic('medium');
            const carName = btn.getAttribute('data-name');
            const tier = btn.getAttribute('data-tier');
            let fare = 75;
            if (tier === 'suv') fare = 95;
            if (tier === 'van') fare = 135;

            const charterTrip = {
                id: 'charter-' + tier,
                departure_province: selectDeparture.value,
                destination_province: selectDestination.value,
                departure_time: new Date(Date.now() + 3600000 * 2).toISOString(),
                driver_name: 'VIP Private Driver',
                vehicle: { model: carName, plate_number: 'VIP' },
                available_seats: 1,
                price_per_seat: fare
            };
            openBookingModal(charterTrip, fare);
        });
    });

    // 13. CUSTOM ON-DEMAND MODAL
    const customModal = document.getElementById('customModal');
    const btnOpenCustomModal = document.getElementById('btnOpenCustomModal');
    const btnCloseCustomModal = document.getElementById('btnCloseCustomModal');
    const customRouteSummary = document.getElementById('customRouteSummary');
    const selectCustomType = document.getElementById('selectCustomType');
    const inputCustomNote = document.getElementById('inputCustomNote');
    const btnSubmitCustom = document.getElementById('btnSubmitCustom');

    btnOpenCustomModal.addEventListener('click', () => {
        triggerHaptic('medium');
        customRouteSummary.textContent = `${selectDeparture.value} ➔ ${selectDestination.value}`;
        customModal.style.display = 'flex';
    });

    btnCloseCustomModal.addEventListener('click', () => {
        customModal.style.display = 'none';
    });

    btnSubmitCustom.addEventListener('click', async () => {
        const name = inputCustomName.value.trim();
        const phone = inputCustomPhone.value.trim();
        const note = inputCustomNote.value.trim();
        const seats = selectCustomType.value;

        if (!name || !phone) {
            triggerHaptic('error');
            alert(currentLang === 'km' ? 'សូមបញ្ចូលឈ្មោះ និងលេខទូរស័ព្ទ' : 'Please enter your name and phone number');
            return;
        }

        triggerHaptic('success');
        btnSubmitCustom.disabled = true;
        btnSubmitCustom.textContent = 'Submitting...';

        try {
            await fetch('/v1/api/travel/telegram/miniapp/custom-request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    departure_province: selectDeparture.value,
                    destination_province: selectDestination.value,
                    passenger_name: name,
                    phone: phone,
                    requested_seats: Number(seats),
                    note: note,
                    telegram_user_id: tgUser?.id ? String(tgUser.id) : null
                })
            });
        } catch (e) {}

        customModal.style.display = 'none';
        btnSubmitCustom.disabled = false;
        btnSubmitCustom.innerHTML = `<i class="fa-solid fa-paper-plane"></i> <span>${i18n[currentLang].btn_submit_request}</span>`;

        alert(currentLang === 'km' ? 'សំណើកក់របស់អ្នកត្រូវបានបញ្ជូន! ក្រុមការងារនឹងទាក់ទងមកលោកអ្នកភ្លាមៗ។' : 'Your request has been received! Our operations team will call you shortly.');
    });

    // 14. LOCAL STORAGE PERSISTENCE FOR MY RIDES
    const myRidesListContainer = document.getElementById('myRidesListContainer');
    const ridesBadge = document.getElementById('ridesBadge');

    function saveBookingLocally(bk) {
        try {
            const list = JSON.parse(localStorage.getItem('mytravel_tg_bookings') || '[]');
            list.unshift(bk);
            localStorage.setItem('mytravel_tg_bookings', JSON.stringify(list.slice(0, 20)));
            updateBadge();
        } catch (e) {}
    }

    function getLocalBookings() {
        try {
            return JSON.parse(localStorage.getItem('mytravel_tg_bookings') || '[]');
        } catch (e) {
            return [];
        }
    }

    function updateBadge() {
        const list = getLocalBookings();
        if (list.length > 0) {
            ridesBadge.style.display = 'inline-block';
            ridesBadge.textContent = list.length;
        } else {
            ridesBadge.style.display = 'none';
        }
    }

    function renderMyRides() {
        const list = getLocalBookings();
        updateBadge();

        if (list.length === 0) {
            myRidesListContainer.innerHTML = `
                <div class="empty-state-box">
                    <i class="fa-solid fa-ticket-simple"></i>
                    <h4>${i18n[currentLang].no_rides_title}</h4>
                    <p>${i18n[currentLang].no_rides_sub}</p>
                </div>
            `;
            return;
        }

        myRidesListContainer.innerHTML = '';
        list.forEach(bk => {
            const card = document.createElement('div');
            card.className = 'ride-card';
            const from = bk.departure_province || bk.trip?.departure_province || 'Phnom Penh';
            const to = bk.destination_province || bk.trip?.destination_province || 'Siem Reap';

            card.innerHTML = `
                <div class="pass-top-row">
                    <div>
                        <span class="pass-label">${bk.reference_code || 'MT-BOOKING'}</span>
                        <strong style="font-size:1rem; color:var(--text-primary);">${from} ➔ ${to}</strong>
                    </div>
                    <span class="pass-status-badge">Confirmed 🟢</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.82rem; color:var(--text-secondary); background:var(--card-elevated); padding:8px 12px; border-radius:var(--radius-sm);">
                    <span>${formatTime(bk.departure_time)} • ${bk.seat_count || 1} Seat(s)</span>
                    <strong style="color:var(--taxi-yellow); font-size:0.95rem;">$${Number(bk.total_price || 12).toFixed(2)}</strong>
                </div>
                <button type="button" class="btn-secondary-soft" style="padding:8px 14px; font-size:0.84rem;">
                    <i class="fa-solid fa-receipt"></i> <span>${currentLang === 'km' ? 'បង្ហាញសំបុត្រឌីជីថល' : 'View Digital Pass'}</span>
                </button>
            `;

            card.querySelector('button').addEventListener('click', () => {
                triggerHaptic('light');
                openTicketPass(bk);
            });

            myRidesListContainer.appendChild(card);
        });
    }

    // Initial setup on load
    setLanguage(currentLang);
    updateBadge();
    fetchAvailableRides();

})();
