/**
 * MyTravel Public Website Data Model (MVC - Model)
 * Contains Cambodian geographical routes, fare matrix, vehicle specs,
 * system statistics, FAQs, and bilingual localization strings.
 */

window.MyTravelData = {
    // Current Exchange Rate: 1 USD = 4,000 KHR
    KHR_RATE: 4000,

    // Major Cambodian Destination Hubs & Distance Matrix (in km)
    PROVINCES: [
        { id: "PP", name_en: "Phnom Penh", name_km: "ភ្នំពេញ" },
        { id: "SR", name_en: "Siem Reap", name_km: "សៀមរាប" },
        { id: "SHV", name_en: "Preah Sihanouk (Sihanoukville)", name_km: "ព្រះសីហនុ" },
        { id: "KP", name_en: "Kampot", name_km: "កំពត" },
        { id: "BTB", name_en: "Battambang", name_km: "បាត់ដំបង" },
        { id: "KPC", name_en: "Kampong Cham", name_km: "កំពង់ចាម" },
        { id: "KPS", name_en: "Kampong Speu", name_km: "កំពង់ស្ពឺ" },
        { id: "KPT", name_en: "Kep", name_km: "កែប" },
        { id: "KK", name_en: "Koh Kong", name_km: "កោះកុង" },
        { id: "PST", name_en: "Pursat", name_km: "ពោធិ៍សាត់" },
        { id: "STR", name_en: "Stung Treng", name_km: "ស្ទឹងត្រែង" },
        { id: "KTE", name_en: "Kratie", name_km: "ក្រចេះ" }
    ],

    // Approximate Distance Matrix between major hubs (km)
    DISTANCE_MATRIX: {
        "PP-SR": 314, "PP-SHV": 230, "PP-KP": 148, "PP-BTB": 291,
        "PP-KPC": 124, "PP-KPS": 48, "PP-KPT": 164, "PP-KK": 271,
        "PP-PST": 186, "PP-STR": 435, "PP-KTE": 340,
        "SR-BTB": 172, "SR-SHV": 530, "SR-KPC": 250, "SR-PST": 240,
        "KP-KPT": 25, "KP-SHV": 105, "SHV-KK": 235
    },

    // Vehicle Tiers & Pricing Formulas
    VEHICLES: [
        {
            id: "sedan",
            name_en: "Standard Sedan",
            name_km: "រថយន្តសេដាន (4 កៅអី)",
            capacity: "4 Passengers",
            base_usd: 2.0,
            per_km_usd: 0.45,
            icon: "fa-car",
            badge_en: "Most Popular",
            badge_km: "ពេញនិយមបំផុត"
        },
        {
            id: "suv",
            name_en: "Comfort SUV",
            name_km: "រថយន្ត SUV (6 កៅអី)",
            capacity: "6 Passengers",
            base_usd: 3.5,
            per_km_usd: 0.65,
            icon: "fa-car-side",
            badge_en: "Extra Space",
            badge_km: "ធំទូលាយ"
        },
        {
            id: "van",
            name_en: "VIP Executive Van",
            name_km: "វ៉ែន VIP (12 កៅអី)",
            capacity: "12 Passengers",
            base_usd: 6.0,
            per_km_usd: 0.95,
            icon: "fa-van-shuttle",
            badge_en: "Group Travel",
            badge_km: "សម្រាប់ក្រុម"
        },
        {
            id: "taxi",
            name_en: "City Taxi & Express",
            name_km: "តាក់ស៊ីក្រុង & ប្រញាប់",
            capacity: "4 Passengers",
            base_usd: 1.5,
            per_km_usd: 0.40,
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
            estimator_subtitle: "Calculate estimated trip costs across major province routes in Cambodia.",
            label_origin: "Pickup Province",
            label_destination: "Destination Province",
            label_vehicle: "Vehicle Class",
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
            estimator_title: "ប្រព័ន្ធគណនាចម្ងាយ និងតម្លៃសេវាភ្លាមៗ",
            estimator_subtitle: "គណនាតម្លៃប៉ាន់ស្មានតាមផ្លូវខេត្តសំខាន់ៗក្នុងប្រទេសកម្ពុជា។",
            label_origin: "ខេត្តដើម (ទទួល)",
            label_destination: "ខេត្តគោលដៅ",
            label_vehicle: "ប្រភេទយានយន្ត",
            est_distance: "ចម្ងាយប៉ាន់ស្មាន",
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
