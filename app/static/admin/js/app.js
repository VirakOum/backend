// My Travel Command Dashboard JavaScript
document.addEventListener('DOMContentLoaded', () => {
    // API Base URLs (relative to this page)
    const API_BASE = '/v1/api/travel/admin';
    const API_V1_BASE = '/v1/api';

    // HTML Escape Helper
    function escapeHtml(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Cambodia 25 Provinces list for searchable select components
    const CAMBODIA_PROVINCES = [
        { kh: "ភ្នំពេញ", en: "Phnom Penh" },
        { kh: "បន្ទាយមានជ័យ", en: "Banteay Meanchey" },
        { kh: "បាត់ដំបង", en: "Battambang" },
        { kh: "កំពង់ចាម", en: "Kampong Cham" },
        { kh: "កំពង់ឆ្នាំង", en: "Kampong Chhnang" },
        { kh: "កំពង់ស្ពឺ", en: "Kampong Speu" },
        { kh: "កំពង់ធំ", en: "Kampong Thom" },
        { kh: "កំពត", en: "Kampot" },
        { kh: "កណ្ដាល", en: "Kandal" },
        { kh: "កោះកុង", en: "Koh Kong" },
        { kh: "ក្រចេះ", en: "Kratie" },
        { kh: "មណ្ឌលគិរី", en: "Mondulkiri" },
        { kh: "ឧត្តរមានជ័យ", en: "Oddar Meanchey" },
        { kh: "ប៉ៃលិន", en: "Pailin" },
        { kh: "ព្រះសីហនុ", en: "Preah Sihanouk" },
        { kh: "ព្រះវិហារ", en: "Preah Vihear" },
        { kh: "ពោធិ៍សាត់", en: "Pursat" },
        { kh: "ព្រៃវែង", en: "Prey Veng" },
        { kh: "រតនគិរី", en: "Ratanakiri" },
        { kh: "សៀមរាប", en: "Siem Reap" },
        { kh: "ស្ទឹងត្រែង", en: "Stung Treng" },
        { kh: "ស្វាយរៀង", en: "Svay Rieng" },
        { kh: "តាកែវ", en: "Takeo" },
        { kh: "ត្បូងឃ្មុំ", en: "Tboung Khmum" },
        { kh: "កែប", en: "Kep" }
    ];

    // Translations Dictionary
    const TRANSLATIONS = {
        en: {
            doc_title: "My Travel - Command Dashboard",
            brand_title: "MY TRAVEL",
            brand_subtitle: "Kinetic Precision Framework",
            nav_overview: "System Overview",
            nav_map: "Live Tracking Map",
            nav_trips: "Trip Operations",
            nav_drivers: "Driver Management",
            nav_passengers: "Passenger Management",
            nav_revenue: "Revenue Analytics",
            system_online: "SYSTEM ONLINE (PP)",
            title_overview: "System Overview",
            subtitle_overview: "Real-time status updates and operations control",
            title_map: "Live Tracking Map",
            subtitle_map: "Real-time location of active and scheduled drivers",
            title_trips: "Trip Operations",
            subtitle_trips: "Track scheduled and active trips day-by-day with passenger booking counts",
            title_drivers: "Driver Management",
            subtitle_drivers: "Inspect, verify, lock, and change tiers for driver partners",
            title_passengers: "Passenger Management",
            subtitle_passengers: "Monitor and verify passenger accounts",
            title_revenue: "Revenue Analytics",
            subtitle_revenue: "Track and analyze My Travel daily and monthly system earnings",
            nav_promotions: "Promotions & Ads",
            title_promotions: "Promotions & Ads Management",
            subtitle_promotions: "Manage system discount coupons and homepage banner ads",
            nav_discounts: "Discount Coupons",
            title_discounts: "Discount Coupons & Tickets",
            subtitle_discounts: "Create, edit, and manage discount tickets and promo codes",
            nav_ads: "Homepage Banner Ads",
            title_ads: "Homepage Banner Ads",
            subtitle_ads: "Manage featured banner advertisements on passenger mobile homepage",
            nav_messages: "System Messages",
            title_messages: "System Messages & Announcements",
            subtitle_messages: "Broadcast informational messages and alerts to app users",
            nav_vehicle_models: "Vehicle Models",
            title_vehicle_models: "Car & Vehicle Models",
            subtitle_vehicle_models: "Manage available vehicle makes, models, and default seating configurations",
            btn_add_vehicle_model: "Add Car Model",
            table_brand: "Make / Brand",
            table_model_name: "Model Name",
            table_display_name: "Display Name",
            table_vehicle_type: "Body / Type",
            table_seat_count: "Default Seats",
            btn_refresh: "Refresh Data",
            kpi_active_vehicles: "Active Vehicles",
            kpi_registered_drivers: "Registered Drivers",
            kpi_total_passengers: "Total Passengers",
            kpi_verified_customers: "Verified Customers",
            kpi_active_trips: "Active Trips",
            kpi_trip_sub: "En Route / Scheduled",
            kpi_debt_owed: "Total Debt Owed",
            config_title: "System Configuration",
            config_enable_digital: "Enable Digital ABA Payments",
            config_enable_digital_desc: "Allow passengers to upload ABA transaction screenshots",
            config_auto_lock: "Auto-Lock Owed Drivers",
            config_auto_lock_desc: "Automatically lock driver when debt limit is breached",
            config_limit_usd: "Cash Debt Limit (USD)",
            config_limit_khr: "Cash Debt Limit (KHR)",
            config_save: "Save Configuration",
            preset_title: "Operational Presets",
            preset_desc: "Utilize database shortcuts to test specific dashboard states.",
            preset_btn: "Seed Demo Data",
            map_overview_label: "My Travel Map",
            map_active_trip: "Active Trip",
            map_scheduled_trip: "Scheduled Trip",
            map_locked_driver: "Locked Driver",
            search_drivers_placeholder: "Search drivers by name or phone...",
            search_passengers_placeholder: "Search passengers by name or phone...",
            table_name: "Name",
            table_phone: "Phone Number",
            table_verification: "Verification Status",
            table_rating: "Rating",
            table_bookings: "Completed Bookings",
            table_joined: "Joined Date",
            table_actions: "Actions",
            settle_title: "Settle Driver Fee Debt",
            settle_desc: "This action marks all outstanding \"owed\" trip fee entries for this driver as \"settled\" and resets the driver's accumulated cash debt to zero.",
            settle_driver_name_lbl: "Driver Name",
            settle_driver_debt_lbl: "Current Outstanding Debt",
            settle_notes_lbl: "Settlement Reference / Notes",
            settle_notes_placeholder: "e.g. Paid cash at office, ABA txn #123456",
            settle_cancel: "Cancel",
            settle_submit: "Record Settlement",
            toast_refresh: "My Travel dashboard data refreshed.",
            toast_settings_saved: "Settings saved and lock limits updated successfully.",
            toast_settings_error: "Error saving settings.",
            toast_network_error: "Network error occurred.",
            toast_verified: "User verification status toggled successfully.",
            toast_lock_updated: "Driver lock status updated.",
            toast_membership_updated: "Driver membership changed successfully.",
            toast_settled: "Driver fee debt settled and account unlocked.",
            
            // Revenue translations
            kpi_monthly_revenue: "Monthly Revenue",
            kpi_daily_revenue: "Daily Revenue",
            chart_toggle_daily: "Daily View",
            chart_toggle_monthly: "Monthly View",
            table_period: "Period / Date",
            table_revenue_usd: "Revenue (USD)",
            table_revenue_khr: "Revenue (KHR)",

            // Trips translations & analytics
            trip_clear_filter: "Clear Filters",
            txt_no_trips: "No trips found matching filter criteria.",
            filter_status_all: "All Statuses",
            filter_status_scheduled: "Scheduled",
            filter_status_active: "Active",
            filter_status_completed: "Completed",
            filter_status_cancelled: "Cancelled",
            filter_dep_placeholder: "Departure...",
            filter_dest_placeholder: "Destination...",
            kpi_total_trips: "Total Trips",
            kpi_total_bookings: "Total Bookings",
            kpi_occupancy_rate: "Seat Occupancy",
            chart_trips_status: "Trips by Status",

            // Trip Detail Modal translations
            trip_detail_title: "Manage Trip Operations",
            edit_trip_status_lbl: "Trip Status",
            edit_trip_price_lbl: "Price Per Seat (KHR)",
            edit_trip_total_seats_lbl: "Total Seating Capacity",
            edit_trip_avail_seats_lbl: "Available Seats",
            trip_save_btn: "Save Changes",
            trip_delete_btn: "Delete Trip",
            toast_trip_saved: "Trip details updated successfully.",
            toast_trip_deleted: "Trip deleted successfully.",
            txt_confirm_delete_trip: "Are you sure you want to delete this trip? This will delete all passenger bookings associated with it.",

            // Dynamic texts
            status_verified: "Verified",
            status_unverified: "Unverified",
            status_open: "Open",
            status_locked: "Locked",
            btn_unverify: "Unverify",
            btn_verify: "Verify",
            btn_lock: "Lock",
            btn_unlock: "Unlock",
            btn_settle: "Settle",
            option_normal: "Normal User",
            option_pro: "Membership Pro",
            option_vip: "VIP Member",
            txt_driver: "Driver",
            txt_vehicle: "Vehicle",
            txt_seats: "Seats",
            txt_status: "Status",
            txt_speed: "Speed",
            txt_heading: "Heading",
            txt_no_drivers: "No drivers found matching search criteria.",
            txt_no_passengers: "No passengers found matching search criteria.",
            txt_seeding: "Seeding database, please wait...",
            txt_seeding_success: "Demo data seeded successfully!",
            txt_seeding_error: "Failed to seed demo data."
        },
        km: {
            doc_title: "ម៉ាយ ត្រាវែល - ផ្ទាំងគ្រប់គ្រង",
            brand_title: "ម៉ាយ ត្រាវែល",
            brand_subtitle: "ក្របខ័ណ្ឌគំរូរចនា Kinetic Precision",
            nav_overview: "ទិដ្ឋភាពទូទៅនៃប្រព័ន្ធ",
            nav_map: "ផែនទីតាមដានផ្ទាល់",
            nav_trips: "ប្រវត្តិធ្វើដំណើរ",
            nav_drivers: "ការគ្រប់គ្រងអ្នកបើកបរ",
            nav_passengers: "ការគ្រប់គ្រងអ្នកដំណើរ",
            nav_revenue: "វិភាគចំណូលសរុប",
            system_online: "ប្រព័ន្ធដំណើរការធម្មតា (ភ្នំពេញ)",
            title_overview: "ទិដ្ឋភាពទូទៅនៃប្រព័ន្ធ",
            subtitle_overview: "ការធ្វើបច្ចុប្បន្នភាពស្ថានភាពពេលវេលាជាក់ស្តែងនិងការគ្រប់គ្រងប្រតិបត្តិការ",
            title_map: "ផែនទីតាមដានផ្ទាល់",
            subtitle_map: "ទីតាំងពេលវេលាជាក់ស្តែងរបស់អ្នកបើកបរដែលកំពុងសកម្មនិងបានគ្រោងទុក",
            title_trips: "ប្រវត្តិធ្វើដំណើរ",
            subtitle_trips: "តាមដានការធ្វើដំណើរប្រចាំថ្ងៃ និងចំនួនកក់សំបុត្ររបស់អ្នកដំណើរ",
            title_drivers: "ការគ្រប់គ្រងអ្នកបើកបរ",
            subtitle_drivers: "ត្រួតពិនិត្យ ផ្ទៀងផ្ទាត់ ចាក់សោ និងផ្លាស់ប្តូរកម្រិតសមាជិកភាពរបស់អ្នកបើកបរ",
            title_passengers: "ការគ្រប់គ្រងអ្នកដំណើរ",
            subtitle_passengers: "ត្រួតពិនិត្យនិងផ្ទៀងផ្ទាត់គណនីអ្នកដំណើរ",
            title_revenue: "វិភាគចំណូលសរុប",
            subtitle_revenue: "តាមដាននិងវិភាគការរកចំណូលប្រចាំថ្ងៃនិងប្រចាំខែរបស់ប្រព័ន្ធ ម៉ាយ ត្រាវែល",
            nav_promotions: "ប្រូម៉ូសិន និងការផ្សព្វផ្សាយ",
            title_promotions: "ការគ្រប់គ្រងប្រូម៉ូសិន និងការផ្សព្វផ្សាយ",
            subtitle_promotions: "គ្រប់គ្រងប័ណ្ណបញ្ចុះតម្លៃប្រព័ន្ធ និងផ្ទាំងផ្សព្វផ្សាយស្លាយនៅទំព័រដើម",
            nav_discounts: "ប័ណ្ណបញ្ចុះតម្លៃ",
            title_discounts: "ការគ្រប់គ្រងប័ណ្ណបញ្ចុះតម្លៃ",
            subtitle_discounts: "បង្កើត កែប្រែ និងគ្រប់គ្រងសំបុត្របញ្ចុះតម្លៃ និងកូដប្រូម៉ូសិន",
            nav_ads: "បដាផ្សាយពាណិជ្ជកម្ម",
            title_ads: "បដាផ្សាយពាណិជ្ជកម្មទំព័រដើម",
            subtitle_ads: "គ្រប់គ្រងរូបភាព និងព័ត៌មានបដាផ្សាយពាណិជ្ជកម្មលើទំព័រដើម",
            nav_messages: "សារប្រព័ន្ធ",
            title_messages: "សារប្រព័ន្ធ និងការប្រកាសដំណឹង",
            subtitle_messages: "ផ្សព្វផ្សាយសារព័ត៌មាន និងការព្រមានដល់អ្នកប្រើប្រាស់កម្មវិធី",
            nav_vehicle_models: "ម៉ូដែលរថយន្ត",
            title_vehicle_models: "ម៉ូដែលរថយន្ត និងយានយន្ត",
            subtitle_vehicle_models: "គ្រប់គ្រងម៉ាក ម៉ូដែល និងចំនួនកៅអីតាមលំនាំដើមរបស់រថយន្ត",
            btn_add_vehicle_model: "បន្ថែមម៉ូដែលរថយន្ត",
            table_brand: "ម៉ាក / ផលិតករ",
            table_model_name: "ឈ្មោះម៉ូដែល",
            table_display_name: "ឈ្មោះបង្ហាញពេញ",
            table_vehicle_type: "ប្រភេទ / ប្រភេទទូក",
            table_seat_count: "ចំនួនកៅអីលំនាំដើម",
            btn_refresh: "ទាញយកទិន្នន័យថ្មី",
            kpi_active_vehicles: "យានយន្តសកម្ម",
            kpi_registered_drivers: "អ្នកបើកបរដែលបានចុះឈ្មោះ",
            kpi_total_passengers: "អ្នកដំណើរសរុប",
            kpi_verified_customers: "អតិថិជនបានផ្ទៀងផ្ទាត់",
            kpi_active_trips: "ការធ្វើដំណើរដែលកំពុងដំណើរការ",
            kpi_trip_sub: "កំពុងធ្វើដំណើរ / បានគ្រោងទុក",
            kpi_debt_owed: "បំណុលត្រូវសងសរុប",
            config_title: "ការកំណត់រចនាសម្ព័ន្ធប្រព័ន្ធ",
            config_enable_digital: "បើកការទូទាត់ ABA ឌីជីថល",
            config_enable_digital_desc: "អនុញ្ញាតឱ្យអ្នកដំណើរផ្ទុកឡើងរូបថតអេក្រង់ប្រតិបត្តិការ ABA",
            config_auto_lock: "ចាក់សោអ្នកបើកបរជំពាក់ស្វ័យប្រវត្តិ",
            config_auto_lock_desc: "ចាក់សោគណនីអ្នកបើកបរដោយស្វ័យប្រវត្តិនៅពេលលើសដែនកំណត់បំណុល",
            config_limit_usd: "ដែនកំណត់បំណុលសាច់ប្រាក់ (USD)",
            config_limit_khr: "ដែនកំណត់បំណុលសាច់ប្រាក់ (KHR)",
            config_save: "រក្សាទុកការកំណត់",
            preset_title: "ទិន្នន័យសាកល្បងប្រព័ន្ធ",
            preset_desc: "ប្រើប្រាស់ផ្លូវកាត់មូលដ្ឋានទិន្នន័យដើម្បីសាកល្បងស្ថានភាពផ្ទាំងគ្រប់គ្រងជាក់លាក់។",
            preset_btn: "បញ្ចូលទិន្នន័យសាកល្បង",
            map_overview_label: "ផែនទី ម៉ាយ ត្រាវែល",
            map_active_trip: "កំពុងធ្វើដំណើរ",
            map_scheduled_trip: "បានគ្រោងទុក",
            map_locked_driver: "អ្នកបើកបរត្រូវបានចាក់សោ",
            search_drivers_placeholder: "ស្វែងរកអ្នកបើកបរតាមឈ្មោះឬលេខទូរស័ព្ទ...",
            search_passengers_placeholder: "ស្វែងរកអ្នកដំណើរតាមឈ្មោះឬលេខទូរស័ព្ទ...",
            table_name: "ឈ្មោះ",
            table_phone: "លេខទូរស័ព្ទ",
            table_verification: "ស្ថានភាពផ្ទៀងផ្ទាត់",
            table_rating: "ការវាយតម្លៃ",
            table_bookings: "ការកក់ដែលបានបញ្ចប់",
            table_joined: "កាលបរិច្ឆេទចូលរួម",
            table_actions: "សកម្មភាព",
            settle_title: "ទូទាត់បំណុលកម្រៃសេវារបស់អ្នកបើកបរ",
            settle_desc: "សកម្មភាពនេះសម្គាល់រាល់ការបញ្ចូលថ្លៃសេវាធ្វើដំណើរ \"ជំពាក់\" សម្រាប់អ្នកបើកបរនេះថា \"បានទូទាត់\" និងកំណត់បំណុលសាច់ប្រាក់បង្គររបស់អ្នកបើកបរទៅសូន្យវិញ។",
            settle_driver_name_lbl: "ឈ្មោះអ្នកបើកបរ",
            settle_driver_debt_lbl: "បំណុលបច្ចុប្បន្នដែលមិនទាន់ទូទាត់",
            settle_notes_lbl: "ឯកសារយោងទូទាត់ / កំណត់ចំណាំ",
            settle_notes_placeholder: "ឧទាហរណ៍៖ បង់ប្រាក់ផ្ទាល់នៅការិយាល័យ, ប្រតិបត្តិការ ABA #123456",
            settle_cancel: "បោះបង់",
            settle_submit: "កត់ត្រាការទូទាត់",
            toast_refresh: "ទិន្នន័យផ្ទាំងគ្រប់គ្រង ម៉ាយ ត្រាវែល ត្រូវបានទាញយកថ្មី។",
            toast_settings_saved: "រក្សាទុកការកំណត់ និងធ្វើបច្ចុប្បន្នភាពដែនកំណត់ចាក់សោដោយជោគជ័យ។",
            toast_settings_error: "មានកំហុសក្នុងការរក្សាទុកការកំណត់។",
            toast_network_error: "មានកំហុសបណ្តាញកើតឡើង។",
            toast_verified: "ស្ថានភាពផ្ទៀងផ្ទាត់របស់អ្នកប្រើប្រាស់ត្រូវបានធ្វើបច្ចុប្បន្នភាព។",
            toast_lock_updated: "ស្ថានភាពចាក់សោរបស់អ្នកបើកបរត្រូវបានធ្វើបច្ចុប្បន្នភាព។",
            toast_membership_updated: "កម្រិតសមាជិកភាពរបស់អ្នកបើកបរត្រូវបានផ្លាស់ប្តូរដោយជោគជ័យ។",
            toast_settled: "បំណុលកម្រៃសេវារបស់អ្នកបើកបរត្រូវបានទូទាត់រួចរាល់ និងបានបើកដំណើរការគណនីឡើងវិញ។",
            
            // Revenue translations
            kpi_monthly_revenue: "ចំណូលប្រចាំខែ",
            kpi_daily_revenue: "ចំណូលប្រចាំថ្ងៃ",
            chart_toggle_daily: "មើលប្រចាំថ្ងៃ",
            chart_toggle_monthly: "មើលប្រចាំខែ",
            table_period: "រយៈពេល / កាលបរិច្ឆេទ",
            table_revenue_usd: "ចំណូល (USD)",
            table_revenue_khr: "ចំណូល (KHR)",

            // Trips translations & analytics
            trip_clear_filter: "សម្អាតតម្រង",
            txt_no_trips: "រកមិនឃើញការធ្វើដំណើរដែលត្រូវគ្នានឹងការស្វែងរកឡើយ។",
            filter_status_all: "ស្ថានភាពទាំងអស់",
            filter_status_scheduled: "បានគ្រោងទុក",
            filter_status_active: "កំពុងដំណើរការ",
            filter_status_completed: "បានបញ្ចប់",
            filter_status_cancelled: "បានបោះបង់",
            filter_dep_placeholder: "ខេត្តចេញដំណើរ...",
            filter_dest_placeholder: "ខេត្តគោលដៅ...",
            kpi_total_trips: "ជើងដំណើរសរុប",
            kpi_total_bookings: "ការកក់សំបុត្រសរុប",
            kpi_occupancy_rate: "អត្រាប្រើប្រាស់កៅអី",
            chart_trips_status: "ជើងដំណើរតាមស្ថានភាព",

            // Trip Detail Modal translations
            trip_detail_title: "គ្រប់គ្រងជើងដំណើរ",
            edit_trip_status_lbl: "ស្ថានភាពជើងដំណើរ",
            edit_trip_price_lbl: "តម្លៃក្នុងមួយកៅអី (៛)",
            edit_trip_total_seats_lbl: "ចំនួនកៅអីសរុប",
            edit_trip_avail_seats_lbl: "ចំនួនកៅអីនៅសល់",
            trip_save_btn: "រក្សាទុកការកែប្រែ",
            trip_delete_btn: "លុបជើងដំណើរនេះ",
            toast_trip_saved: "បានធ្វើបច្ចុប្បន្នភាពព័ត៌មានជើងដំណើរដោយជោគជ័យ។",
            toast_trip_deleted: "បានលុបជើងដំណើរដោយជោគជ័យ។",
            txt_confirm_delete_trip: "តើអ្នកពិតជាចង់លុបជើងដំណើរនេះមែនទេ? ការលុបនេះនឹងលុបរាល់ការកក់របស់អ្នកដំណើរទាំងអស់ដែលពាក់ព័ន្ធ។",

            // Dynamic texts
            status_verified: "បានផ្ទៀងផ្ទាត់",
            status_unverified: "មិនទាន់ផ្ទៀងផ្ទាត់",
            status_open: "ធម្មតា",
            status_locked: "ចាក់សោ",
            btn_unverify: "លុបការផ្ទៀងផ្ទាត់",
            btn_verify: "ផ្ទៀងផ្ទាត់",
            btn_lock: "ចាក់សោ",
            btn_unlock: "បើកសោ",
            btn_settle: "ទូទាត់",
            option_normal: "អ្នកប្រើប្រាស់ធម្មតា",
            option_pro: "សមាជិកប្រូ (Pro)",
            option_vip: "សមាជិកវីអាយភី (VIP)",
            txt_driver: "អ្នកបើកបរ",
            txt_vehicle: "យានយន្ត",
            txt_seats: "កៅអី",
            txt_status: "ស្ថានភាព",
            txt_speed: "ល្បឿន",
            txt_heading: "ទិសដៅ",
            txt_no_drivers: "រកមិនឃើញអ្នកបើកបរដែលត្រូវគ្នានឹងការស្វែងរករបស់អ្នកឡើយ។",
            txt_no_passengers: "រកមិនឃើញអ្នកដំណើរដែលត្រូវគ្នានឹងការស្វែងរករបស់អ្នកឡើយ។",
            txt_seeding: "កំពុងបញ្ចូលទិន្នន័យសាកល្បង ម៉ាយ ត្រាវែល សូមរង់ចាំ...",
            txt_seeding_success: "បានបញ្ចូលទិន្នន័យសាកល្បងដោយជោគជ័យ!",
            txt_seeding_error: "ការបញ្ចូលទិន្នន័យសាកល្បងបានបរាជ័យ។"
        }
    };

    // Geographic Coordinates of Cambodia Provinces for Map Rendering
    const PROVINCE_COORDINATES = {
        "ភ្នំពេញ": [11.5564, 104.9282],
        "Phnom Penh": [11.5564, 104.9282],
        "បន្ទាយមានជ័យ": [13.5857, 102.9737],
        "Banteay Meanchey": [13.5857, 102.9737],
        "បាត់ដំបង": [13.0957, 103.2022],
        "Battambang": [13.0957, 103.2022],
        "កំពង់ចាម": [11.9934, 105.4633],
        "Kampong Cham": [11.9934, 105.4633],
        "កំពង់ឆ្នាំង": [12.2500, 104.6667],
        "Kampong Chhnang": [12.2500, 104.6667],
        "កំពង់ស្ពឺ": [11.4533, 104.5210],
        "Kampong Speu": [11.4533, 104.5210],
        "កំពង់ធំ": [12.7111, 104.8887],
        "Kampong Thom": [12.7111, 104.8887],
        "កំពត": [10.6108, 104.1818],
        "Kampot": [10.6108, 104.1818],
        "កណ្ដាល": [11.4833, 104.9500],
        "Kandal": [11.4833, 104.9500],
        "កោះកុង": [11.6152, 102.9776],
        "Koh Kong": [11.6152, 102.9776],
        "ក្រចេះ": [12.4881, 106.0188],
        "Kratie": [12.4881, 106.0188],
        "មណ្ឌលគិរី": [12.4558, 107.1903],
        "Mondulkiri": [12.4558, 107.1903],
        "ឧត្តរមានជ័យ": [14.1756, 103.5186],
        "Oddar Meanchey": [14.1756, 103.5186],
        "ប៉ៃលិន": [12.8489, 102.6092],
        "Pailin": [12.8489, 102.6092],
        "ព្រះសីហនុ": [10.6253, 103.5298],
        "Sihanoukville": [10.6253, 103.5298],
        "Preah Sihanouk": [10.6253, 103.5298],
        "ព្រះវិហារ": [13.8073, 104.9782],
        "Preah Vihear": [13.8073, 104.9782],
        "ពោធិ៍សាត់": [12.5333, 103.9167],
        "Pursat": [12.5333, 103.9167],
        "ព្រៃវែង": [11.4868, 105.3253],
        "Prey Veng": [11.4868, 105.3253],
        "រតនគិរី": [13.7388, 106.9873],
        "Ratanakiri": [13.7388, 106.9873],
        "សៀមរាប": [13.3633, 103.8564],
        "Siem Reap": [13.3633, 103.8564],
        "ស្ទឹងត្រែង": [13.5259, 105.9683],
        "Stung Treng": [13.5259, 105.9683],
        "ស្វាយរៀង": [11.0878, 105.7994],
        "Svay Rieng": [11.0878, 105.7994],
        "តាកែវ": [10.9900, 104.7849],
        "Takeo": [10.9900, 104.7849],
        "ត្បូងឃ្មុំ": [11.9422, 105.6567],
        "Tboung Khmum": [11.9422, 105.6567],
        "កែប": [10.4829, 104.3167],
        "Kep": [10.4829, 104.3167]
    };

    // App state variables
    let currentLanguage = localStorage.getItem('lang') || 'en';
    let map = null;
    let tripMarkers = [];
    let currentDrivers = [];
    let currentPassengers = [];
    let currentTrips = [];
    let appSettings = null;
    let activeTabId = 'overview';

    // Pagination state
    let driverCurrentPage = 1;
    const driverPageSize = 6;
    let passengerCurrentPage = 1;
    const passengerPageSize = 10;

    // Revenue state
    let revenueData = null;
    let revenueChart = null;
    let activeChartPeriod = 'daily';

    // Trips analytics state
    let tripsStatusChart = null;
    let detailMap = null;
    let detailMarker = null;

    // Elements
    const sidebarNav = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const pageTitle = document.getElementById('page-title');
    const pageSubtitle = document.getElementById('page-subtitle');
    const btnRefreshAll = document.getElementById('btn-refresh-all');
    const btnSeedDemo = document.getElementById('btn-seed-demo');
    const presetStatus = document.getElementById('preset-status');
    const langSelect = document.getElementById('lang-select');
    
    // KPI elements
    const kpiTotalDrivers = document.getElementById('kpi-total-drivers');
    const kpiTotalPassengers = document.getElementById('kpi-total-passengers');
    const kpiActiveTrips = document.getElementById('kpi-active-trips');
    const kpiTotalOwed = document.getElementById('kpi-total-owed');
    const kpiTotalOwedUsd = document.getElementById('kpi-total-owed-usd');
    const driversList = document.getElementById('drivers-list');
    const passengersList = document.getElementById('passengers-list');
    const searchDriversInput = document.getElementById('search-drivers');
    const searchPassengersInput = document.getElementById('search-passengers');
    const settleModal = document.getElementById('settle-modal');
    const settleForm = document.getElementById('settle-form');
    const settleDriverId = document.getElementById('settle-driver-id');
    const settleDriverName = document.getElementById('settle-driver-name');
    const settleDriverDebt = document.getElementById('settle-driver-debt');
    const settleNotesInput = document.getElementById('settle-notes');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const btnCancelSettle = document.getElementById('btn-cancel-settle');

    // Revenue elements
    const kpiRevTotal = document.getElementById('kpi-rev-total');
    const kpiRevTotalUsd = document.getElementById('kpi-rev-total-usd');
    const kpiRevMonth = document.getElementById('kpi-rev-month');
    const kpiRevMonthUsd = document.getElementById('kpi-rev-month-usd');
    const kpiRevToday = document.getElementById('kpi-rev-today');
    const kpiRevTodayUsd = document.getElementById('kpi-rev-today-usd');
    const btnChartDaily = document.getElementById('btn-chart-daily');
    const btnChartMonthly = document.getElementById('btn-chart-monthly');
    const revenueTableBody = document.getElementById('revenue-table-body');

    // Trips tab elements
    const tripDateFilter = document.getElementById('trip-date-filter');
    const tripStatusFilter = document.getElementById('trip-status-filter');
    const tripDepartureFilter = document.getElementById('trip-departure-filter');
    const departureDropdownList = document.getElementById('departure-dropdown-list');
    const tripDestinationFilter = document.getElementById('trip-destination-filter');
    const destinationDropdownList = document.getElementById('destination-dropdown-list');
    const tripVehicleFilter = document.getElementById('trip-vehicle-filter');
    const btnClearDateFilter = document.getElementById('btn-clear-date-filter');
    const tripsByDayList = document.getElementById('trips-by-day-list');

    // Trips KPI elements
    const kpiTripsTotal = document.getElementById('kpi-trips-total');
    const kpiTripsBookings = document.getElementById('kpi-trips-bookings');
    const kpiTripsActive = document.getElementById('kpi-trips-active');
    const kpiTripsOccupancy = document.getElementById('kpi-trips-occupancy');

    // Trip detail modal elements
    const tripDetailModal = document.getElementById('trip-detail-modal');
    const btnCloseTripModal = document.getElementById('btn-close-trip-modal');
    const tripEditForm = document.getElementById('trip-edit-form');
    const editTripId = document.getElementById('edit-trip-id');
    const editTripStatus = document.getElementById('edit-trip-status');
    const editTripPrice = document.getElementById('edit-trip-price');
    const editTripTotalSeats = document.getElementById('edit-trip-total-seats');
    const editTripAvailSeats = document.getElementById('edit-trip-avail-seats');
    const btnDeleteTrip = document.getElementById('btn-delete-trip');
    const detailTripRoute = document.getElementById('detail-trip-route');
    const detailTripTime = document.getElementById('detail-trip-time');
    const detailDriverName = document.getElementById('detail-driver-name');
    const detailVehicle = document.getElementById('detail-vehicle');
    const detailBookings = document.getElementById('detail-bookings');

    // Settings Elements
    const settingsForm = document.getElementById('settings-form');
    const enableDigitalPaymentInput = document.getElementById('enable_digital_payment');
    const autoLockOnLimitInput = document.getElementById('auto_lock_on_limit');
    const driverCashDebtLimitUsdInput = document.getElementById('driver_cash_debt_limit_usd');
    const driverCashDebtLimitKhrInput = document.getElementById('driver_cash_debt_limit_khr');

    // Promotions and Ads Elements
    const btnAddDiscount = document.getElementById('btn-add-discount');
    const btnCloseDiscountModal = document.getElementById('btn-close-discount-modal');
    const discountModal = document.getElementById('discount-modal');
    const formModalDiscount = document.getElementById('form-modal-discount');
    const btnAddAd = document.getElementById('btn-add-ad');
    const btnCloseAdModal = document.getElementById('btn-close-ad-modal');
    const adModal = document.getElementById('ad-modal');
    const formModalAd = document.getElementById('form-modal-ad');
    const discountsTableBody = document.getElementById('discounts-table-body');
    const adsTableBody = document.getElementById('ads-table-body');
    const modalAdImageFile = document.getElementById('modal-ad-image-file');
    const modalAdImageUrl = document.getElementById('modal-ad-image-url');
    const modalAdImagePreview = document.getElementById('modal-ad-image-preview');

    // Setup Custom Searchable Dropdowns for Provinces
    setupSearchableDropdown(tripDepartureFilter, departureDropdownList);
    setupSearchableDropdown(tripDestinationFilter, destinationDropdownList);

    function setupSearchableDropdown(inputEl, listEl) {
        const renderOptions = (filterText = '') => {
            listEl.innerHTML = '';
            const searchVal = filterText.toLowerCase();

            const filtered = CAMBODIA_PROVINCES.filter(p => 
                p.kh.toLowerCase().includes(searchVal) || 
                p.en.toLowerCase().includes(searchVal)
            );

            if (filtered.length === 0) {
                listEl.classList.remove('active');
                return;
            }

            filtered.forEach(p => {
                const item = document.createElement('div');
                item.className = 'dropdown-item';
                const displayText = currentLanguage === 'km' ? `${p.kh} (${p.en})` : `${p.en} (${p.kh})`;
                item.textContent = displayText;
                
                item.addEventListener('click', () => {
                    inputEl.value = currentLanguage === 'km' ? p.kh : p.en;
                    listEl.classList.remove('active');
                    renderTrips();
                });
                listEl.appendChild(item);
            });
            listEl.classList.add('active');
        };

        inputEl.addEventListener('focus', () => {
            renderOptions(inputEl.value);
        });

        inputEl.addEventListener('input', () => {
            renderOptions(inputEl.value);
        });

        document.addEventListener('click', (e) => {
            if (!inputEl.contains(e.target) && !listEl.contains(e.target)) {
                listEl.classList.remove('active');
            }
        });
    }

    // Handle initial language state
    langSelect.value = currentLanguage;
    updateLanguageUI();

    // Language selector change listener
    langSelect.addEventListener('change', (e) => {
        currentLanguage = e.target.value;
        localStorage.setItem('lang', currentLanguage);
        updateLanguageUI();
        renderDrivers();
        renderPassengers();
        if (activeTabId === 'trips') {
            renderTrips();
        }
        if (activeTabId === 'revenue') {
            renderRevenueData();
        }
        if (map) loadMapTrips();
    });

    // Client-side translation updater
    function updateLanguageUI() {
        const dict = TRANSLATIONS[currentLanguage];
        
        // Translate elements with data-i18n
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (dict[key]) {
                el.textContent = dict[key];
            }
        });

        // Translate placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (dict[key]) {
                el.setAttribute('placeholder', dict[key]);
            }
        });

        // Set document title
        document.title = dict.doc_title;

        // Correct page title and subtitle dynamically based on active tab
        pageTitle.textContent = dict[`title_${activeTabId}`];
        pageSubtitle.textContent = dict[`subtitle_${activeTabId}`];
    }

    // Tab Switching Logic
    sidebarNav.forEach(nav => {
        nav.addEventListener('click', (e) => {
            e.preventDefault();
            activeTabId = nav.getAttribute('data-tab');

            sidebarNav.forEach(n => n.classList.remove('active'));
            nav.classList.add('active');

            tabPanes.forEach(pane => {
                pane.classList.remove('active');
                if (pane.id === `tab-${activeTabId}`) {
                    pane.classList.add('active');
                }
            });

            // Auto close mobile sidebar when tab clicked
            const sidebarEl = document.getElementById('app-sidebar');
            const overlayEl = document.getElementById('sidebar-overlay');
            if (sidebarEl && sidebarEl.classList.contains('active')) {
                sidebarEl.classList.remove('active');
                if (overlayEl) overlayEl.classList.remove('active');
            }

            // Update page title/subtitle
            updateLanguageUI();

            // Trigger map render
            if (activeTabId === 'map') {
                setTimeout(() => {
                    initMap();
                }, 100);
            }

            // Trigger trips load
            if (activeTabId === 'trips') {
                loadTrips();
            }

            // Trigger revenue render
            if (activeTabId === 'revenue') {
                loadRevenue();
            }

            // Trigger discounts load
            if (activeTabId === 'discounts') {
                loadDiscountsData();
            }

            // Trigger ads load
            if (activeTabId === 'ads') {
                loadAdsData();
            }

            // Trigger promotions load (fallback)
            if (activeTabId === 'promotions') {
                loadPromotionsData();
            }

            // Trigger messages load
            if (activeTabId === 'messages') {
                loadAdminMessages();
            }

            // Trigger vehicle models load
            if (activeTabId === 'vehicle-models') {
                loadVehicleModels();
            }
        });
    });

    // Mobile Sidebar Drawer Toggle Listeners
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarClose = document.getElementById('btn-close-sidebar');
    const appSidebar = document.getElementById('app-sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    if (sidebarToggle && appSidebar && sidebarOverlay) {
        sidebarToggle.addEventListener('click', () => {
            appSidebar.classList.add('active');
            sidebarOverlay.classList.add('active');
        });
    }

    if (sidebarClose && appSidebar && sidebarOverlay) {
        sidebarClose.addEventListener('click', () => {
            appSidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
        });
    }

    if (sidebarOverlay && appSidebar) {
        sidebarOverlay.addEventListener('click', () => {
            appSidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
        });
    }

    // Initialize Leaflet Map (Cambodia / Phnom Penh focus)
    function initMap() {
        if (map) {
            map.invalidateSize();
            loadMapTrips();
            return;
        }

        // Phnom Penh Coordinates
        const phnomPenh = [11.5564, 104.9282];
        
        // Initialize Map
        map = L.map('fleet-map', {
            zoomControl: true
        }).setView(phnomPenh, 8);

        // CartoDB Positron Tile Layer (Premium light style matching water #fbf9f8 / land #dbd9d9)
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(map);

        loadMapTrips();
    }

    // Load active driver tracking locations onto the map
    async function loadMapTrips() {
        if (!map) return;

        // Clear existing markers
        tripMarkers.forEach(m => map.removeLayer(m));
        tripMarkers = [];

        try {
            const response = await fetch(`${API_BASE}/trips`);
            const trips = await response.json();
            const dict = TRANSLATIONS[currentLanguage];

            trips.forEach(trip => {
                // Determine marker position: Use dynamic live location, fallback to mapped departure province coordinates
                let lat = trip.live_lat;
                let lng = trip.live_lng;

                if (lat === null || lng === null) {
                    const provinceCoords = PROVINCE_COORDINATES[trip.departure_province];
                    if (provinceCoords) {
                        lat = provinceCoords[0];
                        lng = provinceCoords[1];
                    } else {
                        // National capital fallback
                        lat = 11.5564;
                        lng = 104.9282;
                    }
                }

                // Color code markers based on driver status
                let markerColor = '#fbbc00'; // Warning (amber yellow) for scheduled
                if (trip.status === 'active') {
                    markerColor = '#006d43'; // Emerald green for active/live tracking
                } else if (trip.status === 'locked' || trip.status === 'cancelled') {
                    markerColor = '#ba1a1a'; // Red
                }

                // Create circular marker representing driver tracking point
                const marker = L.circleMarker([lat, lng], {
                    radius: 10,
                    fillColor: markerColor,
                    fillOpacity: 0.85,
                    stroke: true,
                    color: '#ffffff',
                    weight: 2
                }).addTo(map);

                const speedText = trip.live_speed_kph ? `${trip.live_speed_kph} km/h` : '0 km/h';
                const headingText = trip.live_heading ? `${trip.live_heading}°` : 'N/A';

                // Popup contents in active language
                const popupContent = `
                    <div style="min-width: 210px;">
                        <h4 style="margin-bottom: 5px; font-family: 'Manrope', sans-serif; font-size: 0.9rem; color: #001b44;">
                            ${trip.departure_province} <i class="fa-solid fa-arrow-right" style="font-size: 0.75rem; margin: 0 4px;"></i> ${trip.destination_province}
                        </h4>
                        <div style="font-size: 0.75rem; line-height: 1.4; color: #434750;">
                            <div><strong>${dict.txt_driver}:</strong> ${trip.driver_name} (${trip.driver_phone})</div>
                            <div><strong>${dict.txt_vehicle}:</strong> ${trip.vehicle_model} (${trip.vehicle_plate})</div>
                            <div><strong>${dict.txt_seats}:</strong> ${trip.available_seats} / ${trip.total_seats}</div>
                            <div style="margin-top: 5px; border-top: 1px solid rgba(0,0,0,0.05); padding-top: 5px;">
                                <strong>${dict.txt_status}:</strong> <span style="text-transform: uppercase; font-weight: 700; color: ${markerColor}">${trip.status}</span>
                            </div>
                            <div style="background: #f5f3f3; padding: 4px 8px; border-radius: 4px; margin-top: 6px;">
                                <div><i class="fa-solid fa-gauge"></i> <strong>${dict.txt_speed}:</strong> ${speedText}</div>
                                <div><i class="fa-solid fa-compass"></i> <strong>${dict.txt_heading}:</strong> ${headingText}</div>
                            </div>
                        </div>
                    </div>
                `;

                marker.bindPopup(popupContent);
                tripMarkers.push(marker);
            });
        } catch (error) {
            console.error('Error loading driver map coordinates:', error);
        }
    }

    // Fetch all trips for day-by-day operations
    async function loadTrips() {
        try {
            const response = await fetch(`${API_BASE}/trips`);
            currentTrips = await response.json();
            renderTrips();
        } catch (error) {
            console.error('Error loading trips database:', error);
        }
    }

    // Render Trips grouped day-by-day with ticket layout and status charts
    function renderTrips() {
        tripsByDayList.innerHTML = '';
        const dict = TRANSLATIONS[currentLanguage];

        const dateVal = tripDateFilter.value;
        const statusVal = tripStatusFilter.value;
        const departureVal = tripDepartureFilter.value.trim().toLowerCase();
        const destinationVal = tripDestinationFilter.value.trim().toLowerCase();
        const vehicleVal = tripVehicleFilter ? tripVehicleFilter.value.trim().toLowerCase() : '';

        // 1. Filter trips
        const filteredTrips = currentTrips.filter(trip => {
            const dateKey = trip.departure_time.split('T')[0];
            
            if (dateVal && dateKey !== dateVal) return false;
            if (statusVal && trip.status !== statusVal) return false;
            if (vehicleVal) {
                const tripVeh = (trip.vehicle_model || '').toLowerCase();
                const tripPlate = (trip.vehicle_plate || '').toLowerCase();
                if (!tripVeh.includes(vehicleVal) && !tripPlate.includes(vehicleVal)) return false;
            }
            
            // Check departure province matching either English or Khmer name
            if (departureVal) {
                const matchedProv = CAMBODIA_PROVINCES.find(p => 
                    p.kh.toLowerCase() === departureVal || 
                    p.en.toLowerCase() === departureVal
                );
                if (matchedProv) {
                    const departureTripLower = trip.departure_province.toLowerCase();
                    if (departureTripLower !== matchedProv.kh.toLowerCase() && departureTripLower !== matchedProv.en.toLowerCase()) {
                        return false;
                    }
                } else {
                    const tripDepLower = trip.departure_province.toLowerCase();
                    if (!tripDepLower.includes(departureVal)) return false;
                }
            }

            // Check destination province matching either English or Khmer name
            if (destinationVal) {
                const matchedProv = CAMBODIA_PROVINCES.find(p => 
                    p.kh.toLowerCase() === destinationVal || 
                    p.en.toLowerCase() === destinationVal
                );
                if (matchedProv) {
                    const destinationTripLower = trip.destination_province.toLowerCase();
                    if (destinationTripLower !== matchedProv.kh.toLowerCase() && destinationTripLower !== matchedProv.en.toLowerCase()) {
                        return false;
                    }
                } else {
                    const tripDestLower = trip.destination_province.toLowerCase();
                    if (!tripDestLower.includes(destinationVal)) return false;
                }
            }
            
            return true;
        });

        // 2. Compute and Render Analytics
        let totalBookings = 0;
        let totalActive = 0;
        let occupiedSeats = 0;
        let capacitySeats = 0;
        const statusCounts = { scheduled: 0, active: 0, completed: 0, cancelled: 0 };

        filteredTrips.forEach(t => {
            totalBookings += t.bookings_count;
            if (t.status === 'active') totalActive++;
            
            statusCounts[t.status] = (statusCounts[t.status] || 0) + 1;
            
            capacitySeats += t.total_seats;
            const booked = t.total_seats - t.available_seats;
            occupiedSeats += Math.max(0, booked);
        });

        const occupancyRate = capacitySeats > 0 ? Math.round((occupiedSeats / capacitySeats) * 100) : 0;

        // If filters are active, show filtered stats. Otherwise, fallback to the API-delivered summary values to respect "all get from api"!
        const hasActiveFilters = dateVal || statusVal || departureVal || destinationVal;
        
        if (hasActiveFilters) {
            kpiTripsTotal.textContent = filteredTrips.length;
            kpiTripsBookings.textContent = totalBookings;
            kpiTripsActive.textContent = totalActive;
            kpiTripsOccupancy.textContent = `${occupancyRate}%`;
        } else {
            // Re-load summary to ensure we are completely synced with the API
            loadSummary();
        }

        renderTripsStatusChart(statusCounts);

        // 3. Group by Day YYYY-MM-DD
        const groups = {};
        filteredTrips.forEach(trip => {
            const dateKey = trip.departure_time.split('T')[0];
            if (!groups[dateKey]) {
                groups[dateKey] = [];
            }
            groups[dateKey].push(trip);
        });

        const sortedDays = Object.keys(groups).sort((a, b) => b.localeCompare(a));

        if (sortedDays.length === 0) {
            tripsByDayList.innerHTML = `
                <div class="content-card text-center" style="padding: 3rem;">
                    <p class="body-md">${dict.txt_no_trips}</p>
                </div>
            `;
            return;
        }

        sortedDays.forEach(day => {
            const trips = groups[day];
            
            const dateObj = new Date(day);
            const dateStr = dateObj.toLocaleDateString(currentLanguage === 'en' ? 'en-US' : 'km-KH', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            const groupDiv = document.createElement('div');
            groupDiv.className = 'day-group';
            
            const tripsCountLabel = currentLanguage === 'en' 
                ? `${trips.length} trip(s)` 
                : `${trips.length} ជើងដំណើរ`;

            groupDiv.innerHTML = `
                <div class="day-group-header">
                    <span class="day-title">${dateStr}</span>
                    <span class="day-trip-count">${tripsCountLabel}</span>
                </div>
                <div class="trips-day-grid" id="day-grid-${day}"></div>
            `;

            tripsByDayList.appendChild(groupDiv);
            const grid = document.getElementById(`day-grid-${day}`);

            trips.forEach(trip => {
                const card = document.createElement('div');
                card.className = 'trip-ticket';
                card.style.cursor = 'pointer';
                
                let statusColorHex = '#fbbc00';
                if (trip.status === 'active') statusColorHex = '#006d43';
                else if (trip.status === 'completed') statusColorHex = '#001b44';
                else if (trip.status === 'cancelled') statusColorHex = '#ba1a1a';
                card.style.setProperty('--status-color', statusColorHex);
                
                card.addEventListener('click', () => openTripDetailPage(trip.id));

                const tripTimeStr = new Date(trip.departure_time).toLocaleTimeString(currentLanguage === 'en' ? 'en-US' : 'km-KH', {
                    hour: 'numeric',
                    minute: '2-digit'
                });

                card.innerHTML = `
                    <div class="ticket-main">
                        <div class="ticket-train-route">
                            <div class="route-station dep-station">
                                <span class="time-large">${tripTimeStr}</span>
                                <span class="station-name">${trip.departure_province}</span>
                            </div>
                            <div class="route-connector-line">
                                <span class="route-dot"></span>
                                <div class="route-track">
                                    <i class="fa-solid fa-train-subway"></i>
                                </div>
                                <span class="route-dot"></span>
                            </div>
                            <div class="route-station arr-station">
                                <span class="time-large">—:—</span>
                                <span class="station-name">${trip.destination_province}</span>
                            </div>
                        </div>
                        <div class="ticket-footer-row">
                            <span class="ticket-price">៛${trip.price_per_seat.toLocaleString()}</span>
                            <span class="ticket-status-badge status-${trip.status}">${trip.status}</span>
                        </div>
                    </div>

                    <div class="ticket-stub-modern">
                        <div class="stub-meta-row">
                            <div class="stub-meta-item">
                                <i class="fa-solid fa-chair"></i>
                                <span class="stub-seats">${trip.available_seats}/${trip.total_seats}</span>
                                <span class="stub-label" data-i18n="txt_seats">SEATS</span>
                            </div>
                            <div class="stub-meta-item" style="background-color: var(--color-success-container); border-color: var(--color-success-container);">
                                <i class="fa-solid fa-ticket" style="color: var(--color-success);"></i>
                                <span class="stub-bookings" style="color: var(--color-success);">${trip.bookings_count}</span>
                                <span class="stub-label" style="color: var(--color-success); font-weight:800;">BOOKED</span>
                            </div>
                        </div>
                        <div class="stub-driver-info">
                            <div class="stub-driver-name" title="${trip.driver_name}">${trip.driver_name}</div>
                            <div class="stub-car-plate">${trip.vehicle_plate}</div>
                        </div>
                    </div>
                `;

                grid.appendChild(card);
            });
        });
    }

    // Render trips status Doughnut chart
    function renderTripsStatusChart(statusCounts) {
        const ctx = document.getElementById('trips-status-chart').getContext('2d');
        const dict = TRANSLATIONS[currentLanguage];

        const labels = [
            dict.filter_status_scheduled,
            dict.filter_status_active,
            dict.filter_status_completed,
            dict.filter_status_cancelled
        ];
        const data = [
            statusCounts.scheduled,
            statusCounts.active,
            statusCounts.completed,
            statusCounts.cancelled
        ];

        if (tripsStatusChart) {
            tripsStatusChart.destroy();
        }

        tripsStatusChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        '#fbbc00', // yellow/scheduled
                        '#006d43', // green/active
                        '#001b44', // navy/completed
                        '#ba1a1a'  // red/cancelled
                    ],
                    borderWidth: 1,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 10,
                            font: {
                                family: "'Manrope', sans-serif",
                                size: 10,
                                weight: '600'
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }

    // Dedicated Trip Detail Page View & Router
    let pageDetailMap = null;
    let pageDetailMarker = null;

    window.openTripDetailPage = async (tripId) => {
        if (!tripId) return;

        // Update URL Hash without triggering reload
        const targetHash = `trip-detail?id=${tripId}`;
        if (window.location.hash !== `#${targetHash}`) {
            window.location.hash = targetHash;
        }

        // Show tab-trip-detail pane
        tabPanes.forEach(pane => {
            pane.classList.remove('active');
            if (pane.id === 'tab-trip-detail') {
                pane.classList.add('active');
            }
        });
        sidebarNav.forEach(n => n.classList.remove('active'));

        // Find trip in currentTrips or fetch from backend
        let trip = currentTrips.find(t => t.id === tripId);
        if (!trip) {
            try {
                const response = await fetch(`${API_BASE}/trips`);
                const trips = await response.json();
                currentTrips = trips;
                trip = currentTrips.find(t => t.id === tripId);
            } catch (err) {
                console.error('Error fetching trips for detail page:', err);
            }
        }

        if (!trip) {
            console.error('Trip not found for id:', tripId);
            return;
        }

        // Populate Form Controls
        const editIdEl = document.getElementById('page-edit-trip-id');
        if (editIdEl) editIdEl.value = trip.id;
        const editStatusEl = document.getElementById('page-edit-trip-status');
        if (editStatusEl) editStatusEl.value = trip.status;
        const editPriceEl = document.getElementById('page-edit-trip-price');
        if (editPriceEl) editPriceEl.value = Math.round(trip.price_per_seat);
        const editTotalSeatsEl = document.getElementById('page-edit-trip-total-seats');
        if (editTotalSeatsEl) editTotalSeatsEl.value = trip.total_seats;
        const editAvailSeatsEl = document.getElementById('page-edit-trip-avail-seats');
        if (editAvailSeatsEl) editAvailSeatsEl.value = trip.available_seats;

        // Populate Headers & Meta
        const routeTitleEl = document.getElementById('page-trip-route-title');
        if (routeTitleEl) routeTitleEl.textContent = `${trip.departure_province} → ${trip.destination_province}`;

        const statusBadgeEl = document.getElementById('page-trip-status-badge');
        if (statusBadgeEl) {
            statusBadgeEl.textContent = trip.status;
            statusBadgeEl.className = `ticket-status-badge status-${trip.status}`;
        }

        const idBadgeEl = document.getElementById('page-trip-id-badge');
        if (idBadgeEl) idBadgeEl.textContent = `ID: ${trip.id}`;

        const depProvEl = document.getElementById('page-dep-province');
        if (depProvEl) depProvEl.textContent = trip.departure_province;
        const destProvEl = document.getElementById('page-dest-province');
        if (destProvEl) destProvEl.textContent = trip.destination_province;

        const depDate = new Date(trip.departure_time);
        const timeStr = depDate.toLocaleString(currentLanguage === 'en' ? 'en-US' : 'km-KH', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit'
        });
        const depTimeEl = document.getElementById('page-dep-time');
        if (depTimeEl) depTimeEl.textContent = timeStr;

        const priceEl = document.getElementById('page-price-per-seat');
        if (priceEl) priceEl.textContent = `៛${trip.price_per_seat.toLocaleString()}`;

        const driverNameEl = document.getElementById('page-driver-name');
        if (driverNameEl) driverNameEl.textContent = trip.driver_name || '—';

        const driverPhoneEl = document.getElementById('page-driver-phone');
        if (driverPhoneEl) {
            if (trip.driver_phone) {
                driverPhoneEl.innerHTML = `<a href="tel:${trip.driver_phone}" style="color: var(--color-primary); font-weight:700;"><i class="fa-solid fa-phone"></i> ${trip.driver_phone}</a>`;
            } else {
                driverPhoneEl.textContent = '—';
            }
        }

        const vehicleModelEl = document.getElementById('page-vehicle-model');
        if (vehicleModelEl) vehicleModelEl.textContent = trip.vehicle_model || '—';
        const vehiclePlateEl = document.getElementById('page-vehicle-plate');
        if (vehiclePlateEl) vehiclePlateEl.textContent = trip.vehicle_plate || '—';

        const seatsOccEl = document.getElementById('page-seats-occupancy');
        if (seatsOccEl) {
            const booked = trip.total_seats - trip.available_seats;
            seatsOccEl.textContent = `${booked} / ${trip.total_seats} booked (${trip.available_seats} remaining)`;
        }

        const bookingsCountEl = document.getElementById('page-bookings-count');
        if (bookingsCountEl) bookingsCountEl.textContent = `${trip.bookings_count} bookings`;

        // Telemetry GPS
        let lat = trip.live_lat;
        let lng = trip.live_lng;
        if (lat === null || lng === null) {
            const provinceCoords = PROVINCE_COORDINATES[trip.departure_province];
            if (provinceCoords) {
                lat = provinceCoords[0];
                lng = provinceCoords[1];
            } else {
                lat = 11.5564;
                lng = 104.9282;
            }
        }

        const gpsLatEl = document.getElementById('page-gps-lat');
        if (gpsLatEl) gpsLatEl.textContent = lat ? lat.toFixed(5) : 'N/A';
        const gpsLngEl = document.getElementById('page-gps-lng');
        if (gpsLngEl) gpsLngEl.textContent = lng ? lng.toFixed(5) : 'N/A';
        const gpsSpeedEl = document.getElementById('page-gps-speed');
        if (gpsSpeedEl) gpsSpeedEl.textContent = trip.live_speed_kph ? `${trip.live_speed_kph} km/h` : '0 km/h';
        const gpsHeadingEl = document.getElementById('page-gps-heading');
        if (gpsHeadingEl) gpsHeadingEl.textContent = trip.live_heading ? `${trip.live_heading}°` : 'N/A';

        // Render Leaflet map container
        setTimeout(() => {
            initPageDetailMap(lat, lng);
        }, 150);

        // Fetch & Render Bookings
        loadTripBookings(trip.id);
    };

    function initPageDetailMap(lat, lng) {
        const mapContainer = document.getElementById('page-trip-detail-map');
        if (!mapContainer) return;

        if (pageDetailMap) {
            pageDetailMap.setView([lat, lng], 11);
            if (pageDetailMarker) {
                pageDetailMarker.setLatLng([lat, lng]);
            } else {
                pageDetailMarker = L.circleMarker([lat, lng], {
                    radius: 9,
                    fillColor: '#006d43',
                    fillOpacity: 0.9,
                    stroke: true,
                    color: '#ffffff',
                    weight: 2
                }).addTo(pageDetailMap);
            }
            pageDetailMap.invalidateSize();
            return;
        }

        pageDetailMap = L.map('page-trip-detail-map', {
            zoomControl: true
        }).setView([lat, lng], 11);

        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            maxZoom: 20
        }).addTo(pageDetailMap);

        pageDetailMarker = L.circleMarker([lat, lng], {
            radius: 9,
            fillColor: '#006d43',
            fillOpacity: 0.9,
            stroke: true,
            color: '#ffffff',
            weight: 2
        }).addTo(pageDetailMap);

        pageDetailMap.invalidateSize();
    }

    async function loadTripBookings(tripId) {
        const tableBody = document.getElementById('page-trip-bookings-list');
        if (!tableBody) return;
        tableBody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding: 1.5rem;"><i class="fa-solid fa-spinner fa-spin"></i> Loading passenger bookings...</td></tr>';

        try {
            const response = await fetch(`${API_BASE}/trips/${tripId}/bookings`);
            if (response.ok) {
                const bookings = await response.json();
                if (bookings.length === 0) {
                    tableBody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding: 1.5rem; color: var(--color-text-secondary);">No passenger bookings recorded for this trip yet.</td></tr>';
                    return;
                }
                tableBody.innerHTML = '';
                bookings.forEach(b => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td><strong style="color: var(--color-primary);">${escapeHtml(b.passenger_name || 'Passenger')}</strong></td>
                        <td>${escapeHtml(b.passenger_phone || '—')}</td>
                        <td><span class="stub-seats">${b.seats_booked}</span></td>
                        <td><strong>៛${(b.total_price || 0).toLocaleString()}</strong></td>
                        <td><span style="font-size: 0.8rem; text-transform: uppercase;">${b.payment_method || 'CASH'}</span></td>
                        <td><span class="ticket-status-badge status-${b.payment_status === 'paid' ? 'completed' : 'scheduled'}">${b.payment_status || 'PENDING'}</span></td>
                        <td><span class="ticket-status-badge status-${b.status === 'boarded' || b.status === 'completed' ? 'active' : 'scheduled'}">${b.status || 'BOOKED'}</span></td>
                    `;
                    tableBody.appendChild(tr);
                });
            } else {
                tableBody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding: 1.5rem; color: var(--color-text-secondary);">No passenger bookings found for this trip.</td></tr>';
            }
        } catch (error) {
            console.error('Error loading trip bookings:', error);
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding: 1.5rem; color: var(--color-text-secondary);">No passenger bookings found for this trip.</td></tr>';
        }
    }

    // Save changes to trip details from Page View Form
    const pageTripEditForm = document.getElementById('page-trip-edit-form');
    if (pageTripEditForm) {
        pageTripEditForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const dict = TRANSLATIONS[currentLanguage];
            const tripId = document.getElementById('page-edit-trip-id').value;

            const payload = {
                status: document.getElementById('page-edit-trip-status').value,
                price_per_seat: parseFloat(document.getElementById('page-edit-trip-price').value),
                total_seats: parseInt(document.getElementById('page-edit-trip-total-seats').value),
                available_seats: parseInt(document.getElementById('page-edit-trip-avail-seats').value)
            };

            try {
                const response = await fetch(`${API_BASE}/trips/${tripId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    showToast(dict.toast_trip_saved);
                    loadTrips();
                    loadSummary();
                    openTripDetailPage(tripId);
                } else {
                    showToast(dict.toast_network_error, true);
                }
            } catch (error) {
                console.error('Error saving trip edits:', error);
                showToast(dict.toast_network_error, true);
            }
        });
    }

    // Delete trip from Page View
    const pageBtnDeleteTrip = document.getElementById('page-btn-delete-trip');
    if (pageBtnDeleteTrip) {
        pageBtnDeleteTrip.addEventListener('click', async () => {
            const dict = TRANSLATIONS[currentLanguage];
            const tripId = document.getElementById('page-edit-trip-id').value;

            if (!confirm(dict.txt_confirm_delete_trip)) {
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/trips/${tripId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    showToast(dict.toast_trip_deleted);
                    window.location.hash = 'trips';
                    loadTrips();
                    loadSummary();
                } else {
                    showToast(dict.toast_network_error, true);
                }
            } catch (error) {
                console.error('Error deleting trip:', error);
                showToast(dict.toast_network_error, true);
            }
        });
    }

    // Back to Trips Button
    const btnBackToTrips = document.getElementById('btn-back-to-trips');
    if (btnBackToTrips) {
        btnBackToTrips.addEventListener('click', () => {
            window.location.hash = 'trips';
            sidebarNav.forEach(n => {
                n.classList.remove('active');
                if (n.getAttribute('data-tab') === 'trips') n.classList.add('active');
            });
            tabPanes.forEach(pane => {
                pane.classList.remove('active');
                if (pane.id === 'tab-trips') pane.classList.add('active');
            });
        });
    }

    // URL Hash Routing Handler
    function handleRouteHash() {
        const hash = window.location.hash.substring(1);
        if (!hash) return;

        if (hash.startsWith('trip-detail')) {
            const params = new URLSearchParams(hash.includes('?') ? hash.split('?')[1] : '');
            const tripId = params.get('id');
            if (tripId) {
                openTripDetailPage(tripId);
            }
        } else {
            const nav = document.querySelector(`.sidebar-nav-item[data-tab="${hash}"]`);
            if (nav) {
                nav.click();
            }
        }
    }

    window.addEventListener('hashchange', handleRouteHash);
    setTimeout(handleRouteHash, 300);

    // Filters event listeners
    tripDateFilter.addEventListener('change', renderTrips);
    tripStatusFilter.addEventListener('change', renderTrips);
    tripDepartureFilter.addEventListener('input', renderTrips);
    tripDestinationFilter.addEventListener('input', renderTrips);
    if (tripVehicleFilter) tripVehicleFilter.addEventListener('input', renderTrips);

    btnClearDateFilter.addEventListener('click', () => {
        tripDateFilter.value = '';
        tripStatusFilter.value = '';
        tripDepartureFilter.value = '';
        tripDestinationFilter.value = '';
        if (tripVehicleFilter) tripVehicleFilter.value = '';
        renderTrips();
    });

    // Refresh Overview KPIs
    async function loadSummary() {
        try {
            const response = await fetch(`${API_BASE}/summary`);
            const data = await response.json();

            kpiTotalDrivers.textContent = data.total_drivers;
            kpiTotalPassengers.textContent = data.total_passengers;
            kpiActiveTrips.textContent = data.active_trips;
            
            // Format Khmer Riel and USD Owed
            kpiTotalOwed.textContent = `៛${data.total_owed_khr.toLocaleString()}`;
            kpiTotalOwedUsd.textContent = `$${data.total_owed_usd.toFixed(2)} USD`;

            // Operational KPIs directly from API
            if (kpiTripsTotal) kpiTripsTotal.textContent = data.total_trips;
            if (kpiTripsBookings) kpiTripsBookings.textContent = data.total_bookings;
            if (kpiTripsActive) kpiTripsActive.textContent = data.active_trips;
            if (kpiTripsOccupancy) kpiTripsOccupancy.textContent = `${Math.round(data.seat_occupancy_rate)}%`;

            // Populate settings inputs
            appSettings = data.settings;
            enableDigitalPaymentInput.checked = appSettings.enable_digital_payment;
            autoLockOnLimitInput.checked = appSettings.auto_lock_on_limit;
            driverCashDebtLimitUsdInput.value = appSettings.driver_cash_debt_limit_usd;
            driverCashDebtLimitKhrInput.value = appSettings.driver_cash_debt_limit_khr;
        } catch (error) {
            console.error('Error loading summary stats:', error);
        }
    }

    // Save Settings
    settingsForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const dict = TRANSLATIONS[currentLanguage];
        
        const payload = {
            enable_digital_payment: enableDigitalPaymentInput.checked,
            auto_lock_on_limit: autoLockOnLimitInput.checked,
            driver_cash_debt_limit_usd: parseFloat(driverCashDebtLimitUsdInput.value),
            driver_cash_debt_limit_khr: parseInt(driverCashDebtLimitKhrInput.value)
        };

        try {
            const response = await fetch(`${API_BASE}/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                showToast(dict.toast_settings_saved);
                loadSummary();
                if (activeTabId === 'drivers') loadDrivers();
            } else {
                showToast(dict.toast_settings_error, true);
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            showToast(dict.toast_network_error, true);
        }
    });

    // Seed Demo Data
    if (btnSeedDemo && presetStatus) {
        btnSeedDemo.addEventListener('click', async () => {
            const dict = TRANSLATIONS[currentLanguage];
            btnSeedDemo.disabled = true;
            presetStatus.textContent = dict.txt_seeding;
            presetStatus.style.color = 'var(--color-primary)';
            
            try {
                const response = await fetch(`${API_BASE}/seed-demo`, {
                    method: 'POST'
                });

                if (response.ok) {
                    presetStatus.textContent = dict.txt_seeding_success;
                    presetStatus.style.color = 'var(--color-success)';
                    loadSummary();
                    if (map) loadMapTrips();
                    loadDrivers();
                    loadPassengers();
                    if (activeTabId === 'trips') loadTrips();
                    if (activeTabId === 'revenue') loadRevenue();
                } else {
                    presetStatus.textContent = dict.txt_seeding_error;
                    presetStatus.style.color = 'var(--color-error)';
                }
            } catch (error) {
                console.error('Error seeding demo data:', error);
                presetStatus.textContent = dict.toast_network_error;
                presetStatus.style.color = 'var(--color-error)';
            } finally {
                setTimeout(() => {
                    btnSeedDemo.disabled = false;
                    presetStatus.textContent = '';
                }, 5000);
            }
        });
    }

    // Load Drivers
    async function loadDrivers() {
        try {
            const response = await fetch(`${API_BASE}/users?role=driver`);
            currentDrivers = await response.json();
            driverCurrentPage = 1;
            renderDrivers();
        } catch (error) {
            console.error('Error loading drivers:', error);
        }
    }

    // Render Drivers Grid with client-side Pagination
    function renderDrivers() {
        driversList.innerHTML = '';
        const searchVal = searchDriversInput.value.toLowerCase();
        const dict = TRANSLATIONS[currentLanguage];

        const filtered = currentDrivers.filter(driver => 
            driver.full_name.toLowerCase().includes(searchVal) || 
            driver.phone.includes(searchVal)
        );

        const totalPages = Math.ceil(filtered.length / driverPageSize) || 1;
        if (driverCurrentPage > totalPages) {
            driverCurrentPage = totalPages;
        }

        const paginated = filtered.slice((driverCurrentPage - 1) * driverPageSize, driverCurrentPage * driverPageSize);

        if (filtered.length === 0) {
            driversList.innerHTML = `
                <div class="content-card col-span-3 text-center" style="grid-column: span 3; padding: 2rem;">
                    <p class="body-md">${dict.txt_no_drivers}</p>
                </div>
            `;
            document.getElementById('drivers-pagination').innerHTML = '';
            return;
        }

        paginated.forEach(driver => {
            const isLocked = driver.wallet ? driver.wallet.is_locked : false;
            const walletOwedKhr = driver.wallet ? driver.wallet.total_owed_khr : 0;
            const walletOwedUsd = driver.wallet ? driver.wallet.total_owed_usd : 0;
            
            // Dynamically resolve defaults from API settings to avoid hardcoded fallbacks
            const fallbackLimitKhr = appSettings ? appSettings.driver_cash_debt_limit_khr : 80000;
            const fallbackLimitUsd = appSettings ? appSettings.driver_cash_debt_limit_usd : 20;

            const creditLimitKhr = driver.wallet && driver.wallet.credit_limit_khr !== null ? driver.wallet.credit_limit_khr : fallbackLimitKhr;
            const creditLimitUsd = driver.wallet && driver.wallet.credit_limit_usd !== null ? driver.wallet.credit_limit_usd : fallbackLimitUsd;

            const card = document.createElement('div');
            card.className = 'driver-card';

            const mTier = driver.membership_code || 'normal';
            
            // Build driver card HTML in selected language
            card.innerHTML = `
                <div class="driver-card-header">
                    <div class="driver-info-main">
                        <span class="driver-name">${driver.full_name}</span>
                        <span class="driver-phone">${driver.phone}</span>
                        <div class="driver-tier-block" style="margin-top: 4px;">
                            <span class="membership-badge ${mTier}">${driver.membership_label || 'Normal'}</span>
                        </div>
                    </div>
                    <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 4px;">
                        <span class="status-pill ${driver.is_verified ? 'active' : 'unverified'}">
                            ${driver.is_verified ? `<i class="fa-solid fa-circle-check"></i> ${dict.status_verified}` : dict.status_unverified}
                        </span>
                        <span class="status-pill ${isLocked ? 'locked' : 'active'}" style="margin-top: 4px;">
                            ${isLocked ? `<i class="fa-solid fa-lock"></i> ${dict.status_locked}` : `<i class="fa-solid fa-circle-check"></i> ${dict.status_open}`}
                        </span>
                    </div>
                </div>

                <div class="driver-stats-row">
                    <div class="driver-stat">
                        <span class="driver-stat-val">${driver.rating_avg.toFixed(1)} <i class="fa-solid fa-star" style="color:var(--color-warning); font-size:0.75rem;"></i></span>
                        <span class="driver-stat-lbl">Rating</span>
                    </div>
                    <div class="driver-stat">
                        <span class="driver-stat-val">${driver.rating_count}</span>
                        <span class="driver-stat-lbl">Votes</span>
                    </div>
                    <div class="driver-stat">
                        <span class="driver-stat-val">${driver.completed_trips}</span>
                        <span class="driver-stat-lbl">Trips</span>
                    </div>
                </div>

                <div class="driver-financial-block">
                    <div class="financial-owed-row">
                        <span class="financial-owed-lbl">${dict.kpi_debt_owed}</span>
                        <span class="financial-owed-val">៛${walletOwedKhr.toLocaleString()} / $${walletOwedUsd.toFixed(2)}</span>
                    </div>
                    <div class="financial-limit-meta">
                        Limit: ៛${creditLimitKhr.toLocaleString()} / $${creditLimitUsd.toFixed(2)}
                    </div>
                </div>

                <div class="driver-actions">
                    <button class="btn btn-chip ${driver.is_verified ? 'secondary' : 'success'}" onclick="toggleVerify('${driver.id}')">
                        ${driver.is_verified ? dict.btn_unverify : dict.btn_verify}
                    </button>
                    <button class="btn btn-chip ${isLocked ? 'success' : 'danger'}" onclick="toggleLock('${driver.id}', ${isLocked})">
                        ${isLocked ? dict.btn_unlock : dict.btn_lock}
                    </button>
                    
                    <div class="driver-actions-bottom">
                        <select onchange="changeMembershipTier('${driver.id}', this.value)">
                            <option value="normal" ${mTier === 'normal' ? 'selected' : ''}>${dict.option_normal}</option>
                            <option value="pro" ${mTier === 'pro' ? 'selected' : ''}>${dict.option_pro}</option>
                            <option value="vip" ${mTier === 'vip' ? 'selected' : ''}>${dict.option_vip}</option>
                        </select>
                        <button class="btn btn-primary btn-chip" style="flex-grow:0; padding: 0.4rem 0.8rem;" onclick="openSettleModal('${driver.id}', '${driver.full_name}', ${walletOwedKhr}, ${walletOwedUsd})">
                            <i class="fa-solid fa-hand-holding-dollar"></i> ${dict.btn_settle}
                        </button>
                    </div>
                </div>
            `;
            driversList.appendChild(card);
        });

        renderDriversPagination(filtered.length);
    }

    // Driver pagination button builder
    function renderDriversPagination(totalCount) {
        const pagEl = document.getElementById('drivers-pagination');
        pagEl.innerHTML = '';
        
        const totalPages = Math.ceil(totalCount / driverPageSize) || 1;

        // Prev btn
        const prevBtn = document.createElement('button');
        prevBtn.className = 'btn btn-chip secondary';
        prevBtn.disabled = driverCurrentPage === 1;
        prevBtn.innerHTML = '<i class="fa-solid fa-chevron-left"></i>';
        prevBtn.addEventListener('click', () => {
            if (driverCurrentPage > 1) {
                driverCurrentPage--;
                renderDrivers();
            }
        });

        // Page info
        const info = document.createElement('span');
        info.className = 'page-info';
        info.textContent = currentLanguage === 'en' 
            ? `Page ${driverCurrentPage} of ${totalPages}`
            : `ទំព័រ ${driverCurrentPage} នៃ ${totalPages}`;

        // Next btn
        const nextBtn = document.createElement('button');
        nextBtn.className = 'btn btn-chip secondary';
        nextBtn.disabled = driverCurrentPage === totalPages;
        nextBtn.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
        nextBtn.addEventListener('click', () => {
            if (driverCurrentPage < totalPages) {
                driverCurrentPage++;
                renderDrivers();
            }
        });

        pagEl.appendChild(prevBtn);
        pagEl.appendChild(info);
        pagEl.appendChild(nextBtn);
    }

    searchDriversInput.addEventListener('input', () => {
        driverCurrentPage = 1;
        renderDrivers();
    });

    searchPassengersInput.addEventListener('input', () => {
        passengerCurrentPage = 1;
        renderPassengers();
    });

    // Global action helpers
    window.toggleVerify = async (userId) => {
        const dict = TRANSLATIONS[currentLanguage];
        try {
            const response = await fetch(`${API_BASE}/users/${userId}/toggle-verification`, {
                method: 'POST'
            });

            if (response.ok) {
                showToast(dict.toast_verified);
                loadDrivers();
                loadPassengers();
                loadSummary();
            } else {
                showToast(dict.toast_network_error, true);
            }
        } catch (error) {
            console.error('Error toggling verification:', error);
            showToast(dict.toast_network_error, true);
        }
    };

    window.toggleLock = async (userId, currentlyLocked) => {
        const dict = TRANSLATIONS[currentLanguage];
        let reason = null;
        if (!currentlyLocked) {
            reason = prompt(currentLanguage === 'en' ? 'Enter a reason for manual lock override (optional):' : 'បញ្ចូលមូលហេតុនៃការចាក់សោ (ស្រេចចិត្ត)៖');
            if (reason === null) return;
        }

        const url = reason 
            ? `${API_BASE}/users/${userId}/toggle-wallet-lock?reason=${encodeURIComponent(reason)}` 
            : `${API_BASE}/users/${userId}/toggle-wallet-lock`;

        try {
            const response = await fetch(url, {
                method: 'POST'
            });

            if (response.ok) {
                showToast(dict.toast_lock_updated);
                loadDrivers();
            } else {
                showToast(dict.toast_network_error, true);
            }
        } catch (error) {
            console.error('Error toggling wallet lock:', error);
            showToast(dict.toast_network_error, true);
        }
    };

    window.changeMembershipTier = async (userId, tier) => {
        const dict = TRANSLATIONS[currentLanguage];
        try {
            const response = await fetch(`${API_BASE}/users/${userId}/change-membership?tier=${tier}`, {
                method: 'POST'
            });

            if (response.ok) {
                showToast(dict.toast_membership_updated);
                loadDrivers();
            } else {
                showToast(dict.toast_network_error, true);
            }
        } catch (error) {
            console.error('Error changing membership:', error);
            showToast(dict.toast_network_error, true);
        }
    };

    // Settle Modal Control
    window.openSettleModal = (driverId, name, owedKhr, owedUsd) => {
        settleDriverId.value = driverId;
        settleDriverName.textContent = name;
        settleDriverDebt.textContent = `៛${owedKhr.toLocaleString()} / $${owedUsd.toFixed(2)} USD`;
        settleNotesInput.value = '';
        settleModal.classList.add('active');
    };

    function closeModal() {
        settleModal.classList.remove('active');
    }

    btnCloseModal.addEventListener('click', closeModal);
    btnCancelSettle.addEventListener('click', closeModal);
    settleModal.addEventListener('click', (e) => {
        if (e.target === settleModal) closeModal();
    });

    // Record Debt Settlement
    settleForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const dict = TRANSLATIONS[currentLanguage];

        const payload = {
            driver_id: settleDriverId.value,
            notes: settleNotesInput.value
        };

        try {
            const response = await fetch(`${API_BASE}/wallet/settle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                showToast(dict.toast_settled);
                closeModal();
                loadDrivers();
                loadSummary();
            } else {
                showToast(dict.toast_network_error, true);
            }
        } catch (error) {
            console.error('Error settling debt:', error);
            showToast(dict.toast_network_error, true);
        }
    });

    // Load Passengers
    async function loadPassengers() {
        try {
            const response = await fetch(`${API_BASE}/users?role=passenger`);
            currentPassengers = await response.json();
            passengerCurrentPage = 1;
            renderPassengers();
        } catch (error) {
            console.error('Error loading passengers:', error);
        }
    }

    // Render Passengers list table with Pagination
    function renderPassengers() {
        passengersList.innerHTML = '';
        const searchVal = searchPassengersInput.value.toLowerCase();
        const dict = TRANSLATIONS[currentLanguage];

        const filtered = currentPassengers.filter(passenger => 
            passenger.full_name.toLowerCase().includes(searchVal) || 
            passenger.phone.includes(searchVal)
        );

        const totalPages = Math.ceil(filtered.length / passengerPageSize) || 1;
        if (passengerCurrentPage > totalPages) {
            passengerCurrentPage = totalPages;
        }

        const paginated = filtered.slice((passengerCurrentPage - 1) * passengerPageSize, passengerCurrentPage * passengerPageSize);

        if (filtered.length === 0) {
            passengersList.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center" style="padding: 2rem; color: var(--color-on-surface-variant);">
                        ${dict.txt_no_passengers}
                    </td>
                </tr>
            `;
            document.getElementById('passengers-pagination').innerHTML = '';
            return;
        }

        paginated.forEach(p => {
            const tr = document.createElement('tr');
            
            const dateStr = new Date(p.created_at).toLocaleDateString(currentLanguage === 'en' ? 'en-US' : 'km-KH', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });

            tr.innerHTML = `
                <td style="font-family: var(--font-display); font-weight:600; color:var(--color-primary);">${p.full_name}</td>
                <td>${p.phone}</td>
                <td>
                    <span class="status-pill ${p.is_verified ? 'active' : 'unverified'}">
                        ${p.is_verified ? `<i class="fa-solid fa-circle-check"></i> ${dict.status_verified}` : dict.status_unverified}
                    </span>
                </td>
                <td>${p.rating_avg.toFixed(1)} <i class="fa-solid fa-star" style="color:var(--color-warning); font-size:0.75rem;"></i></td>
                <td>${p.completed_trips} ${currentLanguage === 'en' ? 'bookings' : 'ការកក់'}</td>
                <td>${dateStr}</td>
                <td class="text-right">
                    <button class="btn-chip ${p.is_verified ? 'danger' : 'success'}" onclick="toggleVerify('${p.id}')">
                        ${p.is_verified ? dict.btn_unverify : dict.btn_verify}
                    </button>
                </td>
            `;
            passengersList.appendChild(tr);
        });

        renderPassengersPagination(filtered.length);
    }

    // Passengers pagination button builder
    function renderPassengersPagination(totalCount) {
        const pagEl = document.getElementById('passengers-pagination');
        pagEl.innerHTML = '';
        
        const totalPages = Math.ceil(totalCount / passengerPageSize) || 1;

        // Prev btn
        const prevBtn = document.createElement('button');
        prevBtn.className = 'btn btn-chip secondary';
        prevBtn.disabled = passengerCurrentPage === 1;
        prevBtn.innerHTML = '<i class="fa-solid fa-chevron-left"></i>';
        prevBtn.addEventListener('click', () => {
            if (passengerCurrentPage > 1) {
                passengerCurrentPage--;
                renderPassengers();
            }
        });

        // Page info
        const info = document.createElement('span');
        info.className = 'page-info';
        info.textContent = currentLanguage === 'en' 
            ? `Page ${passengerCurrentPage} of ${totalPages}`
            : `ទំព័រ ${passengerCurrentPage} នៃ ${totalPages}`;

        // Next btn
        const nextBtn = document.createElement('button');
        nextBtn.className = 'btn btn-chip secondary';
        nextBtn.disabled = passengerCurrentPage === totalPages;
        nextBtn.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
        nextBtn.addEventListener('click', () => {
            if (passengerCurrentPage < totalPages) {
                passengerCurrentPage++;
                renderPassengers();
            }
        });

        pagEl.appendChild(prevBtn);
        pagEl.appendChild(info);
        pagEl.appendChild(nextBtn);
    }

    // Toast Notifications
    function showToast(message, isError = false) {
        const toast = document.createElement('div');
        toast.style.position = 'fixed';
        toast.style.bottom = '20px';
        toast.style.right = '20px';
        toast.style.background = isError ? 'var(--color-error)' : 'var(--color-primary)';
        toast.style.color = '#ffffff';
        toast.style.padding = '10px 20px';
        toast.style.borderRadius = 'var(--radius-xl)';
        toast.style.boxShadow = '0 10px 20px rgba(0, 27, 68, 0.2)';
        toast.style.fontFamily = 'var(--font-display)';
        toast.style.fontWeight = '600';
        toast.style.fontSize = '0.8rem';
        toast.style.zIndex = '99999';
        toast.style.transition = 'all 0.3s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';

        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        }, 50);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 4000);
    }

    // Refresh action
    btnRefreshAll.addEventListener('click', () => {
        loadSummary();
        if (map) loadMapTrips();
        loadDrivers();
        loadPassengers();
        if (activeTabId === 'trips') loadTrips();
        if (activeTabId === 'revenue') loadRevenue();
        if (activeTabId === 'discounts') loadDiscountsData();
        if (activeTabId === 'ads') loadAdsData();
        if (activeTabId === 'promotions') loadPromotionsData();
        showToast(TRANSLATIONS[currentLanguage].toast_refresh);
    });
    

    if (btnAddDiscount) {
        btnAddDiscount.addEventListener('click', () => {
            formModalDiscount.reset();
            document.getElementById('edit-discount-id').value = '';
            document.getElementById('discount-modal-title').textContent = currentLanguage === 'en' ? 'Create Discount Ticket' : 'បង្កើតប័ណ្ណបញ្ចុះតម្លៃ';
            document.getElementById('discount-modal-save-label').textContent = currentLanguage === 'en' ? 'Create Ticket' : 'បង្កើតប័ណ្ណ';
            discountModal.classList.add('active');
        });
    }

    if (btnCloseDiscountModal) {
        btnCloseDiscountModal.addEventListener('click', () => {
            discountModal.classList.remove('active');
        });
    }

    if (btnAddAd) {
        btnAddAd.addEventListener('click', () => {
            formModalAd.reset();
            document.getElementById('edit-ad-id').value = '';
            modalAdImageUrl.value = '';
            if (modalAdImagePreview) {
                modalAdImagePreview.removeAttribute('src');
                modalAdImagePreview.style.display = 'none';
            }
            document.getElementById('ad-modal-title').textContent = currentLanguage === 'en' ? 'Create Banner Ad' : 'បង្កើតផ្ទាំងផ្សព្វផ្សាយ';
            document.getElementById('ad-modal-save-label').textContent = currentLanguage === 'en' ? 'Create Banner' : 'បង្កើតផ្ទាំងផ្សាយ';
            adModal.classList.add('active');
        });
    }

    if (btnCloseAdModal) {
        btnCloseAdModal.addEventListener('click', () => {
            adModal.classList.remove('active');
        });
    }

    if (modalAdImageFile && modalAdImagePreview) {
        modalAdImageFile.addEventListener('change', () => {
            const file = modalAdImageFile.files && modalAdImageFile.files[0];
            if (!file) {
                modalAdImagePreview.removeAttribute('src');
                modalAdImagePreview.style.display = 'none';
                return;
            }
            modalAdImagePreview.src = URL.createObjectURL(file);
            modalAdImagePreview.style.display = 'block';
        });
    }

    async function uploadSelectedAdImage(editId) {
        const file = modalAdImageFile && modalAdImageFile.files ? modalAdImageFile.files[0] : null;
        if (!file) {
            const existingImageUrl = modalAdImageUrl ? modalAdImageUrl.value : '';
            if (editId && existingImageUrl) return existingImageUrl;
            throw new Error('missing_ad_image');
        }

        if (!file.type.startsWith('image/')) {
            throw new Error('invalid_ad_image_type');
        }

        if (file.size > 5 * 1024 * 1024) {
            throw new Error('ad_image_too_large');
        }

        const response = await fetch(`${API_BASE}/ads/upload-image`, {
            method: 'POST',
            headers: { 'Content-Type': file.type },
            body: file
        });
        if (!response.ok) {
            throw new Error('ad_image_upload_failed');
        }

        const data = await response.json();
        if (!data.image_url) {
            throw new Error('ad_image_upload_failed');
        }
        return data.image_url;
    }

    if (formModalDiscount) {
        formModalDiscount.addEventListener('submit', async (e) => {
            e.preventDefault();
            const dict = TRANSLATIONS[currentLanguage];
            const editId = document.getElementById('edit-discount-id').value;
            
            // Validate Percent
            const percentVal = parseInt(document.getElementById('modal-disc-percent').value);
            if (isNaN(percentVal) || percentVal < 0 || percentVal > 100) {
                showToast(currentLanguage === 'en' ? 'Discount percent must be between 0 and 100.' : 'ភាគរយបញ្ចុះតម្លៃត្រូវតែនៅចន្លោះពី 0 ដល់ 100។', true);
                return;
            }

            // Validate Expiry Date
            const expiryVal = document.getElementById('modal-disc-expiry').value;
            let expiresAt = null;
            if (expiryVal) {
                try {
                    expiresAt = new Date(expiryVal).toISOString();
                } catch (err) {
                    showToast(currentLanguage === 'en' ? 'Invalid expiry date format.' : 'ទម្រង់កាលបរិច្ឆេទផុតកំណត់មិនត្រឹមត្រូវ។', true);
                    return;
                }
            } else {
                showToast(currentLanguage === 'en' ? 'Expiry date is required.' : 'តម្រូវឱ្យមានកាលបរិច្ឆេទផុតកំណត់។', true);
                return;
            }

            const payload = {
                code: document.getElementById('modal-disc-code').value.trim(),
                title: document.getElementById('modal-disc-title').value.trim(),
                title_kh: document.getElementById('modal-disc-title-kh').value.trim(),
                discount_percent: percentVal,
                expires_at: expiresAt,
                description: document.getElementById('modal-disc-desc').value.trim() || null,
                description_kh: document.getElementById('modal-disc-desc-kh').value.trim() || null,
                is_active: document.getElementById('modal-disc-active').checked
            };

            try {
                const url = editId ? `${API_BASE}/discounts/${editId}` : `${API_BASE}/discounts`;
                const method = editId ? 'PUT' : 'POST';
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    const msg = editId 
                        ? (currentLanguage === 'en' ? 'Discount ticket updated successfully.' : 'ប័ណ្ណបញ្ចុះតម្លៃត្រូវបានកែប្រែដោយជោគជ័យ។')
                        : (currentLanguage === 'en' ? 'Discount ticket created successfully.' : 'ប័ណ្ណបញ្ចុះតម្លៃត្រូវបានបង្កើតដោយជោគជ័យ។');
                    showToast(msg);
                    formModalDiscount.reset();
                    discountModal.classList.remove('active');
                    loadDiscountsData();
                } else {
                    showToast(dict.toast_network_error, true);
                }
            } catch (error) {
                console.error('Error saving discount:', error);
                showToast(dict.toast_network_error, true);
            }
        });
    }

    if (formModalAd) {
        formModalAd.addEventListener('submit', async (e) => {
            e.preventDefault();
            const dict = TRANSLATIONS[currentLanguage];
            const editId = document.getElementById('edit-ad-id').value;

            try {
                const imageUrl = await uploadSelectedAdImage(editId);
                const payload = {
                    title: document.getElementById('modal-ad-title').value.trim(),
                    title_kh: document.getElementById('modal-ad-title-kh').value.trim(),
                    image_url: imageUrl,
                    link_url: document.getElementById('modal-ad-link').value.trim() || null,
                    description: document.getElementById('modal-ad-desc').value.trim() || null,
                    description_kh: document.getElementById('modal-ad-desc-kh').value.trim() || null,
                    is_active: document.getElementById('modal-ad-active').checked
                };
                const url = editId ? `${API_BASE}/ads/${editId}` : `${API_BASE}/ads`;
                const method = editId ? 'PUT' : 'POST';
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    const msg = editId 
                        ? (currentLanguage === 'en' ? 'Ad banner updated successfully.' : 'ផ្ទាំងផ្សព្វផ្សាយស្លាយត្រូវបានកែប្រែដោយជោគជ័យ។')
                        : (currentLanguage === 'en' ? 'Ad banner created successfully.' : 'ផ្ទាំងផ្សព្វផ្សាយស្លាយត្រូវបានបង្កើតដោយជោគជ័យ។');
                    showToast(msg);
                    formModalAd.reset();
                    adModal.classList.remove('active');
                    loadAdsData();
                } else {
                    showToast(dict.toast_network_error, true);
                }
            } catch (error) {
                console.error('Error saving ad banner:', error);
                if (error.message === 'missing_ad_image') {
                    showToast(currentLanguage === 'en' ? 'Please choose a banner photo from this device.' : 'សូមជ្រើសរើសរូបថតផ្ទាំងផ្សព្វផ្សាយពីឧបករណ៍នេះ។', true);
                } else if (error.message === 'ad_image_too_large') {
                    showToast(currentLanguage === 'en' ? 'Banner photo must be 5 MB or smaller.' : 'រូបថតផ្ទាំងផ្សព្វផ្សាយត្រូវតែមានទំហំ 5 MB ឬតូចជាងនេះ។', true);
                } else if (error.message === 'invalid_ad_image_type') {
                    showToast(currentLanguage === 'en' ? 'Banner photo must be an image file.' : 'រូបថតផ្ទាំងផ្សព្វផ្សាយត្រូវតែជាឯកសាររូបភាព។', true);
                } else {
                    showToast(dict.toast_network_error, true);
                }
            }
        });
    }

    async function loadDiscountsData() {
        if (!discountsTableBody) return;
        try {
            const discResp = await fetch(`${API_BASE}/discounts`);
            const discounts = await discResp.json();
            discountsTableBody.innerHTML = '';
            
            if (!Array.isArray(discounts)) {
                discountsTableBody.innerHTML = `<tr><td colspan="6" class="text-center" style="padding:2rem; color:var(--color-danger);">Failed to load discount tickets.</td></tr>`;
            } else if (discounts.length === 0) {
                discountsTableBody.innerHTML = `<tr><td colspan="6" class="text-center" style="padding:2rem;">No discount tickets found.</td></tr>`;
            } else {
                discounts.forEach(d => {
                    const tr = document.createElement('tr');
                    const expDate = new Date(d.expires_at).toLocaleDateString(currentLanguage === 'en' ? 'en-US' : 'km-KH');
                    const titleText = currentLanguage === 'km' ? d.title_kh : d.title;
                    const descText = currentLanguage === 'km' ? (d.description_kh || '') : (d.description || '');
                    
                    const statusText = d.is_active 
                        ? (currentLanguage === 'en' ? 'Active' : 'សកម្ម') 
                        : (currentLanguage === 'en' ? 'Inactive' : 'មិនសកម្ម');
                    const statusClass = d.is_active ? 'status-active' : 'status-cancelled';

                    tr.innerHTML = `
                        <td style="font-family:var(--font-display); font-weight:800; color:var(--color-primary);">${d.code}</td>
                        <td>
                            <div>${titleText}</div>
                            <small style="color:var(--color-on-surface-variant); font-size:0.65rem;">${descText}</small>
                        </td>
                        <td style="font-weight:700; color:var(--color-success);">${d.discount_percent}%</td>
                        <td>
                            <span class="ticket-status-badge ${statusClass}">${statusText}</span>
                        </td>
                        <td>${expDate}</td>
                        <td class="text-right" style="white-space: nowrap;">
                            <button class="btn btn-chip" onclick="openEditDiscountModal('${d.id}')" style="margin-right: 4px;">
                                <i class="fa-solid fa-pen-to-square"></i>
                            </button>
                            <button class="btn btn-chip danger" onclick="deleteDiscountTicket('${d.id}')">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </td>
                    `;
                    discountsTableBody.appendChild(tr);
                });
            }
        } catch (error) {
            console.error('Error loading discounts data:', error);
        }
    }

    async function loadAdsData() {
        if (!adsTableBody) return;
        try {
            const adsResp = await fetch(`${API_BASE}/ads`);
            const ads = await adsResp.json();
            adsTableBody.innerHTML = '';
            
            if (!Array.isArray(ads)) {
                adsTableBody.innerHTML = `<tr><td colspan="5" class="text-center" style="padding:2rem; color:var(--color-danger);">Failed to load banner ads.</td></tr>`;
            } else if (ads.length === 0) {
                adsTableBody.innerHTML = `<tr><td colspan="5" class="text-center" style="padding:2rem;">No banner ads found.</td></tr>`;
            } else {
                ads.forEach(ad => {
                    const tr = document.createElement('tr');
                    const titleText = currentLanguage === 'km' ? ad.title_kh : ad.title;
                    const descText = currentLanguage === 'km' ? (ad.description_kh || '') : (ad.description || '');
                    
                    const statusText = ad.is_active 
                        ? (currentLanguage === 'en' ? 'Active' : 'សកម្ម') 
                        : (currentLanguage === 'en' ? 'Inactive' : 'មិនសកម្ម');
                    const statusClass = ad.is_active ? 'status-active' : 'status-cancelled';

                    tr.innerHTML = `
                        <td>
                            <img src="${ad.image_url}" style="width:75px; height:42px; object-fit:cover; border-radius:var(--radius-md);" onerror="this.src='https://placehold.co/75x42?text=Banner'">
                        </td>
                        <td>
                            <div style="font-weight:700;">${titleText}</div>
                            <small style="color:var(--color-on-surface-variant); font-size:0.65rem;">${descText}</small>
                        </td>
                        <td style="font-family:monospace; font-size:0.7rem;">${ad.link_url || '—'}</td>
                        <td>
                            <span class="ticket-status-badge ${statusClass}">${statusText}</span>
                        </td>
                        <td class="text-right" style="white-space: nowrap;">
                            <button class="btn btn-chip" onclick="openEditAdModal('${ad.id}')" style="margin-right: 4px;">
                                <i class="fa-solid fa-pen-to-square"></i>
                            </button>
                            <button class="btn btn-chip danger" onclick="deleteAdSlide('${ad.id}')">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </td>
                    `;
                    adsTableBody.appendChild(tr);
                });
            }
        } catch (error) {
            console.error('Error loading ads data:', error);
        }
    }

    async function loadPromotionsData() {
        await loadDiscountsData();
        await loadAdsData();
    }

    window.openEditDiscountModal = async (discountId) => {
        try {
            const response = await fetch(`${API_BASE}/discounts`);
            const discounts = await response.json();
            if (!Array.isArray(discounts)) return;
            const discount = discounts.find(d => d.id === discountId);
            if (!discount) return;

            document.getElementById('edit-discount-id').value = discount.id;
            document.getElementById('modal-disc-code').value = discount.code;
            document.getElementById('modal-disc-title').value = discount.title;
            document.getElementById('modal-disc-title-kh').value = discount.title_kh;
            document.getElementById('modal-disc-percent').value = discount.discount_percent;
            
            const expiryDate = discount.expires_at.split('T')[0];
            document.getElementById('modal-disc-expiry').value = expiryDate;
            document.getElementById('modal-disc-desc').value = discount.description || '';
            document.getElementById('modal-disc-desc-kh').value = discount.description_kh || '';
            document.getElementById('modal-disc-active').checked = discount.is_active;

            document.getElementById('discount-modal-title').textContent = currentLanguage === 'en' ? 'Edit Discount Ticket' : 'កែសម្រួលប័ណ្ណបញ្ចុះតម្លៃ';
            document.getElementById('discount-modal-save-label').textContent = currentLanguage === 'en' ? 'Save Changes' : 'រក្សាទុកការផ្លាស់ប្តូរ';
            
            discountModal.classList.add('active');
        } catch (error) {
            console.error('Error opening edit discount modal:', error);
        }
    };

    window.openEditAdModal = async (adId) => {
        try {
            const response = await fetch(`${API_BASE}/ads`);
            const ads = await response.json();
            if (!Array.isArray(ads)) return;
            const ad = ads.find(a => a.id === adId);
            if (!ad) return;

            document.getElementById('edit-ad-id').value = ad.id;
            document.getElementById('modal-ad-title').value = ad.title;
            document.getElementById('modal-ad-title-kh').value = ad.title_kh;
            modalAdImageUrl.value = ad.image_url;
            if (modalAdImageFile) modalAdImageFile.value = '';
            if (modalAdImagePreview) {
                modalAdImagePreview.src = ad.image_url;
                modalAdImagePreview.style.display = 'block';
            }
            document.getElementById('modal-ad-link').value = ad.link_url || '';
            document.getElementById('modal-ad-desc').value = ad.description || '';
            document.getElementById('modal-ad-desc-kh').value = ad.description_kh || '';
            document.getElementById('modal-ad-active').checked = ad.is_active;

            document.getElementById('ad-modal-title').textContent = currentLanguage === 'en' ? 'Edit Banner Ad' : 'កែសម្រួលផ្ទាំងផ្សព្វផ្សាយ';
            document.getElementById('ad-modal-save-label').textContent = currentLanguage === 'en' ? 'Save Changes' : 'រក្សាទុកការផ្លាស់ប្តូរ';

            adModal.classList.add('active');
        } catch (error) {
            console.error('Error opening edit ad modal:', error);
        }
    };

    window.deleteDiscountTicket = async (ticketId) => {
        if (!confirm(currentLanguage === 'en' ? 'Delete this discount ticket?' : 'តើអ្នកចង់លុបប័ណ្ណបញ្ចុះតម្លៃនេះមែនទេ?')) return;
        try {
            const response = await fetch(`${API_BASE}/discounts/${ticketId}`, { method: 'DELETE' });
            if (response.ok) {
                showToast(currentLanguage === 'en' ? 'Discount ticket deleted.' : 'បានលុបប័ណ្ណបញ្ចុះតម្លៃ។');
                loadDiscountsData();
            }
        } catch (error) {
            console.error('Error deleting discount:', error);
        }
    };

    window.deleteAdSlide = async (adId) => {
        if (!confirm(currentLanguage === 'en' ? 'Delete this banner ad?' : 'តើអ្នកចង់លុបការផ្សព្វផ្សាយនេះមែនទេ?')) return;
        try {
            const response = await fetch(`${API_BASE}/ads/${adId}`, { method: 'DELETE' });
            if (response.ok) {
                showToast(currentLanguage === 'en' ? 'Ad deleted.' : 'បានលុបការផ្សព្វផ្សាយ។');
                loadAdsData();
            }
        } catch (error) {
            console.error('Error deleting ad:', error);
        }
    };

    // System Messages Management
    async function loadAdminMessages() {
        try {
            const response = await fetch(`${API_BASE}/messages`);
            if (!response.ok) return;
            const messages = await response.json();
            const tableBody = document.getElementById('messages-table-body');
            if (!tableBody) return;
            tableBody.innerHTML = '';

            if (!messages || messages.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align: center; padding: 2rem; color: var(--color-text-secondary);">
                            No system messages yet. Broadcast a new message using the form.
                        </td>
                    </tr>
                `;
                return;
            }

            messages.forEach(msg => {
                const tr = document.createElement('tr');
                const targetBadge = msg.target_role === 'driver' 
                    ? '<span class="ticket-status-badge" style="background:#e0f2fe; color:#0369a1;">Drivers Only</span>'
                    : msg.target_role === 'passenger'
                    ? '<span class="ticket-status-badge" style="background:#fef3c7; color:#b45309;">Passengers Only</span>'
                    : '<span class="ticket-status-badge" style="background:#f3e8ff; color:#6b21a8;">All Users</span>';

                const typeColor = msg.message_type === 'warning' ? '#dc2626'
                    : msg.message_type === 'announcement' ? '#2563eb'
                    : msg.message_type === 'maintenance' ? '#d97706'
                    : '#059669';

                const statusClass = msg.is_active ? 'active' : 'inactive';
                const statusText = msg.is_active ? 'Active' : 'Inactive';
                const pinnedTag = msg.is_pinned ? ' <span style="font-size:10px; background:#fef3c7; color:#d97706; padding:2px 6px; border-radius:4px; font-weight:700;"><i class="fa-solid fa-thumbtack"></i> PINNED</span>' : '';

                const createdDate = new Date(msg.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });

                tr.innerHTML = `
                    <td>
                        <div style="font-weight: 700; color: var(--color-primary);">${escapeHtml(msg.title)}${pinnedTag}</div>
                        <div style="font-size: 0.8rem; color: var(--color-text-secondary); max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(msg.body)}</div>
                        <div style="font-size: 0.75rem; color: #9ca3af; margin-top: 2px;">Sent: ${createdDate}</div>
                    </td>
                    <td>${targetBadge}</td>
                    <td><span style="font-weight: 700; font-size: 0.8rem; color: ${typeColor}; text-transform: uppercase;">${msg.message_type}</span></td>
                    <td><span class="ticket-status-badge ${statusClass}">${statusText}</span></td>
                    <td class="text-right" style="white-space: nowrap;">
                        <button class="btn btn-chip" onclick="toggleAdminMessageActive('${msg.id}')" style="margin-right: 4px;" title="Toggle Active">
                            <i class="fa-solid ${msg.is_active ? 'fa-eye-slash' : 'fa-eye'}"></i>
                        </button>
                        <button class="btn btn-chip danger" onclick="deleteAdminMessage('${msg.id}')" title="Delete Message">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </td>
                `;
                tableBody.appendChild(tr);
            });
        } catch (error) {
            console.error('Error loading admin system messages:', error);
        }
    }

    // Handle Form Submit for Creating System Message
    const formCreateMessage = document.getElementById('form-create-message');
    if (formCreateMessage) {
        formCreateMessage.addEventListener('submit', async (e) => {
            e.preventDefault();
            const title = document.getElementById('msg-title').value.trim();
            const body = document.getElementById('msg-body').value.trim();
            const target_role = document.getElementById('msg-target').value;
            const message_type = document.getElementById('msg-type').value;
            const is_pinned = document.getElementById('msg-pinned').checked;
            const broadcast_to_notifications = document.getElementById('msg-broadcast').checked;

            if (!title || !body) return;

            try {
                const response = await fetch(`${API_BASE}/messages`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title,
                        body,
                        target_role,
                        message_type,
                        is_active: true,
                        is_pinned,
                        broadcast_to_notifications
                    })
                });

                if (response.ok) {
                    showToast(currentLanguage === 'en' ? 'System message broadcasted successfully.' : 'បានផ្ញើសារប្រព័ន្ធដោយជោគជ័យ។');
                    formCreateMessage.reset();
                    document.getElementById('msg-broadcast').checked = true;
                    loadAdminMessages();
                } else {
                    const err = await response.json();
                    alert(err.detail || 'Could not broadcast message.');
                }
            } catch (error) {
                console.error('Error creating system message:', error);
            }
        });
    }

    const btnRefreshMessages = document.getElementById('btn-refresh-messages');
    if (btnRefreshMessages) {
        btnRefreshMessages.addEventListener('click', loadAdminMessages);
    }

    window.toggleAdminMessageActive = async (msgId) => {
        try {
            const response = await fetch(`${API_BASE}/messages/${msgId}/toggle-active`, { method: 'POST' });
            if (response.ok) {
                showToast(currentLanguage === 'en' ? 'Message status updated.' : 'បានបច្ចុប្បន្នភាពស្ថានភាពសារ។');
                loadAdminMessages();
            }
        } catch (error) {
            console.error('Error toggling message status:', error);
        }
    };

    window.deleteAdminMessage = async (msgId) => {
        if (!confirm(currentLanguage === 'en' ? 'Delete this system message?' : 'តើអ្នកពិតជាចង់លុបសារប្រព័ន្ធនេះមែនទេ?')) return;
        try {
            const response = await fetch(`${API_BASE}/messages/${msgId}`, { method: 'DELETE' });
            if (response.ok) {
                showToast(currentLanguage === 'en' ? 'System message deleted.' : 'បានលុបសារប្រព័ន្ធ។');
                loadAdminMessages();
            }
        } catch (error) {
            console.error('Error deleting system message:', error);
        }
    };

    // Admin Auth State & Token Manager
    const adminLoginScreen = document.getElementById('admin-login-screen');
    const adminLoginForm = document.getElementById('admin-login-form');
    const adminLoginError = document.getElementById('admin-login-error');
    const adminLoginErrorMsg = document.getElementById('admin-login-error-msg');
    const btnAdminLogin = document.getElementById('btn-admin-login');
    const btnAdminLogout = document.getElementById('btn-admin-logout');
    const btnTogglePass = document.getElementById('btn-toggle-pass');
    const adminPassInput = document.getElementById('admin-pass-input');
    const adminUserInput = document.getElementById('admin-user-input');
    const adminCapsWarning = document.getElementById('admin-caps-warning');

    function checkAdminAuth() {
        const token = localStorage.getItem('admin_token');
        if (!token) {
            if (adminLoginScreen) adminLoginScreen.style.display = 'flex';
            if (adminUserInput) setTimeout(() => adminUserInput.focus(), 150);
            return false;
        }
        if (adminLoginScreen) adminLoginScreen.style.display = 'none';
        return true;
    }

    function getAuthHeaders() {
        const token = localStorage.getItem('admin_token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
    }

    // Password visibility toggle handler
    if (btnTogglePass && adminPassInput) {
        btnTogglePass.addEventListener('click', () => {
            const isPassword = adminPassInput.getAttribute('type') === 'password';
            adminPassInput.setAttribute('type', isPassword ? 'text' : 'password');
            const icon = document.getElementById('pass-visibility-icon');
            if (icon) {
                icon.className = isPassword ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye';
            }
        });
    }

    // Caps Lock indicator
    if (adminPassInput && adminCapsWarning) {
        ['keyup', 'keydown'].forEach(evt => {
            adminPassInput.addEventListener(evt, (e) => {
                if (e.getModifierState && e.getModifierState('CapsLock')) {
                    adminCapsWarning.style.display = 'flex';
                } else {
                    adminCapsWarning.style.display = 'none';
                }
            });
        });
        adminPassInput.addEventListener('blur', () => {
            adminCapsWarning.style.display = 'none';
        });
    }

    function showAdminLoginError(message) {
        if (adminLoginErrorMsg) {
            adminLoginErrorMsg.textContent = message;
        } else if (adminLoginError) {
            adminLoginError.textContent = message;
        }
        if (adminLoginError) {
            adminLoginError.style.display = 'flex';
            // Re-trigger shake animation
            adminLoginError.style.animation = 'none';
            adminLoginError.offsetHeight; /* trigger reflow */
            adminLoginError.style.animation = 'shakeLoginError 0.45s ease-in-out';
        }
    }

    if (adminLoginForm) {
        adminLoginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const phone_or_username = adminUserInput ? adminUserInput.value.trim() : '';
            const password = adminPassInput ? adminPassInput.value : '';
            if (adminLoginError) adminLoginError.style.display = 'none';

            if (!phone_or_username || !password) {
                showAdminLoginError('Please enter both identifier and password.');
                return;
            }

            // Set Loading UI
            const btnContent = btnAdminLogin ? btnAdminLogin.querySelector('.btn-login-content') : null;
            const btnSpinner = btnAdminLogin ? btnAdminLogin.querySelector('.btn-login-spinner') : null;
            if (btnAdminLogin) btnAdminLogin.disabled = true;
            if (btnContent) btnContent.style.display = 'none';
            if (btnSpinner) btnSpinner.style.display = 'inline-flex';

            try {
                const response = await fetch(`${API_BASE}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone_or_username, password })
                });

                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('admin_token', data.access_token);
                    if (adminLoginScreen) adminLoginScreen.style.display = 'none';
                    loadSummary().then(() => {
                        loadDrivers();
                        loadPassengers();
                    });
                } else {
                    const err = await response.json();
                    showAdminLoginError(err.detail || 'Invalid administrator credentials.');
                }
            } catch (error) {
                console.error('Admin login error:', error);
                showAdminLoginError('Could not connect to authentication server.');
            } finally {
                if (btnAdminLogin) btnAdminLogin.disabled = false;
                if (btnContent) btnContent.style.display = 'inline-flex';
                if (btnSpinner) btnSpinner.style.display = 'none';
            }
        });
    }

    if (btnAdminLogout) {
        btnAdminLogout.addEventListener('click', () => {
            localStorage.removeItem('admin_token');
            if (adminLoginScreen) {
                adminLoginScreen.style.display = 'flex';
                if (adminUserInput) setTimeout(() => adminUserInput.focus(), 150);
            }
        });
    }

    // --- Vehicle Models Management ---
    let currentVehicleModels = [];
    let vmCurrentPage = 1;
    let vmPageSize = 50;
    let vmSortColumn = 'sort_order';
    let vmSortDirection = 'asc';

    const searchVehicleModelsInput = document.getElementById('search-vehicle-models');
    const filterVmBrandSelect = document.getElementById('filter-vm-brand');
    const filterVmTypeSelect = document.getElementById('filter-vm-type');
    const filterVmStatusSelect = document.getElementById('filter-vm-status');
    const sortVmSelect = document.getElementById('sort-vm-select');
    const btnClearVmFilters = document.getElementById('btn-clear-vm-filters');
    const vmCountText = document.getElementById('vm-count-text');
    const vmPaginationInfo = document.getElementById('vm-pagination-info');
    const vmPaginationControls = document.getElementById('vm-pagination-controls');
    const vmPageSizeSelect = document.getElementById('vm-page-size-select');
    const btnAddVehicleModel = document.getElementById('btn-add-vehicle-model');
    const btnCloseVehicleModelModal = document.getElementById('btn-close-vehicle-model-modal');
    const vehicleModelModal = document.getElementById('vehicle-model-modal');
    const formModalVehicleModel = document.getElementById('form-modal-vehicle-model');
    const vehicleModelsTableBody = document.getElementById('vehicle-models-table-body');
    const sortableHeaders = document.querySelectorAll('#tab-vehicle-models .sortable-th');

    // Populate Brand Filter Dropdown with model counts
    function populateBrandFilterOptions() {
        if (!filterVmBrandSelect) return;
        const previousVal = filterVmBrandSelect.value;
        const brandCounts = {};
        currentVehicleModels.forEach(m => {
            if (m.brand) {
                brandCounts[m.brand] = (brandCounts[m.brand] || 0) + 1;
            }
        });

        const sortedBrands = Object.keys(brandCounts).sort((a, b) => a.localeCompare(b));
        filterVmBrandSelect.innerHTML = `<option value="">All Brands (${currentVehicleModels.length})</option>`;
        sortedBrands.forEach(brand => {
            const opt = document.createElement('option');
            opt.value = brand;
            opt.textContent = `${brand} (${brandCounts[brand]})`;
            filterVmBrandSelect.appendChild(opt);
        });

        if (previousVal && sortedBrands.includes(previousVal)) {
            filterVmBrandSelect.value = previousVal;
        }
    }

    // Update Header Sort Icons and Active Classes
    function updateHeaderSortIcons() {
        sortableHeaders.forEach(th => {
            const col = th.getAttribute('data-sort-col');
            const icon = th.querySelector('.sort-icon');
            if (col === vmSortColumn) {
                th.classList.add('sort-active');
                if (icon) {
                    icon.className = vmSortDirection === 'asc' ? 'fa-solid fa-sort-up sort-icon' : 'fa-solid fa-sort-down sort-icon';
                }
            } else {
                th.classList.remove('sort-active');
                if (icon) {
                    icon.className = 'fa-solid fa-sort sort-icon';
                }
            }
        });

        // Sync quick sort dropdown if applicable
        if (sortVmSelect) {
            const pair = `${vmSortColumn}-${vmSortDirection}`;
            const matchingOpt = Array.from(sortVmSelect.options).find(o => {
                if (vmSortColumn === 'sort_order' && o.value === 'priority-asc') return true;
                if (vmSortColumn === 'model_name' && o.value === `model-${vmSortDirection}`) return true;
                if (vmSortColumn === 'brand' && o.value === `brand-${vmSortDirection}`) return true;
                if (vmSortColumn === 'seat_count' && o.value === `seats-${vmSortDirection}`) return true;
                if (vmSortColumn === 'vehicle_type' && o.value === `type-${vmSortDirection}`) return true;
                if (vmSortColumn === 'is_active' && o.value === `status-${vmSortDirection}`) return true;
                return false;
            });
            if (matchingOpt) {
                sortVmSelect.value = matchingOpt.value;
            }
        }
    }

    // Set Sort Column & Direction
    function setVehicleModelSort(column, direction = null) {
        if (vmSortColumn === column) {
            vmSortDirection = direction !== null ? direction : (vmSortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            vmSortColumn = column;
            vmSortDirection = direction !== null ? direction : (column === 'seat_count' ? 'desc' : 'asc');
        }
        vmCurrentPage = 1;
        updateHeaderSortIcons();
        renderVehicleModelsTable();
    }

    // Sortable Header Click Listeners
    sortableHeaders.forEach(th => {
        th.addEventListener('click', () => {
            const col = th.getAttribute('data-sort-col');
            if (col) {
                setVehicleModelSort(col);
            }
        });
    });

    // Quick Sort Select Listener
    if (sortVmSelect) {
        sortVmSelect.addEventListener('change', () => {
            const val = sortVmSelect.value;
            switch (val) {
                case 'priority-asc': setVehicleModelSort('sort_order', 'asc'); break;
                case 'model-asc': setVehicleModelSort('model_name', 'asc'); break;
                case 'model-desc': setVehicleModelSort('model_name', 'desc'); break;
                case 'brand-asc': setVehicleModelSort('brand', 'asc'); break;
                case 'brand-desc': setVehicleModelSort('brand', 'desc'); break;
                case 'display-asc': setVehicleModelSort('display_name', 'asc'); break;
                case 'display-desc': setVehicleModelSort('display_name', 'desc'); break;
                case 'seats-desc': setVehicleModelSort('seat_count', 'desc'); break;
                case 'seats-asc': setVehicleModelSort('seat_count', 'asc'); break;
                case 'type-asc': setVehicleModelSort('vehicle_type', 'asc'); break;
                case 'status-desc': setVehicleModelSort('is_active', 'desc'); break;
                default: setVehicleModelSort('sort_order', 'asc');
            }
        });
    }

    // Search and Filter Listeners
    if (searchVehicleModelsInput) {
        searchVehicleModelsInput.addEventListener('input', () => {
            vmCurrentPage = 1;
            renderVehicleModelsTable();
        });
    }

    if (filterVmBrandSelect) {
        filterVmBrandSelect.addEventListener('change', () => {
            vmCurrentPage = 1;
            renderVehicleModelsTable();
        });
    }

    if (filterVmTypeSelect) {
        filterVmTypeSelect.addEventListener('change', () => {
            vmCurrentPage = 1;
            renderVehicleModelsTable();
        });
    }

    if (filterVmStatusSelect) {
        filterVmStatusSelect.addEventListener('change', () => {
            vmCurrentPage = 1;
            renderVehicleModelsTable();
        });
    }

    if (btnClearVmFilters) {
        btnClearVmFilters.addEventListener('click', () => {
            if (searchVehicleModelsInput) searchVehicleModelsInput.value = '';
            if (filterVmBrandSelect) filterVmBrandSelect.value = '';
            if (filterVmTypeSelect) filterVmTypeSelect.value = '';
            if (filterVmStatusSelect) filterVmStatusSelect.value = '';
            setVehicleModelSort('sort_order', 'asc');
        });
    }

    if (vmPageSizeSelect) {
        vmPageSizeSelect.addEventListener('change', () => {
            vmPageSize = parseInt(vmPageSizeSelect.value) || 50;
            vmCurrentPage = 1;
            renderVehicleModelsTable();
        });
    }

    if (btnAddVehicleModel) {
        btnAddVehicleModel.addEventListener('click', () => {
            document.getElementById('vehicle-model-modal-title').textContent = 'Add Vehicle Model';
            document.getElementById('edit-vehicle-model-id').value = '';
            document.getElementById('modal-vm-brand').value = '';
            document.getElementById('modal-vm-model-name').value = '';
            document.getElementById('modal-vm-display-name').value = '';
            document.getElementById('modal-vm-vehicle-type').value = '';
            document.getElementById('modal-vm-seat-count').value = '';
            document.getElementById('modal-vm-sort-order').value = (currentVehicleModels.length + 1).toString();
            document.getElementById('modal-vm-active').checked = true;
            document.getElementById('vehicle-model-modal-save-label').textContent = 'Save Model';
            vehicleModelModal.classList.add('active');
        });
    }

    if (btnCloseVehicleModelModal) {
        btnCloseVehicleModelModal.addEventListener('click', () => {
            vehicleModelModal.classList.remove('active');
        });
    }

    async function loadVehicleModels() {
        try {
            let res = await fetch(`${API_BASE}/vehicle-models`, { headers: getAuthHeaders() });
            if (!res.ok) {
                res = await fetch(`${API_V1_BASE}/travel/vehicle-models`);
            }
            if (!res.ok) throw new Error('Failed to fetch vehicle models');
            currentVehicleModels = await res.json();
            populateBrandFilterOptions();
            updateHeaderSortIcons();
            renderVehicleModelsTable();
        } catch (err) {
            console.error('Error loading vehicle models:', err);
        }
    }

    function renderVehicleModelsTable() {
        if (!vehicleModelsTableBody) return;
        vehicleModelsTableBody.innerHTML = '';

        const searchQuery = searchVehicleModelsInput ? searchVehicleModelsInput.value.trim().toLowerCase() : '';
        const brandFilter = filterVmBrandSelect ? filterVmBrandSelect.value.trim().toLowerCase() : '';
        const typeFilter = filterVmTypeSelect ? filterVmTypeSelect.value.trim().toLowerCase() : '';
        const statusFilter = filterVmStatusSelect ? filterVmStatusSelect.value : '';

        // 1. Filter
        let list = currentVehicleModels.filter(m => {
            if (searchQuery) {
                const b = (m.brand || '').toLowerCase();
                const mn = (m.model_name || '').toLowerCase();
                const dn = (m.display_name || '').toLowerCase();
                const vt = (m.vehicle_type || '').toLowerCase();
                if (!b.includes(searchQuery) && !mn.includes(searchQuery) && !dn.includes(searchQuery) && !vt.includes(searchQuery)) {
                    return false;
                }
            }

            if (brandFilter) {
                if ((m.brand || '').toLowerCase() !== brandFilter) return false;
            }

            if (typeFilter) {
                const vt = (m.vehicle_type || '').toLowerCase();
                if (!vt.includes(typeFilter)) return false;
            }

            if (statusFilter === 'active' && !m.is_active) return false;
            if (statusFilter === 'inactive' && m.is_active) return false;

            return true;
        });

        // 2. Sort
        list.sort((a, b) => {
            let valA, valB;
            switch (vmSortColumn) {
                case 'model_name':
                    valA = (a.model_name || '').toLowerCase();
                    valB = (b.model_name || '').toLowerCase();
                    break;
                case 'brand':
                    valA = (a.brand || '').toLowerCase();
                    valB = (b.brand || '').toLowerCase();
                    break;
                case 'display_name':
                    valA = (a.display_name || '').toLowerCase();
                    valB = (b.display_name || '').toLowerCase();
                    break;
                case 'vehicle_type':
                    valA = (a.vehicle_type || '').toLowerCase();
                    valB = (b.vehicle_type || '').toLowerCase();
                    break;
                case 'seat_count':
                    valA = a.seat_count !== null ? a.seat_count : 0;
                    valB = b.seat_count !== null ? b.seat_count : 0;
                    break;
                case 'is_active':
                    valA = a.is_active ? 1 : 0;
                    valB = b.is_active ? 1 : 0;
                    break;
                case 'sort_order':
                default:
                    valA = a.sort_order !== null ? a.sort_order : 99999;
                    valB = b.sort_order !== null ? b.sort_order : 99999;
                    break;
            }

            let cmp = 0;
            if (typeof valA === 'string') {
                cmp = valA.localeCompare(valB);
            } else {
                cmp = valA < valB ? -1 : (valA > valB ? 1 : 0);
            }

            if (cmp !== 0) {
                return vmSortDirection === 'asc' ? cmp : -cmp;
            }

            // Secondary tie-breaker by brand then model_name
            const bCmp = (a.brand || '').localeCompare(b.brand || '');
            if (bCmp !== 0) return bCmp;
            return (a.model_name || '').localeCompare(b.model_name || '');
        });

        // Update Count Badges
        if (vmCountText) {
            if (brandFilter) {
                vmCountText.textContent = `${list.length} ${filterVmBrandSelect.value} Models`;
            } else {
                vmCountText.textContent = `${list.length} Models`;
            }
        }

        // 3. Paginate
        const totalItems = list.length;
        const totalPages = Math.ceil(totalItems / vmPageSize) || 1;
        if (vmCurrentPage > totalPages) vmCurrentPage = totalPages;
        if (vmCurrentPage < 1) vmCurrentPage = 1;

        const startIdx = (vmCurrentPage - 1) * vmPageSize;
        const endIdx = Math.min(startIdx + vmPageSize, totalItems);
        const paginatedList = list.slice(startIdx, endIdx);

        // Update Pagination Info & Controls
        if (vmPaginationInfo) {
            if (totalItems === 0) {
                vmPaginationInfo.textContent = 'Showing 0 of 0 models';
            } else {
                const filterNote = totalItems < currentVehicleModels.length ? ` (filtered from ${currentVehicleModels.length} total)` : '';
                vmPaginationInfo.textContent = `Showing ${startIdx + 1}–${endIdx} of ${totalItems} models${filterNote}`;
            }
        }

        renderVehicleModelPaginationControls(totalPages);

        if (totalItems === 0) {
            vehicleModelsTableBody.innerHTML = `<tr><td colspan="8" class="text-center text-muted" style="padding: 3rem;">No vehicle models found matching filter criteria.</td></tr>`;
            return;
        }

        paginatedList.forEach(m => {
            const tr = document.createElement('tr');
            const statusBadge = m.is_active
                ? `<span class="badge badge-success" style="cursor:pointer;" onclick="window.toggleVehicleModelActive('${m.id}')" title="Click to Deactivate"><i class="fa-solid fa-check"></i> Active</span>`
                : `<span class="badge badge-secondary" style="cursor:pointer;" onclick="window.toggleVehicleModelActive('${m.id}')" title="Click to Activate"><i class="fa-solid fa-ban"></i> Inactive</span>`;

            tr.innerHTML = `
                <td><strong>${escapeHtml(m.brand)}</strong></td>
                <td><span style="font-weight: 600; color: var(--color-primary);">${escapeHtml(m.model_name)}</span></td>
                <td><span>${escapeHtml(m.display_name)}</span></td>
                <td>${m.vehicle_type ? `<span class="badge badge-outline" style="font-size:0.75rem; border-color: var(--color-outline-variant);">${escapeHtml(m.vehicle_type)}</span>` : '<span class="text-muted">-</span>'}</td>
                <td>${m.seat_count ? `<span style="font-weight: 700;">${m.seat_count}</span> <span class="text-muted" style="font-size:0.75rem;">seats</span>` : '<span class="text-muted">-</span>'}</td>
                <td><span class="text-muted" style="font-size: 0.8rem;">#${m.sort_order || 0}</span></td>
                <td>${statusBadge}</td>
                <td class="text-right">
                    <button class="btn btn-secondary btn-sm" onclick="window.editVehicleModel('${m.id}')" title="Edit Model" style="padding: 0.3rem 0.6rem;">
                        <i class="fa-solid fa-pen-to-square"></i>
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="window.deleteVehicleModel('${m.id}')" title="Delete Model" style="padding: 0.3rem 0.6rem; margin-left: 4px;">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </td>
            `;
            vehicleModelsTableBody.appendChild(tr);
        });
    }

    function renderVehicleModelPaginationControls(totalPages) {
        if (!vmPaginationControls) return;
        vmPaginationControls.innerHTML = '';
        if (totalPages <= 1) return;

        // Prev Button
        const prevBtn = document.createElement('button');
        prevBtn.className = 'btn-page';
        prevBtn.innerHTML = '<i class="fa-solid fa-chevron-left"></i>';
        prevBtn.disabled = vmCurrentPage === 1;
        prevBtn.addEventListener('click', () => {
            if (vmCurrentPage > 1) {
                vmCurrentPage--;
                renderVehicleModelsTable();
            }
        });
        vmPaginationControls.appendChild(prevBtn);

        // Compute Page Numbers
        let pageNumbers = [];
        if (totalPages <= 7) {
            for (let i = 1; i <= totalPages; i++) pageNumbers.push(i);
        } else {
            pageNumbers.push(1);
            if (vmCurrentPage > 3) pageNumbers.push('...');
            const start = Math.max(2, vmCurrentPage - 1);
            const end = Math.min(totalPages - 1, vmCurrentPage + 1);
            for (let i = start; i <= end; i++) pageNumbers.push(i);
            if (vmCurrentPage < totalPages - 2) pageNumbers.push('...');
            pageNumbers.push(totalPages);
        }

        pageNumbers.forEach(p => {
            if (p === '...') {
                const ellipsis = document.createElement('span');
                ellipsis.style.padding = '0 6px';
                ellipsis.style.color = 'var(--color-on-surface-variant)';
                ellipsis.textContent = '…';
                vmPaginationControls.appendChild(ellipsis);
            } else {
                const btn = document.createElement('button');
                btn.className = `btn-page ${p === vmCurrentPage ? 'active' : ''}`;
                btn.textContent = p;
                btn.addEventListener('click', () => {
                    vmCurrentPage = p;
                    renderVehicleModelsTable();
                });
                vmPaginationControls.appendChild(btn);
            }
        });

        // Next Button
        const nextBtn = document.createElement('button');
        nextBtn.className = 'btn-page';
        nextBtn.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
        nextBtn.disabled = vmCurrentPage === totalPages;
        nextBtn.addEventListener('click', () => {
            if (vmCurrentPage < totalPages) {
                vmCurrentPage++;
                renderVehicleModelsTable();
            }
        });
        vmPaginationControls.appendChild(nextBtn);
    }

    if (formModalVehicleModel) {
        formModalVehicleModel.addEventListener('submit', async (e) => {
            e.preventDefault();
            const modelId = document.getElementById('edit-vehicle-model-id').value;
            const brand = document.getElementById('modal-vm-brand').value.trim();
            const modelName = document.getElementById('modal-vm-model-name').value.trim();
            const displayName = document.getElementById('modal-vm-display-name').value.trim();
            const vehicleType = document.getElementById('modal-vm-vehicle-type').value.trim();
            const seatCountVal = document.getElementById('modal-vm-seat-count').value;
            const sortOrderVal = document.getElementById('modal-vm-sort-order').value;
            const isActive = document.getElementById('modal-vm-active').checked;

            const payload = {
                brand: brand,
                model_name: modelName,
                display_name: displayName || null,
                vehicle_type: vehicleType || null,
                seat_count: seatCountVal ? parseInt(seatCountVal) : null,
                sort_order: sortOrderVal ? parseInt(sortOrderVal) : 0,
                is_active: isActive
            };

            try {
                const url = modelId ? `${API_BASE}/vehicle-models/${modelId}` : `${API_BASE}/vehicle-models`;
                const method = modelId ? 'PUT' : 'POST';
                const res = await fetch(url, {
                    method: method,
                    headers: getAuthHeaders(),
                    body: JSON.stringify(payload)
                });
                if (!res.ok) {
                    const errJson = await res.json();
                    throw new Error(errJson.detail || 'Failed to save vehicle model');
                }
                vehicleModelModal.classList.remove('active');
                await loadVehicleModels();
            } catch (err) {
                alert('Error saving vehicle model: ' + err.message);
            }
        });
    }

    window.editVehicleModel = function(id) {
        const item = currentVehicleModels.find(m => m.id === id);
        if (!item) return;
        document.getElementById('vehicle-model-modal-title').textContent = 'Edit Vehicle Model';
        document.getElementById('edit-vehicle-model-id').value = item.id;
        document.getElementById('modal-vm-brand').value = item.brand || '';
        document.getElementById('modal-vm-model-name').value = item.model_name || '';
        document.getElementById('modal-vm-display-name').value = item.display_name || '';
        document.getElementById('modal-vm-vehicle-type').value = item.vehicle_type || '';
        document.getElementById('modal-vm-seat-count').value = item.seat_count !== null ? item.seat_count : '';
        document.getElementById('modal-vm-sort-order').value = item.sort_order || 0;
        document.getElementById('modal-vm-active').checked = item.is_active;
        document.getElementById('vehicle-model-modal-save-label').textContent = 'Update Model';
        vehicleModelModal.classList.add('active');
    };

    window.toggleVehicleModelActive = async function(id) {
        try {
            const res = await fetch(`${API_BASE}/vehicle-models/${id}/toggle-active`, {
                method: 'POST',
                headers: getAuthHeaders()
            });
            if (!res.ok) throw new Error('Failed to toggle status');
            await loadVehicleModels();
        } catch (err) {
            alert('Error updating model status: ' + err.message);
        }
    };

    window.deleteVehicleModel = async function(id) {
        if (!confirm('Are you sure you want to delete this vehicle model?')) return;
        try {
            const res = await fetch(`${API_BASE}/vehicle-models/${id}`, {
                method: 'DELETE',
                headers: getAuthHeaders()
            });
            if (!res.ok) throw new Error('Failed to delete vehicle model');
            await loadVehicleModels();
        } catch (err) {
            alert('Error deleting model: ' + err.message);
        }
    };

    // Check Auth on Startup
    if (checkAdminAuth()) {
        loadSummary().then(() => {
            loadDrivers();
            loadPassengers();
            loadVehicleModels();
        });
    }
});

