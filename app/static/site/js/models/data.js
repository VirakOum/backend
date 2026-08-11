/**
 * MyTravel Public Website Data Model (MVC - Model)
 * Contains Cambodian geographical routes, fare matrix, vehicle specs,
 * system statistics, FAQs, and bilingual localization strings.
 */

window.MyTravelData = {
    // Current Exchange Rate: 1 USD = 4,100 KHR
    KHR_RATE: 4100,

    // Complete 25 Cambodian Destination Hubs with Geographic Coordinates & Highways
    PROVINCES: [
        { id: "PP", name_en: "Phnom Penh", name_km: "ភ្នំពេញ", lat: 11.5564, lng: 104.9282, hwy: "NR6 / E4" },
        { id: "SR", name_en: "Siem Reap", name_km: "សៀមរាប", lat: 13.3671, lng: 103.8448, hwy: "NR6" },
        { id: "SHV", name_en: "Preah Sihanouk (Sihanoukville)", name_km: "ព្រះសីហនុ", lat: 10.6256, lng: 103.5234, hwy: "Expressway E4 / NR4" },
        { id: "KP", name_en: "Kampot", name_km: "កំពត", lat: 10.6104, lng: 104.1815, hwy: "NR3" },
        { id: "BTB", name_en: "Battambang", name_km: "បាត់ដំបង", lat: 13.0957, lng: 103.2022, hwy: "NR5" },
        { id: "KPC", name_en: "Kampong Cham", name_km: "កំពង់ចាម", lat: 11.9924, lng: 105.4645, hwy: "NR7" },
        { id: "KCH", name_en: "Kampong Chhnang", name_km: "កំពង់ឆ្នាំង", lat: 12.2500, lng: 104.6667, hwy: "NR5" },
        { id: "KSP", name_en: "Kampong Speu", name_km: "កំពង់ស្ពឺ", lat: 11.4533, lng: 104.5209, hwy: "NR4" },
        { id: "KTH", name_en: "Kampong Thom", name_km: "កំពង់ធំ", lat: 12.7111, lng: 104.8887, hwy: "NR6" },
        { id: "KEP", name_en: "Kep", name_km: "កែប", lat: 10.4828, lng: 104.3167, hwy: "NR33" },
        { id: "KDL", name_en: "Kandal", name_km: "កណ្ដាល", lat: 11.4500, lng: 104.9500, hwy: "NR21 / NR2" },
        { id: "KK", name_en: "Koh Kong", name_km: "កោះកុង", lat: 11.6153, lng: 103.1143, hwy: "NR48" },
        { id: "KTE", name_en: "Kratie", name_km: "ក្រចេះ", lat: 12.4881, lng: 106.0188, hwy: "NR7" },
        { id: "MDK", name_en: "Mondulkiri", name_km: "មណ្ឌលគិរី", lat: 12.4558, lng: 107.1881, hwy: "NR76" },
        { id: "BMC", name_en: "Banteay Meanchey", name_km: "បន្ទាយមានជ័យ", lat: 13.5859, lng: 102.9737, hwy: "NR5 / NR6" },
        { id: "OMC", name_en: "Oddar Meanchey", name_km: "ឧត្តរមានជ័យ", lat: 14.1812, lng: 103.5176, hwy: "NR68" },
        { id: "PLN", name_en: "Pailin", name_km: "ប៉ៃលិន", lat: 12.8489, lng: 102.6093, hwy: "NR57" },
        { id: "PVH", name_en: "Preah Vihear", name_km: "ព្រះវិហារ", lat: 13.8073, lng: 104.9805, hwy: "NR62" },
        { id: "PST", name_en: "Pursat", name_km: "ពោធិ៍សាត់", lat: 12.5388, lng: 103.9192, hwy: "NR5" },
        { id: "PVG", name_en: "Prey Veng", name_km: "ព្រៃវែង", lat: 11.4868, lng: 105.3253, hwy: "NR11" },
        { id: "RTK", name_en: "Ratanakiri", name_km: "រតនគិរី", lat: 13.7394, lng: 106.9872, hwy: "NR78" },
        { id: "STR", name_en: "Stung Treng", name_km: "ស្ទឹងត្រែង", lat: 13.5259, lng: 105.9683, hwy: "NR7" },
        { id: "SVR", name_en: "Svay Rieng", name_km: "ស្វាយរៀង", lat: 11.0879, lng: 105.7994, hwy: "NR1" },
        { id: "TKO", name_en: "Takeo", name_km: "តាកែវ", lat: 10.9908, lng: 104.7848, hwy: "NR2" },
        { id: "TBK", name_en: "Tboung Khmum", name_km: "ត្បូងឃ្មុំ", lat: 11.8891, lng: 105.8760, hwy: "NR7" }
    ],

    // Known Highway Distance Lookup Table (km)
    DISTANCE_MATRIX: {
        "PP-SR": 314, "PP-SHV": 190, "PP-KP": 148, "PP-BTB": 291,
        "PP-KPC": 124, "PP-KPS": 48, "PP-KEP": 164, "PP-KK": 271,
        "PP-PST": 186, "PP-STR": 435, "PP-KTE": 340, "PP-MDK": 520,
        "PP-RTK": 588, "PP-PVH": 405, "PP-BMC": 358, "PP-SVR": 122,
        "PP-TKO": 78, "PP-PVG": 90, "PP-TBK": 155, "PP-KDL": 25,
        "SR-BTB": 152, "SR-BMC": 105, "SR-SHV": 504, "SR-KPC": 250,
        "SR-PVH": 145, "KP-KEP": 25, "KP-SHV": 105, "SHV-KK": 235,
        "BTB-PLN": 82, "STR-RTK": 142, "KTE-STR": 148
    },

    // Calculate Road Distance in KM between any two provinces
    calculateRouteDistance: function(origId, destId) {
        if (origId === destId) return 15; // Intra-city local ride fallback
        const key1 = `${origId}-${destId}`;
        const key2 = `${destId}-${origId}`;
        if (this.DISTANCE_MATRIX[key1]) return this.DISTANCE_MATRIX[key1];
        if (this.DISTANCE_MATRIX[key2]) return this.DISTANCE_MATRIX[key2];

        const p1 = this.PROVINCES.find(p => p.id === origId);
        const p2 = this.PROVINCES.find(p => p.id === destId);
        if (!p1 || !p2) return 180;

        const R = 6371;
        const dLat = (p2.lat - p1.lat) * Math.PI / 180;
        const dLon = (p2.lng - p1.lng) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(p1.lat * Math.PI / 180) * Math.cos(p2.lat * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return Math.max(20, Math.round(R * c * 1.28));
    },

    // Calculate Travel Duration in hours/mins based on highway speeds
    calculateRouteDuration: function(distanceKm) {
        // Average speed: ~65-75 km/h on national roads
        const hours = distanceKm / 68;
        const h = Math.floor(hours);
        const m = Math.round((hours - h) * 60);
        if (h === 0) return `${m} mins`;
        return `${h} hrs ${m} mins`;
    },

    // Vehicle Tiers & Realistic Cambodian Pricing Formulas
    VEHICLES: [
        {
            id: "sedan",
            name_en: "Standard Sedan",
            name_km: "រថយន្តសេដាន (4 កៅអី)",
            capacity: "4 Passengers",
            charter_base_usd: 10.0,
            charter_per_km_usd: 0.20,
            seat_base_usd: 2.50,
            seat_per_km_usd: 0.035,
            icon: "fa-car",
            badge_en: "Most Popular",
            badge_km: "ពេញនិយមបំផុត"
        },
        {
            id: "suv",
            name_en: "Comfort SUV",
            name_km: "រថយន្ត SUV (6 កៅអី)",
            capacity: "6 Passengers",
            charter_base_usd: 15.0,
            charter_per_km_usd: 0.28,
            seat_base_usd: 3.50,
            seat_per_km_usd: 0.045,
            icon: "fa-car-side",
            badge_en: "Extra Space",
            badge_km: "ធំទូលាយ"
        },
        {
            id: "van",
            name_en: "VIP Executive Van",
            name_km: "វ៉ែន VIP (12 កៅអី)",
            capacity: "12 Passengers",
            charter_base_usd: 25.0,
            charter_per_km_usd: 0.40,
            seat_base_usd: 4.50,
            seat_per_km_usd: 0.055,
            icon: "fa-van-shuttle",
            badge_en: "Group Travel",
            badge_km: "សម្រាប់ក្រុម"
        },
        {
            id: "taxi",
            name_en: "City Taxi & Express",
            name_km: "តាក់ស៊ីក្រុង & ប្រញាប់",
            capacity: "4 Passengers",
            charter_base_usd: 4.0,
            charter_per_km_usd: 0.18,
            seat_base_usd: 1.50,
            seat_per_km_usd: 0.030,
            icon: "fa-taxi",
            badge_en: "Fast Service",
            badge_km: "សេវាកម្មរហ័ស"
        }
    ],


    // Real-Time System Telemetry Metrics
    STATS: [
        { count: "25", label_en: "Provinces Covered", label_km: "ខេត្តក្រុងទូទាំងប្រទេស", icon: "fa-map-location-dot" },
        { count: "1,250+", label_en: "Verified Drivers", label_km: "អ្នកបើកបរឆ្លងកាត់ការផ្ទៀងផ្ទាត់", icon: "fa-id-card" },
        { count: "48,000+", label_en: "Completed Trips", label_km: "ដំណើរដែលបានបញ្ចប់", icon: "fa-route" },
        { count: "99.9%", label_en: "System Reliability", label_km: "ភាពជឿជាក់នៃប្រព័ន្ធ", icon: "fa-shield-halved" }
    ],

    // Frequently Asked Questions
    FAQS: [
        {
            q_en: "How do I book an inter-city ride or city taxi with MyTravel?",
            q_km: "តើខ្ញុំអាចកក់ដំណើរអន្តរខេត្ត ឬតាក់ស៊ីក្រុងជាមួយ MyTravel ដោយរបៀបណា?",
            a_en: "Download the MyTravel Passenger App on iOS or Android. Select your pickup and destination provinces, choose your preferred seats or private vehicle tier, and confirm your booking with instant driver assignment.",
            a_km: "ទាញយកកម្មវិធី MyTravel Passenger លើ iOS ឬ Android។ ជ្រើសរើសខេត្តដើម និងខេត្តគោលដៅ ជ្រើសរើសកៅអី ឬប្រភេទរថយន្ត ហើយបន្តការកក់ដោយមានការទទួលភ្លាមៗពីអ្នកបើកបរ។"
        },
        {
            q_en: "How does MyTravel handle payment and currency?",
            q_km: "តើ MyTravel ទូទាត់ប្រាក់ និងប្រាក់រៀល/ដុល្លារយ៉ាងដូចម្តេច?",
            a_en: "MyTravel supports dual-currency cash payments in USD ($) and Khmer Riel (៛), as well as direct digital payments via KHQR scanning with local Cambodian banks.",
            a_km: "MyTravel គាំទ្រការទូទាត់សាច់ប្រាក់ជាពីររូបិយវត្ថុ (ដុល្លារអាមេរិក $ និងរៀល ៛) ព្រមទាំងការទូទាត់ឌីជីថលតាមរយៈ KHQR ជាមួយធនាគារក្នុងស្រុក។"
        },
        {
            q_en: "What safety features are integrated into the MyTravel platform?",
            q_km: "តើ MyTravel មានមុខងារសុវត្ថិភាពអ្វីខ្លះ?",
            a_en: "Every trip is tracked in real-time on GPS with proximity-based arrival verification. In an emergency, passengers and drivers can trigger one-tap direct dispatch to Cambodian emergency hotlines (117 Police, 118 Fire, 119 Ambulance).",
            a_km: "គ្រប់ដំណើរទាំងអស់ត្រូវបានតាមដានតាម GPS រយៈពេលជាក់ស្តែង ជាមួយប្រព័ន្ធផ្ទៀងផ្ទាត់ចម្ងាយ។ ករណីបន្ទាន់ អាចចុចហៅទូរស័ព្ទបន្ទាន់ក្នុងស្រុក (១១៧ នគរបាល, ១១៨ អគ្គិភ័យ, ១១៩ សង្គ្រោះបន្ទាន់) ភ្លាមៗ។"
        },
        {
            q_en: "How can drivers join the MyTravel network?",
            q_km: "តើអ្នកបើកបរអាចចូលរួមជាមួយ MyTravel យ៉ាងដូចម្តេច?",
            a_en: "Drivers can download the MyTravel App, register their phone number, complete trusted-device verification, upload vehicle details, and choose flexible membership tiers (Pro, VIP, Standard) with low daily commission rates.",
            a_km: "អ្នកបើកបរអាចទាញយកកម្មវិធី MyTravel ចុះឈ្មោះតាមលេខទូរស័ព្ទ ផ្ទៀងផ្ទាត់ឧបករណ៍ ដាក់ឯកសារយានយន្ត និងជ្រើសរើសកញ្ចប់សមាជិកភាព (Pro, VIP, Standard) ដោយកាត់សេវាទាបបំផុត។"
        }
    ],

    // Localization Translations (English / Khmer)
    I18N: {
        en: {
            brand_name: "MYTRAVEL.TAXI",
            tagline: "Cambodia's Modern Inter-City Ride & Taxi Network",
            nav_about: "About",
            nav_features: "Features",
            nav_estimator: "Fare Estimator",
            nav_safety: "Safety",
            nav_faq: "FAQ",
            nav_account: "How to Register",
            hero_title: "Kinetic Precision Transport across 25 Cambodian Provinces",
            hero_subtitle: "Experience seamless inter-city rides, real-time live location tracking, seat selection, and bilingual support. Travel with confidence everywhere in Cambodia.",
            btn_passenger_app: "Get Passenger App",
            btn_how_to_start: "How to Create Account",
            badge_phnom_penh: "Phnom Penh Time (GMT+7)",
            how_start_title: "How to Get Started & Create an Account",
            how_start_subtitle: "Fast, simple 4-step onboarding for Passengers and Driver Partners matching mobile app flow.",
            tab_passenger: "Passenger Account",
            tab_driver: "Driver Partner",
            step1_p_title: "1. Phone Number Signup",
            step1_p_desc: "Sign up using your Cambodian phone number (e.g., 012 345 678) and a secure password.",
            step2_p_title: "2. Trusted Device Security",
            step2_p_desc: "Automated hardware device token registers your phone for fast, safe, silent auto-login.",
            step3_p_title: "3. Saved Places & Preferences",
            step3_p_desc: "Configure your Home and Work provinces for instant 1-tap route searches.",
            step4_p_title: "4. Book Seats & Payment",
            step4_p_desc: "Pick specific seats, select Cash (USD/KHR) or KHQR digital payment, and track your driver live.",
            step1_d_title: "1. Driver Phone Registration",
            step1_d_desc: "Register your mobile phone number and password in the Driver mode onboarding flow.",
            step2_d_title: "2. Vehicle & Plate Registration",
            step2_d_desc: "Enter vehicle details (Model, Plate Number e.g. 2AB-1234, Seat Type, and Color).",
            step3_d_title: "3. Choose Membership Tier",
            step3_d_desc: "Select Standard, Pro, or VIP membership tiers with low daily commission rates.",
            step4_d_title: "4. Publish Trips & Earn",
            step4_d_desc: "Create inter-city routes, accept passenger bookings, track live GPS progress, and manage earnings.",
            estimator_title: "Instant Fare & Route Estimator",
            estimator_subtitle: "Calculate estimated trip costs across all 25 provinces in Cambodia.",
            label_origin: "Pickup Province",
            label_destination: "Destination Province",
            label_vehicle: "Vehicle Class",
            mode_shared: "Shared Seat (Per Seat)",
            mode_charter: "Full Private Charter",
            btn_swap_route: "Swap Route",
            label_est_route: "Route & Highway",
            label_est_duration: "Est. Travel Time",
            label_est_seat_price: "Seat Price (Per Seat)",
            label_est_charter_price: "Full Vehicle Charter",
            btn_book_route: "Book This Route Now",
            est_distance: "Estimated Distance",
            est_usd: "Estimated Cost (USD)",
            est_khr: "Estimated Cost (KHR)",
            features_p_title: "Passenger App Highlights",
            features_p_desc: "Empowering travelers with smart route search, seat selection, and real-time tracking.",
            feat_1_title: "Real-Time GPS Tracking",
            feat_1_desc: "Watch your driver's live location and receive arrival & boarding status alerts.",
            feat_2_title: "Seat & Vehicle Choice",
            feat_2_desc: "Choose individual seats for shared inter-city trips or reserve a full private vehicle.",
            feat_3_title: "Bilingual Experience",
            feat_3_desc: "Seamless switching between Khmer (ភាសាខ្មែរ) and English across all flows.",
            features_d_title: "Driver & Operations Platform",
            features_d_desc: "High earnings, flexible membership tiers, and total control over cash debt limits.",
            feat_d1_title: "Fair Commission & Debt Limit",
            feat_d1_desc: "Transparent wallet settlement, automated cash debt tracking, and flexible membership options.",
            feat_d2_title: "Live Operations Control",
            feat_d2_desc: "Real-time trip progress, route status tracking, and proximity arrival alerts.",
            feat_d3_title: "Trusted Device Security",
            feat_d3_desc: "Hardware-backed device token identity prevents unauthorized session hijacking.",
            safety_title: "Safety First Architecture",
            safety_desc: "Proximity arrival enforcement & direct national emergency hotlines.",
            safety_card1_title: "National Emergency Integration",
            safety_card1_desc: "Direct single-tap calling to Police (117), Fire (118), and Ambulance (119).",
            safety_card2_title: "Proximity Verification",
            safety_card2_desc: "Driver arrival and passenger boarding confirmed by system GPS radius truth, not guesswork.",
            faq_title: "Frequently Asked Questions",
            faq_subtitle: "Everything you need to know about riding and driving with MyTravel.",
            footer_copyright: "© 2026 MyTravel Transport Systems. All rights reserved. Kingdom of Cambodia."
        },
        km: {
            brand_name: "MYTRAVEL.TAXI",
            tagline: "បណ្តាញតាក់ស៊ី និងធ្វើដំណើរអន្តរខេត្តទំនើបចុងក្រោយនៅកម្ពុជា",
            nav_about: "អំពីយើង",
            nav_features: "មុខងារពិសេស",
            nav_estimator: "គណនាតម្លៃ",
            nav_safety: "សុវត្ថិភាព",
            nav_faq: "សំណួរញឹកញាប់",
            nav_account: "របៀបចុះឈ្មោះ",
            hero_title: "សេវាធ្វើដំណើរប្រកបដោយទំនុកចិត្ត និងសុវត្ថិភាពទូទាំង ២៥ ខេត្តក្រុង",
            hero_subtitle: "បទពិសោធន៍ធ្វើដំណើរអន្តរខេត្តដ៏រលូន តាមដានទីតាំងផ្ទាល់ ជ្រើសរើសកៅអី និងគាំទ្រពីរភាសា (ខ្មែរ/អង់គ្លេស)។ ធ្វើដំណើរដោយទំនុកចិត្តគ្រប់ទីកន្លែងក្នុងប្រទេសកម្ពុជា។",
            btn_passenger_app: "ទាញយក កម្មវិធីអ្នកជិះ",
            btn_how_to_start: "របៀបបង្កើតគណនី",
            badge_phnom_penh: "ម៉ោងនៅភ្នំពេញ (GMT+7)",
            how_start_title: "របៀបបង្កើតគណនី និងចាប់ផ្តើមប្រើប្រាស់",
            how_start_subtitle: "ជំហានងាយៗ ៤ យ៉ាង សម្រាប់អ្នកជិះ និងអ្នកបើកបរដៃគូ ដូចក្នុងកម្មវិធីទូរស័ព្ទ។",
            tab_passenger: "គណនីអ្នកជិះ (Passenger)",
            tab_driver: "គណនីអ្នកបើកបរ (Driver Partner)",
            step1_p_title: "១. ចុះឈ្មោះតាមលេខទូរស័ព្ទ",
            step1_p_desc: "ចុះឈ្មោះដោយប្រើលេខទូរស័ព្ទក្នុងស្រុក (ឧ. 012 345 678) និងលេខសម្ងាត់សុវត្ថិភាព។",
            step2_p_title: "២. សុវត្ថិភាពឧបករណ៍ជឿជាក់",
            step2_p_desc: "ប្រព័ន្ធចុះឈ្មោះឧបករណ៍កម្រិត hardware ស្វ័យប្រវត្តិ ចូលប្រើប្រាស់រហ័ស និងសុវត្ថិភាព។",
            step3_p_title: "៣. កំណត់ទីតាំងផ្ទះ និងកន្លែងធ្វើការ",
            step3_p_desc: "កំណត់ខេត្ត/ទីតាំងផ្ទះ និងកន្លែងធ្វើការ សម្រាប់ការស្វែងរកជើងដំណើរលឿន ១-ចុច។",
            step4_p_title: "៤. ជ្រើសកៅអី និងទូទាត់ប្រាក់",
            step4_p_desc: "ជ្រើសកៅអីផ្ទាល់ខ្លួន ទូទាត់សាច់ប្រាក់ ($/៛) ឬ KHQR និងតាមដានទីតាំងអ្នកបើកបរផ្ទាល់។",
            step1_d_title: "១. ចុះឈ្មោះអ្នកបើកបរ",
            step1_d_desc: "ចុះឈ្មោះតាមលេខទូរស័ព្ទ និងលេខសម្ងាត់ ក្នុងមុខងារអ្នកបើកបរ។",
            step2_d_title: "២. បញ្ចូលព័ត៌មានរថយន្ត & ស្លាកលេខ",
            step2_d_desc: "បញ្ចូលព័ត៌មានរថយន្ត (ម៉ូឌែល, ស្លាកលេខ ឧ. 2AB-1234, ប្រភេទកៅអី, និងពណ៌)។",
            step3_d_title: "៣. ជ្រើសរើសកញ្ចប់សមាជិកភាព",
            step3_d_desc: "ជ្រើសរើសកញ្ចប់ Standard, Pro, ឬ VIP ជាមួយអត្រាកាត់សេវាទាបសមរម្យ។",
            step4_d_title: "៤. បង្កើតជើងដំណើរ & រកចំណូល",
            step4_d_desc: "បង្កើតតារាងធ្វើដំណើរអន្តរខេត្ត ទទួលការកក់ តាមដាន GPS ផ្ទាល់ និងគ្រប់គ្រងចំណូល។",
            estimator_title: "គណនាតម្លៃសំបុត្រ & ជើងធ្វើដំណើរអន្តរខេត្ត",
            estimator_subtitle: "គណនាតម្លៃសំបុត្រតាមកៅអី តម្លៃកក់មួយឡាន និងចម្ងាយផ្លូវទូទាំង ២៥ ខេត្តក្រុងក្នុងប្រទេសកម្ពុជា។",
            label_origin: "ខេត្តដើម (Pickup Province)",
            label_destination: "ខេត្តគោលដៅ (Destination)",
            label_vehicle: "ប្រភេទយានយន្ត",
            mode_shared: "សំបុត្រតាមកៅអី (Shared Seat)",
            mode_charter: "កក់មួយឡានពេញ (Full Charter)",
            btn_swap_route: "ផ្លាស់ប្តូរទិសដៅ",
            label_est_route: "ផ្លូវជាតិ / ផ្លូវល្បឿនលឿន",
            label_est_duration: "រយៈពេលធ្វើដំណើរប្រហែល",
            label_est_seat_price: "តម្លៃសំបុត្រ (ក្នុង ១កៅអី)",
            label_est_charter_price: "តម្លៃកក់មួយឡានពេញ",
            btn_book_route: "កក់ជើងធ្វើដំណើរនេះ",
            est_distance: "ចម្ងាយផ្លូវប្រហែល",
            est_usd: "តម្លៃប៉ាន់ស្មាន ($ ដុល្លារ)",
            est_khr: "តម្លៃប៉ាន់ស្មាន (៛ រៀល)",

            features_p_title: "មុខងារសំខាន់ៗ កម្មវិធីអ្នកជិះ",
            features_p_desc: "ផ្តល់ភាពងាយស្រួលដល់អ្នកធ្វើដំណើរ ជាមួយការស្វែងរកផ្លូវ ជ្រើសរើសកៅអី និងតាមដានទីតាំងផ្ទាល់។",
            feat_1_title: "តាមដានទីតាំង GPS ផ្ទាល់",
            feat_1_desc: "មើលទីតាំងអ្នកបើកបរភ្លាមៗ និងទទួលការជូនដំណឹងពេលមកដល់។",
            feat_2_title: "ជ្រើសរើសកៅអី និងយានយន្ត",
            feat_2_desc: "ជ្រើសរើសកៅអីផ្ទាល់ខ្លួនសម្រាប់ជើងដំណើររួមគ្នា ឬកក់រថយន្តផ្ទាល់ខ្លួន។",
            feat_3_title: "គាំទ្រ ពីរភាសាពេញលេញ",
            feat_3_desc: "ផ្លាស់ប្តូររវាង ភាសាខ្មែរ និង អង់គ្លេស បានយ៉ាងងាយស្រួលគ្រប់ទំព័រ។",
            features_d_title: "ប្រព័ន្ធអ្នកបើកបរ និងគ្រប់គ្រង",
            features_d_desc: "ចំណូលខ្ពស់ កញ្ចប់សមាជិកភាពបត់បែន និងការគ្រប់គ្រងបំណុលសាច់ប្រាក់ច្បាស់លាស់។",
            feat_d1_title: "កាត់សេវាសមរម្យ & បំណុលសាច់ប្រាក់",
            feat_d1_desc: "ការកាត់សេវាតម្លាភាព តាមដានបំណុលសាច់ប្រាក់ស្វ័យប្រវត្តិ និងជម្រើសកញ្ចប់សមាជិកភាព។",
            feat_d2_title: "ការគ្រប់គ្រងជើងដំណើរផ្ទាល់",
            feat_d2_desc: "តាមដានស្ថានភាពជើងដំណើរ ផ្លូវធ្វើដំណើរ និងការជូនដំណឹងចម្ងាយមកដល់ផ្ទាល់។",
            feat_d3_title: "សុវត្ថិភាព ឧបករណ៍ជឿជាក់",
            feat_d3_desc: "ការផ្ទៀងផ្ទាត់ឧបករណ៍កម្រិត hardware ការពារការលួចប្រើប្រាស់គណនី។",
            safety_title: "ប្រព័ន្ធសុវត្ថិភាពជាចម្បង",
            safety_desc: "ការផ្ទៀងផ្ទាត់ចម្ងាយមកដល់ & ការភ្ជាប់ទូរស័ព្ទបន្ទាន់ជាតិ។",
            safety_card1_title: "ភ្ជាប់ប្រព័ន្ធសង្គ្រោះបន្ទាន់ជាតិ",
            safety_card1_desc: "ចុចទូរស័ព្ទផ្ទាល់ទៅកាន់ នគរបាល (១១៧), អគ្គិភ័យ (១១៨), និងសង្គ្រោះបន្ទាន់ (១១៩)។",
            safety_card2_title: "ការផ្ទៀងផ្ទាត់ចម្ងាយ GPS",
            safety_card2_desc: "ការបញ្ជាក់ការមកដល់របស់អ្នកបើកបរ និងការឡើងរថយន្តផ្អែកលើចម្ងាយ GPS ពិតប្រាកដ។",
            faq_title: "សំណួរដែលសួរញឹកញាប់",
            faq_subtitle: "ព័ត៌មានចាំបាច់ទាំងអស់អំពីការធ្វើដំណើរ និងការបើកបរជាមួយ MyTravel។",
            footer_copyright: "© ២០២៦ ប្រព័ន្ធដឹកជញ្ជូន MyTravel។ រក្សាសិទ្ធិគ្រប់យ៉ាង។ ព្រះរាជាណាចក្រកម្ពុជា។"
        }
    }
};
