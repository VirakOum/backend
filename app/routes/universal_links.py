import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db
from ..models import Trip, NewsArticle, SystemAd, Vehicle, UniversalLinkConfig, User

router = APIRouter(tags=["universal_links"])

AASA_DATA = {
    "applinks": {
        "apps": [],
        "details": [
            {
                "appID": "3VMD59LYS6.com.kh.mytravel.app",
                "paths": [
                    "/trips/*",
                    "/t/*",
                    "/news/*",
                    "/ads/*",
                    "/promotions/*",
                    "/travel/*",
                ],
            }
        ],
    },
    "webcredentials": {
        "apps": ["3VMD59LYS6.com.kh.mytravel.app"]
    },
}

ASSETLINKS_DATA = [
    {
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": "com.kh.mytravel.mytravel",
            "sha256_cert_fingerprints": [
                # Google Play App Signing (Production Play Store)
                "4B:33:E5:28:B3:A4:59:1A:D1:77:90:CD:9F:49:CB:47:EF:A9:9F:EF:D9:58:75:B7:29:3D:FE:87:E1:FE:47:73",
                # Local Release Keystore (Keystone.jks)
                "0C:B8:64:C9:26:44:67:E9:21:9F:A5:F4:D2:0B:66:40:2F:1C:F2:B1:FA:05:2F:BF:42:6F:EF:40:6F:9D:ED:47",
                # Local Debug Keystore
                "ED:F9:37:D3:54:59:0B:A8:73:D3:8E:DD:AE:E3:7E:1A:D6:C8:33:CD:25:74:18:08:70:77:F3:EA:B9:37:DC:F8",
            ],
        },
    }
]


def get_effective_aasa(db: Session | None = None) -> dict[str, Any]:
    if db is not None:
        try:
            cfg = db.execute(select(UniversalLinkConfig).where(UniversalLinkConfig.key == "default")).scalars().first()
            if cfg and cfg.is_active:
                app_id = f"{cfg.apple_team_id}.{cfg.apple_bundle_id}"
                data: dict[str, Any] = {
                    "applinks": {
                        "apps": [],
                        "details": [
                            {
                                "appID": app_id,
                                "paths": cfg.apple_paths or AASA_DATA["applinks"]["details"][0]["paths"],
                            }
                        ],
                    }
                }
                if cfg.webcredentials_enabled:
                    data["webcredentials"] = {"apps": [app_id]}
                return data
        except Exception:
            pass
    return AASA_DATA


def get_effective_assetlinks(db: Session | None = None) -> list[dict[str, Any]]:
    if db is not None:
        try:
            cfg = db.execute(select(UniversalLinkConfig).where(UniversalLinkConfig.key == "default")).scalars().first()
            if cfg and cfg.is_active:
                fps = []
                for item in (cfg.android_sha256_fingerprints or []):
                    if isinstance(item, dict) and item.get("fingerprint"):
                        fps.append(item["fingerprint"].strip().upper())
                    elif isinstance(item, str) and item.strip():
                        fps.append(item.strip().upper())
                if not fps:
                    fps = ASSETLINKS_DATA[0]["target"]["sha256_cert_fingerprints"]
                return [
                    {
                        "relation": ["delegate_permission/common.handle_all_urls"],
                        "target": {
                            "namespace": "android_app",
                            "package_name": cfg.android_package_name or "com.kh.mytravel.mytravel",
                            "sha256_cert_fingerprints": fps,
                        },
                    }
                ]
        except Exception:
            pass
    return ASSETLINKS_DATA


@router.get("/.well-known/apple-app-site-association", include_in_schema=False)
@router.get("/apple-app-site-association", include_in_schema=False)
def get_apple_app_site_association(db: Session = Depends(get_db)) -> JSONResponse:
    data = get_effective_aasa(db)
    return JSONResponse(content=data, media_type="application/json")


@router.get("/.well-known/assetlinks.json", include_in_schema=False)
@router.get("/assetlinks.json", include_in_schema=False)
def get_assetlinks(db: Session = Depends(get_db)) -> JSONResponse:
    data = get_effective_assetlinks(db)
    return JSONResponse(content=data, media_type="application/json")


def _render_deep_link_page(
    *,
    title: str,
    description: str,
    image_url: str,
    app_deep_link: str,
    web_canonical_url: str,
    badge_text: str = "My Travel",
    accent_color: str = "#FFC83D",
) -> HTMLResponse:
    html = f"""<!DOCTYPE html>
<html lang="km">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - My Travel</title>
    <meta name="description" content="{description}">
    <link rel="canonical" href="{web_canonical_url}">
    
    <!-- Open Graph / Facebook / Telegram -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{web_canonical_url}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:site_name" content="My Travel Cambodia">

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{image_url}">

    <!-- iOS Smart App Banner -->
    <meta name="apple-itunes-app" content="app-id=6815109556, app-argument={app_deep_link}">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Kantumruy+Pro:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <style>
        :root {{
            --primary: #17223A;
            --accent: {accent_color};
            --text-dark: #0F172A;
            --text-light: #64748B;
            --bg: #0B0F19;
            --card-bg: #131B2E;
            --border: #334155;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Kantumruy Pro', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        body {{
            background: linear-gradient(145deg, #070A11 0%, #0F172A 100%);
            color: #F8FAFC;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 28px;
            max-width: 480px;
            width: 100%;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
            animation: fadeIn 0.4s ease-out;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(12px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .hero-img {{
            width: 100%;
            height: 220px;
            object-fit: cover;
            background: #1E293B;
            display: block;
        }}
        .content {{
            padding: 24px;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(255, 200, 61, 0.15);
            color: #FFC83D;
            border: 1px solid rgba(255, 200, 61, 0.3);
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 800;
            margin-bottom: 14px;
        }}
        h1 {{
            font-size: 20px;
            font-weight: 900;
            line-height: 1.4;
            color: #FFFFFF;
            margin-bottom: 10px;
        }}
        p.desc {{
            font-size: 14px;
            color: #94A3B8;
            line-height: 1.6;
            margin-bottom: 24px;
        }}
        .btn-open {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            width: 100%;
            background: #FFC83D;
            color: #0F172A;
            text-decoration: none;
            padding: 15px;
            border-radius: 18px;
            font-weight: 800;
            font-size: 15px;
            box-shadow: 0 4px 16px rgba(255, 200, 61, 0.35);
            transition: all 0.2s ease;
        }}
        .btn-open:hover {{
            background: #F5B82E;
            transform: translateY(-1px);
        }}
        .btn-secondary {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
            background: transparent;
            color: #94A3B8;
            border: 1px solid var(--border);
            text-decoration: none;
            padding: 12px;
            border-radius: 16px;
            font-weight: 700;
            font-size: 13px;
            margin-top: 12px;
            transition: all 0.2s ease;
        }}
        .btn-secondary:hover {{
            color: #FFFFFF;
            border-color: #64748B;
        }}
        .footer-note {{
            text-align: center;
            font-size: 11.5px;
            color: #64748B;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <img class="hero-img" src="{image_url}" alt="{title}" onerror="this.src='https://mytravel.taxi/assets/logo.png'">
        <div class="content">
            <div class="badge"><i class="fa-solid fa-taxi"></i> {badge_text}</div>
            <h1>{title}</h1>
            <p class="desc">{description}</p>
            <a href="{app_deep_link}" class="btn-open" id="btn-deep-link">
                <i class="fa-solid fa-mobile-screen-button"></i> បើកក្នុងកម្មវិធី My Travel
            </a>
            <a href="https://mytravel.taxi/" class="btn-secondary">
                <i class="fa-solid fa-globe"></i> ចូលទៅកាន់គេហទំព័រផ្លូវការ
            </a>
            <p class="footer-note">បើកដោយស្វ័យប្រវត្តិកាលណាបានដំឡើងកម្មវិធី My Travel</p>
        </div>
    </div>

    <script>
        // Auto attempt opening in the app on supported devices
        const deepLink = "{app_deep_link}";
        if (deepLink && !window.location.search.includes('no_redirect=1')) {{
            setTimeout(function() {{
                window.location.href = deepLink;
            }}, 600);
        }}
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html)


def _sanitize_og_image(url: str) -> str:
    if not url or url.startswith("data:"):
        return "https://mytravel.taxi/assets/logo.png"
    return url


def _render_trip_detail_page(
    *,
    trip: Trip,
    vehicle: Vehicle | None,
    driver: User | None,
    car_photos: list[str],
    hero_photo: str,
    has_real_car_photo: bool,
    app_deep_link: str,
    web_canonical_url: str,
) -> HTMLResponse:
    title = f"{trip.departure_province} ទៅ {trip.destination_province} - My Travel Taxi"
    dep_time_str = trip.departure_time.strftime("%d/%m/%Y • %I:%M %p") if trip.departure_time else "ឆាប់ៗនេះ"
    price_usd = f"${float(trip.price_per_seat):,.2f}" if trip.price_per_seat else "តម្លៃពិសេស"
    price_khr = f"{int(float(trip.price_per_seat or 0) * 4100):,} ៛" if trip.price_per_seat else "តម្លៃពិសេស"

    vehicle_model = (vehicle.model or "រថយន្តតាក់ស៊ីទំនើប").strip() if vehicle else "រថយន្តតាក់ស៊ីទំនើប"
    vehicle_type = (vehicle.vehicle_type or "Car").strip() if vehicle else "Car"
    plate_number = (vehicle.plate_number or "").strip() if vehicle else ""
    color = (vehicle.color or "").strip() if vehicle else ""

    driver_name = driver.full_name if driver else "អ្នកបើកបរអាជីព"
    rating_val = f"{float(driver.rating_avg or 4.9):.1f}" if driver else "4.9"
    trips_count = driver.completed_trips if (driver and driver.completed_trips) else 120

    description = f"ជើងដំណើរពី {trip.departure_province} ទៅ {trip.destination_province} ជាមួយ {vehicle_model} ({vehicle_type}) | ចេញដំណើរ: {dep_time_str} | តម្លៃ: {price_usd} / {price_khr} | កៅអីនៅសល់: {trip.available_seats}/{trip.total_seats}"
    social_img = _sanitize_og_image(hero_photo)

    gallery_html = ""
    if len(car_photos) > 1:
        thumb_items = []
        for idx, p_url in enumerate(car_photos):
            active_class = "active" if idx == 0 else ""
            thumb_items.append(
                f'<button type="button" class="thumb-btn {active_class}" onclick="selectCarPhoto(this, \'{p_url}\')">'
                f'<img src="{p_url}" alt="Car photo {idx+1}">'
                f'</button>'
            )
        gallery_html = f'<div class="thumbnails-container">{"".join(thumb_items)}</div>'

    verified_badge_html = ""
    if has_real_car_photo:
        verified_badge_html = '<span class="photo-verified-badge"><i class="fa-solid fa-camera"></i> រូបថតរថយន្តពិត</span>'
    else:
        verified_badge_html = '<span class="photo-verified-badge" style="border-color: rgba(255,200,61,0.5);"><i class="fa-solid fa-shield-halved"></i> រថយន្ត MyTravel</span>'

    html = f"""<!DOCTYPE html>
<html lang="km">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <link rel="canonical" href="{web_canonical_url}">

    <!-- Open Graph -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{web_canonical_url}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="{social_img}">
    <meta property="og:site_name" content="My Travel Cambodia">

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <!-- iOS Smart App Banner -->
    <meta name="apple-itunes-app" content="app-id=6815109556, app-argument={app_deep_link}">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Kantumruy+Pro:wght@400;600;700;800;900&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

    <style>
        :root {{
            --primary: #17223A;
            --accent: #FFC83D;
            --accent-hover: #F5B82E;
            --bg-dark: #0B0F19;
            --card-bg: #131B2E;
            --surface-elevated: #1E293B;
            --border: #334155;
            --text-white: #F8FAFC;
            --text-muted: #94A3B8;
            --success: #1FA86C;
            --radius-card: 24px;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Kantumruy Pro', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        body {{
            background: linear-gradient(145deg, #070A11 0%, #0F172A 100%);
            color: var(--text-white);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 16px;
        }}
        .top-nav {{
            max-width: 520px;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
            padding: 0 4px;
        }}
        .brand-link {{
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--accent);
            text-decoration: none;
            font-weight: 800;
            font-size: 15px;
            font-family: 'Outfit', sans-serif;
        }}
        .brand-link img {{
            width: 28px;
            height: 28px;
            border-radius: 8px;
        }}
        .btn-all-trips-nav {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(255, 200, 61, 0.12);
            color: var(--accent);
            border: 1px solid rgba(255, 200, 61, 0.35);
            padding: 7px 14px;
            border-radius: 9999px;
            font-size: 12.5px;
            font-weight: 700;
            text-decoration: none;
            transition: all 0.2s ease;
        }}
        .btn-all-trips-nav:hover {{
            background: var(--accent);
            color: #0F172A;
        }}
        .trip-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: var(--radius-card);
            max-width: 520px;
            width: 100%;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.65);
            animation: fadeIn 0.35s ease-out;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .hero-media {{
            position: relative;
            width: 100%;
            height: 240px;
            background: #1E293B;
            overflow: hidden;
        }}
        .hero-media img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
            transition: transform 0.3s ease;
        }}
        .photo-verified-badge {{
            position: absolute;
            top: 14px;
            left: 14px;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(8px);
            color: var(--accent);
            border: 1px solid rgba(255, 200, 61, 0.4);
            padding: 5px 12px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }}
        .status-badge {{
            position: absolute;
            top: 14px;
            right: 14px;
            background: rgba(31, 168, 108, 0.9);
            color: #FFFFFF;
            padding: 5px 12px;
            border-radius: 9999px;
            font-size: 11.5px;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .thumbnails-container {{
            display: flex;
            gap: 8px;
            padding: 10px 16px;
            background: rgba(11, 15, 25, 0.8);
            border-bottom: 1px solid var(--border);
            overflow-x: auto;
        }}
        .thumb-btn {{
            width: 52px;
            height: 40px;
            border-radius: 8px;
            border: 2px solid transparent;
            overflow: hidden;
            background: none;
            cursor: pointer;
            padding: 0;
            flex-shrink: 0;
            opacity: 0.65;
            transition: all 0.2s ease;
        }}
        .thumb-btn.active, .thumb-btn:hover {{
            opacity: 1;
            border-color: var(--accent);
            transform: scale(1.05);
        }}
        .thumb-btn img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}
        .card-body {{
            padding: 22px;
        }}
        .route-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--surface-elevated);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 14px 18px;
            margin-bottom: 16px;
        }}
        .route-point {{
            display: flex;
            flex-direction: column;
        }}
        .route-label {{
            font-size: 11px;
            color: var(--text-muted);
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        .route-name {{
            font-size: 17px;
            font-weight: 900;
            color: #FFFFFF;
            margin-top: 2px;
        }}
        .route-arrow {{
            color: var(--accent);
            font-size: 16px;
            padding: 0 10px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 18px;
        }}
        .info-box {{
            background: rgba(30, 41, 59, 0.5);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 12px 14px;
        }}
        .info-label {{
            font-size: 11px;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 4px;
            font-weight: 700;
        }}
        .info-val {{
            font-size: 14px;
            font-weight: 800;
            color: #FFFFFF;
        }}
        .info-val.price {{
            color: var(--accent);
            font-size: 16px;
        }}
        .info-val.seats {{
            color: var(--success);
        }}
        .driver-strip {{
            display: flex;
            align-items: center;
            gap: 12px;
            background: var(--surface-elevated);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 12px 16px;
            margin-bottom: 20px;
        }}
        .driver-avatar {{
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: var(--primary);
            border: 2px solid var(--accent);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--accent);
            font-weight: 800;
            font-size: 18px;
            overflow: hidden;
        }}
        .driver-meta {{
            flex: 1;
        }}
        .driver-name {{
            font-size: 14px;
            font-weight: 800;
            color: #FFFFFF;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .driver-stats {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 2px;
        }}
        .driver-stats .star {{
            color: #FFC83D;
        }}
        .btn-primary {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            width: 100%;
            background: var(--accent);
            color: #0F172A;
            text-decoration: none;
            padding: 16px;
            border-radius: 18px;
            font-weight: 900;
            font-size: 16px;
            box-shadow: 0 6px 20px rgba(255, 200, 61, 0.35);
            transition: all 0.2s ease;
            margin-bottom: 10px;
        }}
        .btn-primary:hover {{
            background: var(--accent-hover);
            transform: translateY(-1px);
        }}
        .action-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }}
        .btn-secondary {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
            background: transparent;
            color: #F8FAFC;
            border: 1px solid var(--border);
            text-decoration: none;
            padding: 13px;
            border-radius: 16px;
            font-weight: 700;
            font-size: 13.5px;
            transition: all 0.2s ease;
            cursor: pointer;
        }}
        .btn-secondary:hover {{
            background: var(--surface-elevated);
            border-color: var(--text-muted);
        }}
        .toast {{
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: #1FA86C;
            color: #FFFFFF;
            padding: 10px 22px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 700;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 1000;
        }}
        .toast.show {{
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }}
    </style>
</head>
<body>
    <div class="top-nav">
        <a href="/" class="brand-link">
            <img src="/assets/logo.png" alt="My Travel Logo" onerror="this.src='https://mytravel.taxi/assets/logo.png'">
            <span>MYTRAVEL.TAXI</span>
        </a>
        <a href="/trips" class="btn-all-trips-nav">
            <i class="fa-solid fa-list-ul"></i> ជើងដំណើរទាំងអស់
        </a>
    </div>

    <div class="trip-card">
        <div class="hero-media">
            <img id="main-car-img" src="{hero_photo}" alt="{vehicle_model}" onerror="this.src='https://images.unsplash.com/photo-1549399542-7e3f8b79c341?q=80&w=800&auto=format&fit=crop'">
            {verified_badge_html}
            <div class="status-badge"><i class="fa-solid fa-circle-check"></i> កំពុងបើកកក់</div>
        </div>

        {gallery_html}

        <div class="card-body">
            <div class="route-header">
                <div class="route-point">
                    <span class="route-label">ចេញដំណើរ (From)</span>
                    <span class="route-name">{trip.departure_province}</span>
                </div>
                <div class="route-arrow">
                    <i class="fa-solid fa-arrow-right-long"></i>
                </div>
                <div class="route-point" style="text-align: right;">
                    <span class="route-label">ទៅកាន់ (To)</span>
                    <span class="route-name">{trip.destination_province}</span>
                </div>
            </div>

            <div class="info-grid">
                <div class="info-box">
                    <div class="info-label"><i class="fa-regular fa-clock"></i> ពេលចេញដំណើរ</div>
                    <div class="info-val">{dep_time_str}</div>
                </div>
                <div class="info-box">
                    <div class="info-label"><i class="fa-solid fa-tag"></i> តម្លៃក្នុង ១កៅអី</div>
                    <div class="info-val price">{price_usd} <span style="font-size:12px; font-weight:600; color:var(--text-muted)">({price_khr})</span></div>
                </div>
                <div class="info-box">
                    <div class="info-label"><i class="fa-solid fa-car-side"></i> យានយន្ត</div>
                    <div class="info-val">{vehicle_model} <span style="font-size:11.5px; color:var(--text-muted)">({vehicle_type})</span></div>
                </div>
                <div class="info-box">
                    <div class="info-label"><i class="fa-solid fa-chair"></i> កៅអីនៅសល់</div>
                    <div class="info-val seats">{trip.available_seats} នៃ {trip.total_seats} កៅអី</div>
                </div>
            </div>

            <div class="driver-strip">
                <div class="driver-avatar">
                    <i class="fa-solid fa-user"></i>
                </div>
                <div class="driver-meta">
                    <div class="driver-name">
                        {driver_name}
                        <i class="fa-solid fa-circle-check" style="color:#38BDF8; font-size:13px;" title="Verified Driver"></i>
                    </div>
                    <div class="driver-stats">
                        <span class="star"><i class="fa-solid fa-star"></i> {rating_val}</span> • {trips_count} ជើងជោគជ័យ
                    </div>
                </div>
                {f'<div style="text-align:right; font-size:12px; color:var(--text-muted); font-weight:700;"><i class="fa-solid fa-id-card"></i> {plate_number}</div>' if plate_number else ''}
            </div>

            <a href="{app_deep_link}" class="btn-primary" id="btn-deep-link">
                <i class="fa-solid fa-mobile-screen-button"></i> បើកកក់ក្នុងកម្មវិធី My Travel
            </a>

            <div class="action-row">
                <a href="/trips" class="btn-secondary">
                    <i class="fa-solid fa-magnifying-glass"></i> ស្វែងរកជើងផ្សេង
                </a>
                <button type="button" class="btn-secondary" onclick="copyTripLink()">
                    <i class="fa-solid fa-share-nodes"></i> ចម្លងដំណភ្ជាប់
                </button>
            </div>
        </div>
    </div>

    <div id="toast" class="toast">✓ បានចម្លងដំណភ្ជាប់រួចរាល់!</div>

    <script>
        function selectCarPhoto(btn, src) {{
            const mainImg = document.getElementById('main-car-img');
            if (mainImg) mainImg.src = src;
            document.querySelectorAll('.thumb-btn').forEach(b => b.classList.remove('active'));
            if (btn) btn.classList.add('active');
        }}

        function copyTripLink() {{
            navigator.clipboard.writeText(window.location.href).then(() => {{
                const toast = document.getElementById('toast');
                toast.classList.add('show');
                setTimeout(() => toast.classList.remove('show'), 2500);
            }});
        }}

        const deepLink = "{app_deep_link}";
        if (deepLink && !window.location.search.includes('no_redirect=1')) {{
            setTimeout(function() {{
                window.location.href = deepLink;
            }}, 600);
        }}
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html)


@router.get("/trips/{trip_id}", response_class=HTMLResponse, include_in_schema=False)
@router.get("/t/{trip_id}", response_class=HTMLResponse, include_in_schema=False)
def open_trip_universal_link(
    trip_id: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    try:
        trip_uuid = uuid.UUID(trip_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid trip ID")

    trip = db.get(Trip, trip_uuid)
    if not trip:
        return _render_deep_link_page(
            title="ដំណើរកម្សាន្តមិនត្រូវបានរកឃើញទេ",
            description="ដំណើរកម្សាន្តនេះប្រហែលជាត្រូវបានបញ្ចប់ ឬលុបចេញពីប្រព័ន្ធ។ សូមស្វែងរកជើងដំណើរថ្មីៗនៅលើ My Travel!",
            image_url="https://mytravel.taxi/assets/logo.png",
            app_deep_link=f"mytravel://trip/{trip_id}",
            web_canonical_url=f"https://mytravel.taxi/trips/{trip_id}",
            badge_text="My Travel Trip",
        )

    vehicle = db.get(Vehicle, trip.vehicle_id) if trip.vehicle_id else None
    driver = db.get(User, trip.driver_id) if trip.driver_id else None

    car_photos: list[str] = []
    if vehicle and vehicle.image_urls:
        for img in vehicle.image_urls:
            if img and isinstance(img, str) and img.strip():
                car_photos.append(img.strip())

    has_real_car_photo = len(car_photos) > 0
    if has_real_car_photo:
        primary_photo = car_photos[0]
    else:
        primary_photo = "https://mytravel.taxi/assets/default_car.jpg"

    return _render_trip_detail_page(
        trip=trip,
        vehicle=vehicle,
        driver=driver,
        car_photos=car_photos,
        hero_photo=primary_photo,
        has_real_car_photo=has_real_car_photo,
        app_deep_link=f"mytravel://trip/{trip_id}",
        web_canonical_url=f"https://mytravel.taxi/trips/{trip_id}",
    )


@router.get("/news/{article_id}", response_class=HTMLResponse, include_in_schema=False)
def open_news_universal_link(
    article_id: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    try:
        article_uuid = uuid.UUID(article_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid news article ID")

    article = db.get(NewsArticle, article_uuid)
    if not article:
        return _render_deep_link_page(
            title="ព័ត៌មានមិនត្រូវបានរកឃើញទេ",
            description="ព័ត៌មាននេះប្រហែលជាត្រូវបានលុបចេញពីប្រព័ន្ធ។ សូមពិនិត្យព័ត៌មានថ្មីៗនៅលើ My Travel!",
            image_url="https://mytravel.taxi/assets/logo.png",
            app_deep_link=f"mytravel://news/{article_id}",
            web_canonical_url=f"https://mytravel.taxi/news/{article_id}",
            badge_text="My Travel News",
        )

    title = article.title_kh or article.title
    description = article.summary_kh or article.summary or article.content or "ព័ត៌មានថ្មីៗពី My Travel"
    img_url = (
        article.image_url
        if (article.image_url and article.image_url.strip())
        else "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800&auto=format&fit=crop"
    )

    return _render_deep_link_page(
        title=title,
        description=description,
        image_url=img_url,
        app_deep_link=f"mytravel://news/{article_id}",
        web_canonical_url=f"https://mytravel.taxi/news/{article_id}",
        badge_text=article.category or "ព័ត៌មានប្រព័ន្ធ",
    )


@router.get("/ads/{ad_id}", include_in_schema=False)
def open_ad_universal_link(
    ad_id: str,
    db: Session = Depends(get_db),
) -> Any:
    try:
        ad_uuid = uuid.UUID(ad_id)
    except Exception:
        return RedirectResponse(url="https://mytravel.taxi/", status_code=302)

    ad = db.get(SystemAd, ad_uuid)
    if not ad:
        return RedirectResponse(url="https://mytravel.taxi/", status_code=302)

    target_url = (ad.link_url or "").strip()
    if target_url.startswith("http://") or target_url.startswith("https://"):
        return RedirectResponse(url=target_url, status_code=302)
    elif target_url.startswith("/"):
        return RedirectResponse(url=f"https://mytravel.taxi{target_url}", status_code=302)
    elif target_url:
        return RedirectResponse(url=f"https://mytravel.taxi/{target_url}", status_code=302)
    return RedirectResponse(url="https://mytravel.taxi/", status_code=302)
