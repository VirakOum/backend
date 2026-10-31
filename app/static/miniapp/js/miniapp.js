/**
 * MyTravel Telegram Mini App (TMA) — 100% Real API Integration
 * Live Inter-Province Trips, Seat Selection, Real Database Bookings, Fleet & Support
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
            if (themeIcon) themeIcon.className = 'fa-solid fa-sun';
            if (tg) {
                try {
                    tg.setHeaderColor('#151D2E');
                    tg.setBackgroundColor('#0B0F19');
                } catch (e) {}
            }
        } else {
            if (themeIcon) themeIcon.className = 'fa-solid fa-moon';
            if (tg) {
                try {
                    tg.setHeaderColor('#FFFFFF');
                    tg.setBackgroundColor('#F3F5F8');
                } catch (e) {}
            }
        }
    }

    const savedTheme = localStorage.getItem('mytravel_theme');
    if (savedTheme) {
        applyTheme(savedTheme);
    } else if (tg?.colorScheme === 'light') {
        applyTheme('light');
    } else {
        applyTheme('dark');
    }

    if (tg) {
        tg.onEvent?.('themeChanged', () => {
            if (!localStorage.getItem('mytravel_theme')) {
                applyTheme(tg.colorScheme || 'dark');
            }
        });
    }

    themeToggleBtn?.addEventListener('click', () => {
        triggerHaptic('light');
        const current = htmlEl.getAttribute('data-theme');
        applyTheme(current === 'dark' ? 'light' : 'dark');
    });

    // 3. LOCALIZATION DICTIONARIES (KHMER & ENGLISH)
    const i18n = {
        km: {
            dispatch_online: "ប្រព័ន្ធកក់ឡានផ្ទាល់ 24/7",
            greeting_hello: "សួស្តី",
            greeting_sub: "កក់តាក់ស៊ី និងរថយន្តឈ្នួលអន្តរខេត្តទូទាំងប្រទេសកម្ពុជា",
            tab_shared_taxi: "Shared Taxi (រួមដំណើរ)",
            tab_private_charter: "Fleet & Charter (ម៉ៅដាច់)",
            tab_parcel_delivery: "Express Parcel (ផ្ញើឥវ៉ាន់)",
            popular_routes_title: "🔥 ជ្រើសរើសខ្សែរត់រហ័ស / Quick Route Filters:",
            chip_all_routes: "គ្រប់ខ្សែរត់ / All Routes",
            field_from_label: "ចេញដំណើរពី / Departure:",
            field_to_label: "ទៅកាន់ខេត្ត / Destination:",
            date_all: "គ្រប់ថ្ងៃ / All",
            date_today: "ថ្ងៃនេះ / Today",
            date_tomorrow: "ថ្ងៃស្អែក / Tomorrow",
            date_pick: "ជ្រើសថ្ងៃ",
            btn_search_rides: "ស្វែងរកឡានទំនេរ / Find Available Rides",
            available_cars_title: "រថយន្តដែលមានក្នុងប្រព័ន្ធ / Live Trips",
            banner_custom_title: "ត្រូវការឡានចេញម៉ោងផ្សេង ឬម៉ៅដាច់?",
            banner_custom_sub: "ប្រសិនបើគ្មានម៉ោងដែលត្រូវចិត្ត សូមផ្ញើសំណើកក់ឡានពិសេសតាមម៉ោងដែលអ្នកចង់បាន!",
            btn_custom_request: "ស្នើសុំឡាន",
            charter_title: "ប្រភេទរថយន្ត និងសេវាម៉ៅដាច់ VIP",
            charter_desc: "រថយន្តក្នុងប្រព័ន្ធ MyTravel ទទួលដល់ផ្ទះ ធ្វើដំណើរឯកជន ឬជាក្រុមគ្រួសារ",
            btn_book_charter: "ស្នើសុំម៉ៅដាច់រថយន្តនេះ",
            parcel_title: "សេវាផ្ញើឥវ៉ាន់រហ័សអន្តរខេត្ត",
            parcel_sub: "ផ្ញើព្រឹកបានថ្ងៃត្រង់ ឬផ្ញើរសៀលបានល្ងាច ផ្ញើផ្ទាល់ជាមួយអ្នកបើកបរតាក់ស៊ីក្នុងប្រព័ន្ធ",
            my_rides_title: "🎟️ សំបុត្រ និងការកក់របស់ខ្ញុំ",
            my_rides_subtitle: "ទិន្នន័យការកក់ពិតប្រាកដពីប្រព័ន្ធ MyTravel",
            lookup_phone_label: "លេខទូរស័ព្ទដែលបានកក់ / Your Booking Phone Number:",
            btn_sync_bookings: "ស្វែងរក",
            no_rides_title: "មិនទាន់មានការកក់នៅឡើយទេ",
            no_rides_sub: "បញ្ចូលលេខទូរស័ព្ទរបស់អ្នកខាងលើ ឬកក់រថយន្តដើម្បីមើលសំបុត្រឌីជីថលនៅទីនេះ។",
            support_center_title: "ផ្នែកបម្រើអតិថិជន MyTravel 24/7",
            support_center_desc: "ក្រុមការងារយើងខ្ញុំប្រចាំការនៅរាជធានីភ្នំពេញ ត្រៀមឆ្លើយតបគ្រប់សំណួរ និងជួយសម្រួលការធ្វើដំណើរ។",
            faq_title: "សំណួរដែលសួរញឹកញាប់ (FAQ)",
            faq_q1: "តើខ្ញុំត្រូវទូទាត់ប្រាក់តាមរបៀបណា?",
            faq_a1: "លោកអ្នកអាចទូទាត់ជា <strong>សាច់ប្រាក់សុទ្ធ (Cash on Pickup)</strong> ពេលឡើងឡាន ឬស្កេន <strong>ABA / KHQR</strong> ជាមួយអ្នកបើកបរផ្ទាល់។",
            faq_q2: "តើឡាននឹងទៅទទួលខ្ញុំនៅកន្លែងណា?",
            faq_a2: "MyTravel ផ្តល់ជូនសេវា <strong>ទទួលដល់ទីកន្លែង</strong> ឬតាមចំណតដែលបានកំណត់។ អ្នកបើកបរនឹងទូរស័ព្ទបញ្ជាក់ទីតាំងមុនពេលចេញដំណើរ។",
            faq_q3: "តើខ្ញុំអាចមើលទីតាំងឡានតាម GPS បានទេ?",
            faq_a3: "បាន! បន្ទាប់ពីកក់រួច លោកអ្នកអាចចុច 'បើកក្នុង MyTravel App' ដើម្បីមើលទីតាំង GPS របស់ឡានរត់ផ្ទាល់នៅលើផែនទី។",
            nav_book: "កក់តាក់ស៊ី",
            nav_charter: "រថយន្ត & ម៉ៅដាច់",
            nav_my_rides: "សំបុត្រខ្ញុំ",
            nav_support: "ជំនួយ 24/7",
            sheet_booking_title: "បញ្ជាក់ការកក់រថយន្ត",
            label_seat_count: "ជ្រើសរើសកៅអីទំនេរ / Select Seat(s):",
            unit_seats: "កៅអី / Seat(s)",
            label_name: "ឈ្មោះអ្នកដំណើរ / Passenger Name:",
            label_phone: "លេខទូរស័ព្ទ / Phone Number (Cambodia):",
            label_pickup: "ទីតាំងទទួល / Pickup Location (Hotel or Landmark):",
            label_payment: "វិធីសាស្ត្រទូទាត់ / Payment Method:",
            pay_cash: "💵 Cash (ពេលឡើងឡាន)",
            pay_khqr: "📱 ABA / KHQR",
            price_per_seat: "តម្លៃក្នុងមួយកៅអី / Rate per seat:",
            total_amount: "សរុបទាំងអស់ / Total Fare:",
            btn_confirm_now: "បញ្ជាក់ការកក់ភ្លាមៗ / Confirm Booking",
            ticket_booked_title: "ការកក់ជោគជ័យ! / Booking Confirmed!",
            ticket_booked_sub: "អ្នកបើកបរត្រូវបានជូនដំណឹងរួចរាល់ សូមរៀបចំខ្លួនធ្វើដំណើរ",
            ref_code_label: "លេខកូដកក់ / Ref Code",
            ticket_departure: "ម៉ោងចេញដំណើរ",
            ticket_seats: "លេខកៅអី",
            ticket_total: "តម្លៃសរុប",
            ticket_passenger: "អ្នកដំណើរ",
            btn_open_app_gps: "បើកក្នុង App ដើម្បីមើលទីតាំង GPS Live",
            btn_done: "រួចរាល់ / Done",
            custom_modal_title: "ស្នើសុំរថយន្តពិសេស / ម៉ៅដាច់",
            custom_modal_sub: "សំណើនឹងត្រូវបញ្ជូនទៅកាន់ប្រព័ន្ធប្រតិបត្តិការ MyTravel ផ្ទាល់",
            custom_label_route: "ខ្សែរត់ដែលស្នើសុំ / Requested Route:",
            custom_label_type: "ចំនួនកៅអី ឬប្រភេទរថយន្ត / Seats & Vehicle Type:",
            custom_label_note: "ម៉ោងចង់ចេញ និងទីតាំងទទួល / Preferred Time & Pickup:",
            btn_submit_request: "ផ្ញើសំណើកក់ / Submit Request",
            empty_trips_title: "មិនទាន់មានជើងរថយន្តសម្រាប់ខ្សែរត់នេះទេ",
            empty_trips_sub: "សូមជ្រើសរើស 'គ្រប់ខេត្តទាំងអស់' ដើម្បីមើលរថយន្តទាំងអស់ដែលកំពុងចេញដំណើរ ឬដាក់សំណើកក់ឡានផ្ទាល់។",
            btn_show_all_trips: "🌍 បង្ហាញជើងរថយន្តទាំងអស់ទូទាំងប្រទេស"
        },
        en: {
            dispatch_online: "Live 24/7 Inter-Province Dispatch",
            greeting_hello: "Hello",
            greeting_sub: "Real-time inter-province taxi & charter booking in Cambodia",
            tab_shared_taxi: "Shared Taxi",
            tab_private_charter: "Fleet & Charter",
            tab_parcel_delivery: "Express Parcel",
            popular_routes_title: "🔥 Quick Route Filters:",
            chip_all_routes: "All Active Routes",
            field_from_label: "Departure:",
            field_to_label: "Destination:",
            date_all: "All Dates",
            date_today: "Today",
            date_tomorrow: "Tomorrow",
            date_pick: "Pick Date",
            btn_search_rides: "Find Available Rides",
            available_cars_title: "Live Scheduled Trips",
            banner_custom_title: "Need a custom schedule or private car?",
            banner_custom_sub: "If no scheduled trip matches your route, submit a custom dispatch request in 1 tap!",
            btn_custom_request: "Request Ride",
            charter_title: "MyTravel Vehicle Fleet & VIP Charter",
            charter_desc: "Verified vehicles registered in MyTravel for private family or corporate travel.",
            btn_book_charter: "Request Private Charter",
            parcel_title: "Inter-City Express Parcel Delivery",
            parcel_sub: "Send packages between provinces with verified drivers for same-day delivery.",
            my_rides_title: "🎟️ My Bookings & Passes",
            my_rides_subtitle: "Live booking records synced from MyTravel database",
            lookup_phone_label: "Your Booking Phone Number:",
            btn_sync_bookings: "Search",
            no_rides_title: "No Bookings Found",
            no_rides_sub: "Enter your phone number above or book an available trip to view your pass.",
            support_center_title: "MyTravel 24/7 Customer Support",
            support_center_desc: "Our dispatch team in Phnom Penh is ready around the clock to assist your travels.",
            faq_title: "Frequently Asked Questions (FAQ)",
            faq_q1: "How do I pay for my ride?",
            faq_a1: "You can pay with <strong>Cash on Pickup</strong> or scan <strong>ABA / KHQR</strong> directly with your driver.",
            faq_q2: "Where will the driver pick me up?",
            faq_a2: "MyTravel provides <strong>door-to-door pickup</strong> or designated station pickup. The driver will call you to confirm.",
            faq_q3: "Can I track the driver on a live map?",
            faq_a3: "Yes! Once booked, tap 'Open in MyTravel App' for turn-by-turn live GPS tracking.",
            nav_book: "Book Taxi",
            nav_charter: "Fleet & Charter",
            nav_my_rides: "My Rides",
            nav_support: "Support",
            sheet_booking_title: "Confirm Your Ride",
            label_seat_count: "Select Available Seat(s):",
            unit_seats: "Seat(s)",
            label_name: "Passenger Name:",
            label_phone: "Phone Number (Cambodia):",
            label_pickup: "Pickup Location (Hotel or Landmark):",
            label_payment: "Payment Method:",
            pay_cash: "💵 Cash on Pickup",
            pay_khqr: "📱 ABA / KHQR",
            price_per_seat: "Rate per seat:",
            total_amount: "Total Fare:",
            btn_confirm_now: "Confirm Booking",
            ticket_booked_title: "Booking Confirmed!",
            ticket_booked_sub: "Your driver has been notified and your seat is reserved.",
            ref_code_label: "Booking Ref",
            ticket_departure: "Departure",
            ticket_seats: "Seat(s)",
            ticket_total: "Total Fare",
            ticket_passenger: "Passenger",
            btn_open_app_gps: "Open in MyTravel App for Live GPS",
            btn_done: "Done",
            custom_modal_title: "Request Custom Ride / Charter",
            custom_modal_sub: "Creates a live dispatch ticket for our operations team",
            custom_label_route: "Requested Route:",
            custom_label_type: "Seats & Vehicle Type:",
            custom_label_note: "Preferred Time & Pickup Location:",
            btn_submit_request: "Submit Request",
            empty_trips_title: "No Scheduled Trips for This Filter",
            empty_trips_sub: "Tap below to view all active trips across Cambodia or request a custom ride.",
            btn_show_all_trips: "🌍 Show All Available Trips Across Cambodia"
        }
    };

    let currentLang = 'km';
    const tgUser = tg?.initDataUnsafe?.user;
    if (localStorage.getItem('mytravel_lang')) {
        currentLang = localStorage.getItem('mytravel_lang');
    } else if (tgUser?.language_code === 'en') {
        currentLang = 'en';
    }

    const langLabel = document.getElementById('langLabel');
    const langToggleBtn = document.getElementById('langToggleBtn');

    let cachedTrips = [];
    let cachedVehicleModels = [];
    let cachedMyBookings = [];
    const EXCHANGE_RATE = 4100;

    function setLanguage(lang) {
        currentLang = lang;
        localStorage.setItem('mytravel_lang', lang);
        if (langLabel) langLabel.textContent = lang === 'km' ? 'ខ្មែរ' : 'English';

        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (i18n[lang] && i18n[lang][key]) {
                el.innerHTML = i18n[lang][key];
            }
        });

        renderTrips(cachedTrips);
        if (cachedVehicleModels.length > 0) {
            renderVehicleModels(cachedVehicleModels);
        }
        renderMyBookingsList(cachedMyBookings);
    }

    langToggleBtn?.addEventListener('click', () => {
        triggerHaptic('light');
        setLanguage(currentLang === 'km' ? 'en' : 'km');
    });

    // 4. USER IDENTITY & PHONE SYNC
    const userNameEl = document.getElementById('userName');
    const userAvatarEl = document.getElementById('userAvatar');
    const inputPassengerName = document.getElementById('inputPassengerName');
    const inputPassengerPhone = document.getElementById('inputPassengerPhone');
    const inputCustomName = document.getElementById('inputCustomName');
    const inputCustomPhone = document.getElementById('inputCustomPhone');
    const inputLookupPhone = document.getElementById('inputLookupPhone');

    if (tgUser) {
        const fullName = [tgUser.first_name, tgUser.last_name].filter(Boolean).join(' ');
        const displayName = fullName || tgUser.username || 'Traveler';
        if (userNameEl) userNameEl.textContent = displayName;
        if (inputPassengerName) inputPassengerName.value = displayName;
        if (inputCustomName) inputCustomName.value = displayName;
        if (tgUser.first_name && userAvatarEl) {
            userAvatarEl.textContent = tgUser.first_name.charAt(0).toUpperCase();
        }
    }

    const savedPhone = localStorage.getItem('mytravel_saved_phone') || '';
    if (savedPhone) {
        if (inputPassengerPhone) inputPassengerPhone.value = savedPhone;
        if (inputCustomPhone) inputCustomPhone.value = savedPhone;
        if (inputLookupPhone) inputLookupPhone.value = savedPhone;
    }

    function syncSavedPhone(phone) {
        if (!phone) return;
        localStorage.setItem('mytravel_saved_phone', phone);
        if (inputPassengerPhone && !inputPassengerPhone.value) inputPassengerPhone.value = phone;
        if (inputCustomPhone && !inputCustomPhone.value) inputCustomPhone.value = phone;
        if (inputLookupPhone && !inputLookupPhone.value) inputLookupPhone.value = phone;
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
            fetchMyBookings();
        } else if (targetTabId === 'tabCharter' && cachedVehicleModels.length === 0) {
            fetchVehicleModels();
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

    // 6. REAL PROVINCES API (/v1/api/addresses/provinces) & ROUTE FILTERS
    const selectDeparture = document.getElementById('selectDeparture');
    const selectDestination = document.getElementById('selectDestination');
    const btnSwapRoute = document.getElementById('btnSwapRoute');

    async function loadRealProvinces() {
        try {
            const res = await fetch('/v1/api/addresses/provinces');
            if (!res.ok) return;
            const provinces = await res.json();
            if (!Array.isArray(provinces) || provinces.length === 0) return;

            [selectDeparture, selectDestination].forEach(selectEl => {
                if (!selectEl) return;
                const currentVal = selectEl.value || 'all';
                const existingValues = new Set(
                    Array.from(selectEl.options).map(opt => opt.value.toLowerCase())
                );
                provinces.forEach(p => {
                    const enName = (p.name || '').trim();
                    const kmName = (p.description || '').trim();
                    if (!enName) return;
                    if (!existingValues.has(enName.toLowerCase())) {
                        const opt = document.createElement('option');
                        opt.value = enName;
                        opt.textContent = kmName ? `📍 ${enName} (${kmName})` : `📍 ${enName}`;
                        selectEl.appendChild(opt);
                        existingValues.add(enName.toLowerCase());
                    }
                });
                selectEl.value = currentVal;
            });
        } catch (err) {
            console.warn('Could not load provinces list:', err);
        }
    }

    document.querySelectorAll('.popular-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            triggerHaptic('light');
            document.querySelectorAll('.popular-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');

            const from = chip.getAttribute('data-from') || 'all';
            const to = chip.getAttribute('data-to') || 'all';
            if (selectDeparture) selectDeparture.value = from;
            if (selectDestination) selectDestination.value = to;

            fetchAvailableRides();
        });
    });

    btnSwapRoute?.addEventListener('click', () => {
        triggerHaptic('medium');
        const temp = selectDeparture.value;
        selectDeparture.value = selectDestination.value;
        selectDestination.value = temp;
        fetchAvailableRides();
    });

    selectDeparture?.addEventListener('change', () => {
        document.querySelectorAll('.popular-chip').forEach(c => c.classList.remove('active'));
        fetchAvailableRides();
    });
    selectDestination?.addEventListener('change', () => {
        document.querySelectorAll('.popular-chip').forEach(c => c.classList.remove('active'));
        fetchAvailableRides();
    });

    // 7. DATE SELECTION PILLS
    const nativeDateInput = document.getElementById('nativeDateInput');
    const datePickLabel = document.getElementById('datePickLabel');
    let selectedDateFilter = 'all'; // 'all', 'today', 'tomorrow', or 'YYYY-MM-DD'

    function getFormattedDateString(offsetDays = 0) {
        const d = new Date();
        d.setDate(d.getDate() + offsetDays);
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}`;
    }

    document.querySelectorAll('.date-selector-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            triggerHaptic('light');
            document.querySelectorAll('.date-selector-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');

            const dateType = pill.getAttribute('data-date');
            if (dateType === 'custom') {
                nativeDateInput?.showPicker?.() || nativeDateInput?.click();
            } else if (dateType === 'today') {
                selectedDateFilter = getFormattedDateString(0);
                if (datePickLabel) datePickLabel.textContent = i18n[currentLang].date_pick;
                fetchAvailableRides();
            } else if (dateType === 'tomorrow') {
                selectedDateFilter = getFormattedDateString(1);
                if (datePickLabel) datePickLabel.textContent = i18n[currentLang].date_pick;
                fetchAvailableRides();
            } else {
                selectedDateFilter = 'all';
                if (datePickLabel) datePickLabel.textContent = i18n[currentLang].date_pick;
                fetchAvailableRides();
            }
        });
    });

    nativeDateInput?.addEventListener('change', (e) => {
        if (e.target.value) {
            selectedDateFilter = e.target.value;
            if (datePickLabel) datePickLabel.textContent = e.target.value;
            fetchAvailableRides();
        }
    });

    // 8. CURRENCY & DATE/TIME HELPERS FOR REAL TRIP DATA
    function formatTripPrice(amount, currency) {
        const num = Number(amount || 0);
        const curr = String(currency || 'KHR').toUpperCase();
        const isKhr = curr === 'KHR' || curr === '៛' || num >= 1000;
        if (isKhr) {
            const khrVal = Math.round(num);
            const usdVal = (num / EXCHANGE_RATE).toFixed(2);
            return {
                primary: `${khrVal.toLocaleString()} ៛`,
                secondary: `≈ $${usdVal}`,
                isKhr: true,
                rawUnit: num,
                currency: 'KHR'
            };
        } else {
            const usdVal = num.toFixed(2);
            const khrVal = Math.round(num * EXCHANGE_RATE).toLocaleString();
            return {
                primary: `$${usdVal}`,
                secondary: `${khrVal} ៛`,
                isKhr: false,
                rawUnit: num,
                currency: 'USD'
            };
        }
    }

    function formatDateTimeShort(isoString) {
        if (!isoString) return '-';
        try {
            const d = new Date(isoString);
            if (isNaN(d.getTime())) return isoString;
            const datePart = d.toLocaleDateString([], { month: 'short', day: 'numeric' });
            const timePart = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
            return `${datePart}, ${timePart}`;
        } catch (e) {
            return isoString;
        }
    }

    // 9. FETCH & RENDER REAL PUBLIC TRIPS (/v1/api/travel/trips/public)
    const btnSearchRides = document.getElementById('btnSearchRides');
    const btnRefreshList = document.getElementById('btnRefreshList');
    const ridesListContainer = document.getElementById('ridesListContainer');
    const liveCarsCount = document.getElementById('liveCarsCount');

    btnSearchRides?.addEventListener('click', () => {
        triggerHaptic('medium');
        fetchAvailableRides();
    });

    btnRefreshList?.addEventListener('click', () => {
        triggerHaptic('medium');
        fetchAvailableRides();
    });

    async function fetchAvailableRides() {
        const from = selectDeparture?.value || 'all';
        const to = selectDestination?.value || 'all';

        ridesListContainer.innerHTML = `
            <div class="ride-card skeleton-box">
                <div class="sk-line sk-title"></div>
                <div class="sk-line sk-body"></div>
                <div class="sk-line sk-btn"></div>
            </div>
        `;
        if (liveCarsCount) liveCarsCount.textContent = '...';

        try {
            const params = new URLSearchParams();
            if (from && from !== 'all') params.set('departure_province', from);
            if (to && to !== 'all') params.set('destination_province', to);
            if (selectedDateFilter && selectedDateFilter !== 'all') {
                params.set('journey_date', selectedDateFilter);
            }
            params.set('limit', '60');

            const res = await fetch(`/v1/api/travel/trips/public?${params.toString()}`);
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }
            const data = await res.json();
            cachedTrips = Array.isArray(data) ? data : [];
            renderTrips(cachedTrips);
        } catch (err) {
            console.error('Failed to fetch real trips:', err);
            cachedTrips = [];
            renderTrips([]);
        }
    }

    function renderTrips(trips) {
        if (!ridesListContainer) return;
        if (liveCarsCount) liveCarsCount.textContent = String(trips.length);

        if (trips.length === 0) {
            const isFiltered = (selectDeparture?.value !== 'all') || (selectDestination?.value !== 'all') || (selectedDateFilter !== 'all');
            ridesListContainer.innerHTML = `
                <div class="empty-state-box">
                    <i class="fa-solid fa-car-Rear" style="font-size:2rem; color:var(--taxi-yellow);"></i>
                    <h4>${i18n[currentLang].empty_trips_title}</h4>
                    <p>${i18n[currentLang].empty_trips_sub}</p>
                    ${isFiltered ? `
                        <button type="button" id="btnResetTripFilters" class="btn-primary-yellow" style="margin-top:10px; padding:10px 16px; font-size:0.86rem;">
                            <span>${i18n[currentLang].btn_show_all_trips}</span>
                        </button>
                    ` : ''}
                </div>
            `;
            document.getElementById('btnResetTripFilters')?.addEventListener('click', () => {
                triggerHaptic('light');
                if (selectDeparture) selectDeparture.value = 'all';
                if (selectDestination) selectDestination.value = 'all';
                selectedDateFilter = 'all';
                document.querySelectorAll('.popular-chip').forEach(c => {
                    c.classList.toggle('active', c.getAttribute('data-from') === 'all');
                });
                document.querySelectorAll('.date-selector-pill').forEach(p => {
                    p.classList.toggle('active', p.getAttribute('data-date') === 'all');
                });
                fetchAvailableRides();
            });
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

        const driverName = trip.driver?.full_name || 'Verified Driver';
        const ratingAvg = trip.driver?.rating_avg ? Number(trip.driver.rating_avg).toFixed(1) : null;
        const completedTrips = trip.driver?.completed_trips || 0;
        const vehicleModel = trip.vehicle?.model || trip.vehicle?.type || 'Taxi';
        const plateNumber = trip.vehicle?.plate_number || '';
        const vehicleDisplay = plateNumber ? `${vehicleModel} (${plateNumber})` : vehicleModel;
        const timeStr = formatDateTimeShort(trip.departure_time);
        const availableSeats = typeof trip.available_seats === 'number' ? trip.available_seats : (trip.available_seat_numbers?.length || 0);
        const totalSeats = trip.total_seats || availableSeats;
        const priceInfo = formatTripPrice(trip.price_per_seat, trip.currency);

        const pickupLabel = trip.pickup_stop?.stop_label || trip.departure_province;
        const dropoffLabel = trip.dropoff_stop?.stop_label || trip.destination_province;
        const isLive = trip.status === 'active';

        card.innerHTML = `
            <div class="trip-route-banner">
                <span>📍 ${trip.departure_province} ➔ ${trip.destination_province}</span>
                <span style="font-size:0.74rem; color:${isLive ? 'var(--success-color)' : 'var(--taxi-yellow)'};">
                    ${isLive ? '🟢 កំពុងចេញដំណើរ / Active' : '🗓 Scheduled'}
                </span>
            </div>
            ${(pickupLabel !== trip.departure_province || dropoffLabel !== trip.destination_province) ? `
                <div class="route-stop-sub">
                    <i class="fa-solid fa-route"></i>
                    <span>${pickupLabel} ➔ ${dropoffLabel}</span>
                </div>
            ` : ''}
            <div class="ride-card-top" style="margin-top:4px;">
                <div class="driver-profile-row">
                    <div class="driver-avatar-circle">
                        <i class="fa-solid fa-user-tie"></i>
                    </div>
                    <div class="driver-name-col">
                        <strong>${driverName} ${trip.driver?.is_verified !== false ? '<i class="fa-solid fa-circle-check verified-badge" title="Verified"></i>' : ''}</strong>
                        <div class="driver-stars-row">
                            ${ratingAvg ? `⭐ ${ratingAvg}` : '⭐ Verified'}
                            ${completedTrips > 0 ? ` • ${completedTrips} Trips` : ''}
                        </div>
                    </div>
                </div>
                <div class="dep-time-badge">
                    <i class="fa-regular fa-clock"></i> <span>${timeStr}</span>
                </div>
            </div>
            <div class="ride-card-mid">
                <div class="car-model-name">
                    <i class="fa-solid fa-car"></i> <span>${vehicleDisplay}</span>
                </div>
                <div class="seats-remaining">
                    <i class="fa-solid fa-chair"></i> <span>${availableSeats}/${totalSeats} ${i18n[currentLang].unit_seats}</span>
                </div>
            </div>
            <div class="ride-card-bottom">
                <div class="fare-display-group">
                    <span class="fare-usd">${priceInfo.primary}</span>
                    <span class="fare-khr">${priceInfo.secondary} / seat</span>
                </div>
                <button type="button" class="btn-book-seat" ${availableSeats <= 0 ? 'disabled style="opacity:0.5;cursor:not-allowed;"' : ''}>
                    <span>${availableSeats <= 0 ? (currentLang === 'km' ? 'ពេញហើយ' : 'Full') : (currentLang === 'km' ? 'កក់កៅអី' : 'Book Seat')}</span>
                    <i class="fa-solid fa-arrow-right"></i>
                </button>
            </div>
        `;

        if (availableSeats > 0) {
            card.querySelector('.btn-book-seat')?.addEventListener('click', () => {
                triggerHaptic('medium');
                openBookingModal(trip);
            });
        }

        return card;
    }

    // 10. BOOKING BOTTOM SHEET WITH INTERACTIVE SEAT PICKER
    const bookingModal = document.getElementById('bookingModal');
    const btnCloseBookingModal = document.getElementById('btnCloseBookingModal');
    const bookingErrorAlert = document.getElementById('bookingErrorAlert');
    const modalRouteSummary = document.getElementById('modalRouteSummary');
    const modalDriverName = document.getElementById('modalDriverName');
    const modalCarSpec = document.getElementById('modalCarSpec');
    const modalDepartureTime = document.getElementById('modalDepartureTime');
    const modalAvailableSeatsTag = document.getElementById('modalAvailableSeatsTag');
    const seatPickerGrid = document.getElementById('seatPickerGrid');
    const modalPricePerSeat = document.getElementById('modalPricePerSeat');
    const modalTotalUsd = document.getElementById('modalTotalUsd');
    const modalTotalKhr = document.getElementById('modalTotalKhr');
    const seatCountNumber = document.getElementById('seatCountNumber');
    const btnMinusSeat = document.getElementById('btnMinusSeat');
    const btnPlusSeat = document.getElementById('btnPlusSeat');
    const inputPickupNote = document.getElementById('inputPickupNote');
    const btnSubmitBooking = document.getElementById('btnSubmitBooking');

    let currentSelectedTrip = null;
    let selectedSeatNumbers = [];

    function getTripAvailableSeatNumbers(trip) {
        if (Array.isArray(trip.available_seat_numbers) && trip.available_seat_numbers.length > 0) {
            return trip.available_seat_numbers;
        }
        const total = trip.total_seats || trip.available_seats || 4;
        const booked = new Set(Array.isArray(trip.booked_seat_numbers) ? trip.booked_seat_numbers : []);
        const avail = [];
        for (let i = 1; i <= total; i++) {
            if (!booked.has(i)) avail.push(i);
        }
        return avail;
    }

    function renderSeatChips() {
        if (!seatPickerGrid || !currentSelectedTrip) return;
        const total = currentSelectedTrip.total_seats || currentSelectedTrip.available_seats || 4;
        const availSet = new Set(getTripAvailableSeatNumbers(currentSelectedTrip));
        seatPickerGrid.innerHTML = '';

        for (let i = 1; i <= total; i++) {
            const isAvail = availSet.has(i);
            const isSelected = selectedSeatNumbers.includes(i);
            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = `seat-chip ${!isAvail ? 'booked' : ''} ${isSelected ? 'selected' : ''}`;
            chip.disabled = !isAvail;
            chip.innerHTML = `<i class="fa-solid fa-chair"></i> #${i}`;
            if (isAvail) {
                chip.addEventListener('click', () => {
                    triggerHaptic('light');
                    if (selectedSeatNumbers.includes(i)) {
                        if (selectedSeatNumbers.length > 1) {
                            selectedSeatNumbers = selectedSeatNumbers.filter(s => s !== i);
                        }
                    } else {
                        selectedSeatNumbers.push(i);
                        selectedSeatNumbers.sort((a, b) => a - b);
                    }
                    if (seatCountNumber) seatCountNumber.textContent = String(selectedSeatNumbers.length);
                    renderSeatChips();
                    updateTotals();
                });
            }
            seatPickerGrid.appendChild(chip);
        }
    }

    function openBookingModal(trip) {
        currentSelectedTrip = trip;
        if (bookingErrorAlert) {
            bookingErrorAlert.style.display = 'none';
            bookingErrorAlert.textContent = '';
        }

        const availSeats = getTripAvailableSeatNumbers(trip);
        selectedSeatNumbers = availSeats.length > 0 ? [availSeats[0]] : [1];
        if (seatCountNumber) seatCountNumber.textContent = String(selectedSeatNumbers.length);

        if (modalRouteSummary) {
            modalRouteSummary.textContent = `${trip.departure_province} ➔ ${trip.destination_province}`;
        }
        if (modalDriverName) {
            modalDriverName.textContent = trip.driver?.full_name || 'Verified Driver';
        }
        if (modalCarSpec) {
            const model = trip.vehicle?.model || trip.vehicle?.type || 'Taxi';
            const plate = trip.vehicle?.plate_number ? ` • ${trip.vehicle.plate_number}` : '';
            modalCarSpec.textContent = `${model}${plate}`;
        }
        if (modalDepartureTime) {
            modalDepartureTime.textContent = formatDateTimeShort(trip.departure_time);
        }
        if (modalAvailableSeatsTag) {
            modalAvailableSeatsTag.textContent = `${availSeats.length} ${i18n[currentLang].unit_seats}`;
        }

        const unitPriceInfo = formatTripPrice(trip.price_per_seat, trip.currency);
        if (modalPricePerSeat) {
            modalPricePerSeat.textContent = `${unitPriceInfo.primary} (${unitPriceInfo.secondary})`;
        }

        renderSeatChips();
        updateTotals();
        if (bookingModal) bookingModal.style.display = 'flex';
    }

    function closeBookingModal() {
        if (bookingModal) bookingModal.style.display = 'none';
    }

    btnCloseBookingModal?.addEventListener('click', closeBookingModal);

    function updateTotals() {
        if (!currentSelectedTrip) return;
        const count = Math.max(1, selectedSeatNumbers.length);
        const unitRaw = Number(currentSelectedTrip.price_per_seat || 0);
        const totalRaw = unitRaw * count;
        const totalInfo = formatTripPrice(totalRaw, currentSelectedTrip.currency);
        if (modalTotalUsd) modalTotalUsd.textContent = totalInfo.primary;
        if (modalTotalKhr) modalTotalKhr.textContent = `(${totalInfo.secondary})`;
    }

    btnMinusSeat?.addEventListener('click', () => {
        triggerHaptic('light');
        if (selectedSeatNumbers.length > 1) {
            selectedSeatNumbers.pop();
            if (seatCountNumber) seatCountNumber.textContent = String(selectedSeatNumbers.length);
            renderSeatChips();
            updateTotals();
        }
    });

    btnPlusSeat?.addEventListener('click', () => {
        triggerHaptic('light');
        if (!currentSelectedTrip) return;
        const availSeats = getTripAvailableSeatNumbers(currentSelectedTrip);
        if (selectedSeatNumbers.length < availSeats.length) {
            const nextSeat = availSeats.find(s => !selectedSeatNumbers.includes(s));
            if (nextSeat !== undefined) {
                selectedSeatNumbers.push(nextSeat);
                selectedSeatNumbers.sort((a, b) => a - b);
                if (seatCountNumber) seatCountNumber.textContent = String(selectedSeatNumbers.length);
                renderSeatChips();
                updateTotals();
            }
        }
    });

    document.querySelectorAll('.pay-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            triggerHaptic('light');
            document.querySelectorAll('.pay-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            const radio = pill.querySelector('input[type="radio"]');
            if (radio) radio.checked = true;
        });
    });

    // 11. SUBMIT REAL BOOKING ORDER (/v1/api/travel/telegram/miniapp/quick-book)
    async function submitBookingOrder() {
        if (!currentSelectedTrip || !currentSelectedTrip.id) return;

        const name = inputPassengerName?.value.trim() || '';
        const phone = inputPassengerPhone?.value.trim() || '';
        const pickup = inputPickupNote?.value.trim() || '';
        const payRadio = document.querySelector('input[name="payMethod"]:checked');
        const paymentMethod = payRadio ? payRadio.value : 'cash';

        if (bookingErrorAlert) {
            bookingErrorAlert.style.display = 'none';
            bookingErrorAlert.textContent = '';
        }

        if (!name || name.length < 2) {
            triggerHaptic('error');
            if (bookingErrorAlert) {
                bookingErrorAlert.textContent = currentLang === 'km' ? 'សូមបញ្ចូលឈ្មោះអ្នកដំណើរ' : 'Please enter passenger name.';
                bookingErrorAlert.style.display = 'block';
            }
            inputPassengerName?.focus();
            return;
        }

        if (!phone || phone.length < 6) {
            triggerHaptic('error');
            if (bookingErrorAlert) {
                bookingErrorAlert.textContent = currentLang === 'km' ? 'សូមបញ្ចូលលេខទូរស័ព្ទត្រឹមត្រូវ' : 'Please enter a valid phone number.';
                bookingErrorAlert.style.display = 'block';
            }
            inputPassengerPhone?.focus();
            return;
        }

        syncSavedPhone(phone);
        triggerHaptic('medium');

        btnSubmitBooking.disabled = true;
        btnSubmitBooking.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Booking...</span>`;

        const payload = {
            trip_id: String(currentSelectedTrip.id),
            seat_count: selectedSeatNumbers.length,
            seat_numbers: selectedSeatNumbers,
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

            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                throw new Error(data.detail || `Booking failed (HTTP ${res.status})`);
            }

            closeBookingModal();
            openTicketPass(data);
            triggerHaptic('success');

            // Refresh real trips & real bookings from backend DB
            fetchAvailableRides();
            fetchMyBookings();
        } catch (err) {
            triggerHaptic('error');
            if (bookingErrorAlert) {
                bookingErrorAlert.textContent = err.message || 'Could not complete booking. Please try again.';
                bookingErrorAlert.style.display = 'block';
            }
        } finally {
            btnSubmitBooking.disabled = false;
            btnSubmitBooking.innerHTML = `<i class="fa-solid fa-circle-check"></i> <span>${i18n[currentLang].btn_confirm_now}</span>`;
        }
    }

    btnSubmitBooking?.addEventListener('click', submitBookingOrder);

    // 12. DIGITAL BOARDING PASS MODAL (REAL BOOKING RECORD)
    const ticketModal = document.getElementById('ticketModal');
    const passRefCode = document.getElementById('passRefCode');
    const passStatusBadge = document.getElementById('passStatusBadge');
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
        if (passRefCode) passRefCode.textContent = booking.reference_code || `MT-${String(booking.booking_id || '').slice(0, 6).toUpperCase()}`;
        if (passStatusBadge) {
            const st = String(booking.status || 'confirmed').toLowerCase();
            passStatusBadge.textContent = st === 'cancelled' ? 'Cancelled 🔴' : (st === 'pending' ? 'Pending 🟡' : 'Confirmed 🟢');
        }
        if (passFromProvince) passFromProvince.textContent = booking.departure_province || '-';
        if (passToProvince) passToProvince.textContent = booking.destination_province || '-';
        if (passDepartureTime) passDepartureTime.textContent = formatDateTimeShort(booking.departure_time);

        const seatsArr = Array.isArray(booking.seat_numbers) && booking.seat_numbers.length > 0
            ? booking.seat_numbers.map(s => `#${s}`).join(', ')
            : `${booking.seat_count || 1}`;
        if (passSeatCount) passSeatCount.textContent = `${seatsArr} (${booking.seat_count || 1} ${i18n[currentLang].unit_seats})`;

        const priceInfo = formatTripPrice(booking.total_price, booking.currency);
        const payLabel = String(booking.payment_method || 'cash').toUpperCase();
        if (passTotalPrice) passTotalPrice.textContent = `${priceInfo.primary} (${payLabel})`;
        if (passPassengerName) passPassengerName.textContent = booking.passenger_name || '-';

        if (passDriverName) passDriverName.textContent = booking.driver_name || 'Verified Driver';
        const vehicleParts = [booking.vehicle_model, booking.plate_number].filter(Boolean);
        if (passCarModel) passCarModel.textContent = vehicleParts.length > 0 ? vehicleParts.join(' • ') : '-';

        if (btnCallDriver) {
            if (booking.driver_phone) {
                btnCallDriver.href = `tel:${booking.driver_phone}`;
                btnCallDriver.style.display = 'flex';
            } else {
                btnCallDriver.style.display = 'none';
            }
        }

        if (ticketModal) ticketModal.style.display = 'flex';

        if (btnOpenInApp) {
            btnOpenInApp.onclick = () => {
                triggerHaptic('medium');
                const schemeUrl = `mytravel://booking/${booking.booking_id || ''}`;
                window.location.href = schemeUrl;
                setTimeout(() => {
                    window.location.href = '/app';
                }, 1200);
            };
        }
    }

    btnCloseTicket?.addEventListener('click', () => {
        triggerHaptic('light');
        if (ticketModal) ticketModal.style.display = 'none';
    });

    // 13. REAL VEHICLE MODELS FLEET (/v1/api/travel/vehicle-models)
    const vehicleModelsContainer = document.getElementById('vehicleModelsContainer');

    async function fetchVehicleModels() {
        if (!vehicleModelsContainer) return;
        try {
            const res = await fetch('/v1/api/travel/vehicle-models');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const models = await res.json();
            cachedVehicleModels = Array.isArray(models) ? models : [];
            renderVehicleModels(cachedVehicleModels);
        } catch (err) {
            console.error('Failed to load vehicle models:', err);
            vehicleModelsContainer.innerHTML = `
                <div class="empty-state-box">
                    <i class="fa-solid fa-car-side"></i>
                    <p>Unable to load vehicle fleet right now.</p>
                </div>
            `;
        }
    }

    function renderVehicleModels(models) {
        if (!vehicleModelsContainer) return;
        if (models.length === 0) {
            vehicleModelsContainer.innerHTML = `
                <div class="empty-state-box">
                    <i class="fa-solid fa-car-side"></i>
                    <p>No active vehicle models configured.</p>
                </div>
            `;
            return;
        }

        vehicleModelsContainer.innerHTML = '';
        models.forEach((vm, idx) => {
            const card = document.createElement('div');
            card.className = `charter-card ${idx === 0 ? 'featured' : ''}`;
            const typeLabel = (vm.vehicle_type || 'VIP').toUpperCase();
            const seatCount = vm.seat_count || 4;
            const title = vm.display_name || `${vm.brand} ${vm.model_name}`;

            card.innerHTML = `
                <div class="charter-card-top">
                    <div class="car-badge ${idx === 0 ? 'bg-yellow' : 'bg-gold'}">${typeLabel} • ${seatCount} SEATS</div>
                    <div class="charter-price-tag">
                        <span class="price-val">${vm.brand}</span>
                        <span class="price-sub">${vm.model_name}</span>
                    </div>
                </div>
                <div class="car-photo-placeholder suv-bg" style="height:84px;">
                    <i class="fa-solid ${seatCount >= 7 ? 'fa-van-shuttle' : 'fa-car-side'}"></i>
                    <span>${title}</span>
                </div>
                <ul class="charter-features">
                    <li><i class="fa-solid fa-check text-success"></i> សម្រាប់អ្នកដំណើររហូតដល់ ${seatCount} កៅអី (${seatCount} Seats)</li>
                    <li><i class="fa-solid fa-check text-success"></i> ទទួលដល់ផ្ទះ និងជូនដល់គោលដៅផ្ទាល់ (Door-to-Door)</li>
                </ul>
                <button type="button" class="btn-charter-action ${idx === 0 ? 'btn-highlight' : ''}">
                    <span>${i18n[currentLang].btn_book_charter}</span>
                </button>
            `;

            card.querySelector('.btn-charter-action')?.addEventListener('click', () => {
                triggerHaptic('medium');
                openCustomRequestModal({
                    seats: seatCount,
                    notePrefix: `Charter Vehicle: ${title} (${seatCount} seats)`
                });
            });

            vehicleModelsContainer.appendChild(card);
        });
    }

    // 14. CUSTOM ON-DEMAND / CHARTER DISPATCH REQUEST (/v1/api/travel/telegram/miniapp/custom-request)
    const customModal = document.getElementById('customModal');
    const btnOpenCustomModal = document.getElementById('btnOpenCustomModal');
    const btnRequestParcel = document.getElementById('btnRequestParcel');
    const btnCloseCustomModal = document.getElementById('btnCloseCustomModal');
    const customRouteSummary = document.getElementById('customRouteSummary');
    const selectCustomType = document.getElementById('selectCustomType');
    const inputCustomNote = document.getElementById('inputCustomNote');
    const btnSubmitCustom = document.getElementById('btnSubmitCustom');

    function openCustomRequestModal(opts = {}) {
        const from = (selectDeparture?.value && selectDeparture.value !== 'all') ? selectDeparture.value : 'Phnom Penh';
        const to = (selectDestination?.value && selectDestination.value !== 'all') ? selectDestination.value : 'Siem Reap';
        if (customRouteSummary) customRouteSummary.textContent = `${from} ➔ ${to}`;
        if (opts.seats && selectCustomType) {
            selectCustomType.value = String(opts.seats);
        }
        if (opts.notePrefix && inputCustomNote) {
            inputCustomNote.value = opts.notePrefix;
        }
        if (customModal) customModal.style.display = 'flex';
    }

    btnOpenCustomModal?.addEventListener('click', () => {
        triggerHaptic('medium');
        openCustomRequestModal();
    });

    btnRequestParcel?.addEventListener('click', () => {
        triggerHaptic('medium');
        openCustomRequestModal({
            seats: 1,
            notePrefix: 'Express Parcel Delivery / ផ្ញើឥវ៉ាន់រហ័ស'
        });
    });

    btnCloseCustomModal?.addEventListener('click', () => {
        if (customModal) customModal.style.display = 'none';
    });

    btnSubmitCustom?.addEventListener('click', async () => {
        const name = inputCustomName?.value.trim() || '';
        const phone = inputCustomPhone?.value.trim() || '';
        const note = inputCustomNote?.value.trim() || '';
        const seats = Number(selectCustomType?.value || 4);
        const from = (selectDeparture?.value && selectDeparture.value !== 'all') ? selectDeparture.value : 'Phnom Penh';
        const to = (selectDestination?.value && selectDestination.value !== 'all') ? selectDestination.value : 'Siem Reap';

        if (!name || !phone || phone.length < 6) {
            triggerHaptic('error');
            alert(currentLang === 'km' ? 'សូមបញ្ចូលឈ្មោះ និងលេខទូរស័ព្ទត្រឹមត្រូវ' : 'Please enter your name and valid phone number.');
            return;
        }

        syncSavedPhone(phone);
        triggerHaptic('medium');
        btnSubmitCustom.disabled = true;
        btnSubmitCustom.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Submitting...`;

        try {
            const res = await fetch('/v1/api/travel/telegram/miniapp/custom-request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    departure_province: from,
                    destination_province: to,
                    passenger_name: name,
                    phone: phone,
                    requested_seats: seats,
                    note: note,
                    telegram_user_id: tgUser?.id ? String(tgUser.id) : null
                })
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                throw new Error(data.detail || `Request failed (${res.status})`);
            }
            if (customModal) customModal.style.display = 'none';
            triggerHaptic('success');
            alert(
                currentLang === 'km'
                    ? `សំណើកក់របស់អ្នក (${data.reference_code}) ត្រូវបានកត់ត្រាក្នុងប្រព័ន្ធ! ក្រុមការងារនឹងទាក់ទងមកលោកអ្នកភ្លាមៗ។`
                    : `Your request (${data.reference_code}) has been recorded! Our team will contact you shortly.`
            );
        } catch (err) {
            triggerHaptic('error');
            alert(err.message || 'Failed to submit request.');
        } finally {
            btnSubmitCustom.disabled = false;
            btnSubmitCustom.innerHTML = `<i class="fa-solid fa-paper-plane"></i> <span>${i18n[currentLang].btn_submit_request}</span>`;
        }
    });

    // 15. REAL MY BOOKINGS SYNC (/v1/api/travel/telegram/miniapp/my-bookings)
    const myRidesListContainer = document.getElementById('myRidesListContainer');
    const ridesBadge = document.getElementById('ridesBadge');
    const btnSyncMyBookings = document.getElementById('btnSyncMyBookings');

    btnSyncMyBookings?.addEventListener('click', () => {
        triggerHaptic('light');
        const typedPhone = inputLookupPhone?.value.trim() || '';
        if (typedPhone) syncSavedPhone(typedPhone);
        fetchMyBookings();
    });

    async function fetchMyBookings() {
        const phone = (inputLookupPhone?.value.trim()) || localStorage.getItem('mytravel_saved_phone') || '';
        const tgId = tgUser?.id ? String(tgUser.id) : '';

        if (!phone && !tgId) {
            cachedMyBookings = [];
            renderMyBookingsList([]);
            return;
        }

        try {
            const params = new URLSearchParams();
            if (phone) params.set('phone', phone);
            if (tgId) params.set('telegram_user_id', tgId);
            params.set('limit', '25');

            const res = await fetch(`/v1/api/travel/telegram/miniapp/my-bookings?${params.toString()}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const list = await res.json();
            cachedMyBookings = Array.isArray(list) ? list : [];
            if (cachedMyBookings.length > 0 && cachedMyBookings[0].phone) {
                syncSavedPhone(cachedMyBookings[0].phone);
            }
            renderMyBookingsList(cachedMyBookings);
        } catch (err) {
            console.error('Failed to load real bookings:', err);
            renderMyBookingsList(cachedMyBookings);
        }
    }

    function renderMyBookingsList(list) {
        if (ridesBadge) {
            if (list.length > 0) {
                ridesBadge.style.display = 'inline-block';
                ridesBadge.textContent = String(list.length);
            } else {
                ridesBadge.style.display = 'none';
            }
        }

        if (!myRidesListContainer) return;

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
            const priceInfo = formatTripPrice(bk.total_price, bk.currency);
            const statusText = bk.status === 'cancelled' ? 'Cancelled 🔴' : 'Confirmed 🟢';
            const seatText = Array.isArray(bk.seat_numbers) && bk.seat_numbers.length > 0
                ? bk.seat_numbers.map(s => `#${s}`).join(', ')
                : `${bk.seat_count || 1} Seat(s)`;

            card.innerHTML = `
                <div class="pass-top-row">
                    <div>
                        <span class="pass-label">${bk.reference_code || 'MT-PASS'}</span>
                        <strong style="font-size:1rem; color:var(--text-primary); display:block;">${bk.departure_province} ➔ ${bk.destination_province}</strong>
                    </div>
                    <span class="pass-status-badge">${statusText}</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.82rem; color:var(--text-secondary); background:var(--card-elevated); padding:8px 12px; border-radius:var(--radius-sm);">
                    <span><i class="fa-regular fa-clock"></i> ${formatDateTimeShort(bk.departure_time)} • 💺 ${seatText}</span>
                    <strong style="color:var(--taxi-yellow); font-size:0.95rem;">${priceInfo.primary}</strong>
                </div>
                <button type="button" class="btn-secondary-soft" style="padding:8px 14px; font-size:0.84rem;">
                    <i class="fa-solid fa-receipt"></i> <span>${currentLang === 'km' ? 'បង្ហាញសំបុត្រឌីជីថល' : 'View Digital Pass'}</span>
                </button>
            `;

            card.querySelector('button')?.addEventListener('click', () => {
                triggerHaptic('light');
                openTicketPass(bk);
            });

            myRidesListContainer.appendChild(card);
        });
    }

    // 16. REAL SUPPORT CONFIG (/v1/api/travel/support/config)
    async function fetchSupportConfig() {
        try {
            const res = await fetch('/v1/api/travel/support/config');
            if (!res.ok) return;
            const cfg = await res.json();
            if (cfg.support_phone) {
                const phoneBtn = document.getElementById('supportPhoneBtn');
                const phoneVal = document.getElementById('supportPhoneVal');
                const parcelLink = document.getElementById('parcelSupportPhoneLink');
                const parcelText = document.getElementById('parcelSupportPhoneText');
                if (phoneBtn) phoneBtn.href = `tel:${cfg.support_phone}`;
                if (phoneVal) phoneVal.textContent = cfg.support_phone;
                if (parcelLink) parcelLink.href = `tel:${cfg.support_phone}`;
                if (parcelText) parcelText.textContent = `Hotline: ${cfg.support_phone}`;
            }
            if (cfg.telegram_url || cfg.telegram_username) {
                const tgBtn = document.getElementById('supportTelegramBtn');
                const tgVal = document.getElementById('supportTelegramVal');
                if (tgBtn && cfg.telegram_url) tgBtn.href = cfg.telegram_url;
                if (tgVal && cfg.telegram_username) {
                    tgVal.textContent = cfg.telegram_username.startsWith('@') ? cfg.telegram_username : `@${cfg.telegram_username}`;
                }
            }
            const noteEl = document.getElementById('supportNoteText');
            if (noteEl) {
                const note = currentLang === 'km' ? cfg.note_km : cfg.note_en;
                if (note) noteEl.textContent = note;
            }
        } catch (err) {
            console.warn('Support config fetch skipped:', err);
        }
    }

    // INITIALIZE MINI APP WITH REAL APIS
    setLanguage(currentLang);
    loadRealProvinces();
    fetchAvailableRides();
    fetchVehicleModels();
    fetchMyBookings();
    fetchSupportConfig();

})();
