import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db
from ..models import Trip, NewsArticle, SystemAd, Vehicle

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


@router.get("/.well-known/apple-app-site-association", include_in_schema=False)
@router.get("/apple-app-site-association", include_in_schema=False)
def get_apple_app_site_association() -> JSONResponse:
    return JSONResponse(content=AASA_DATA, media_type="application/json")


@router.get("/.well-known/assetlinks.json", include_in_schema=False)
@router.get("/assetlinks.json", include_in_schema=False)
def get_assetlinks() -> JSONResponse:
    return JSONResponse(content=ASSETLINKS_DATA, media_type="application/json")


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
    <meta name="apple-itunes-app" content="app-id=com.kh.mytravel.app, app-argument={app_deep_link}">

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
    vehicle_info = f"{vehicle.make} {vehicle.model}" if vehicle else "រថយន្តតាក់ស៊ីទំនើប"
    vehicle_photo = (
        vehicle.photo_url
        if (vehicle and vehicle.photo_url)
        else "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?q=80&w=800&auto=format&fit=crop"
    )

    dep_time = trip.departure_time.strftime("%d/%m/%Y %H:%M") if trip.departure_time else "ឆាប់ៗនេះ"
    price_formatted = f"${trip.price_per_seat:,.2f}" if trip.price_per_seat else "តម្លៃពិសេស"

    title = f"{trip.departure_province} ទៅ {trip.destination_province}"
    description = (
        f"ដំណើរកម្សាន្តជាមួយ {vehicle_info} | ចេញដំណើរ: {dep_time} | "
        f"តម្លៃ: {price_formatted}/កៅអី | កៅអីនៅសល់: {trip.available_seats}។ កក់ឥឡូវនេះ!"
    )

    return _render_deep_link_page(
        title=title,
        description=description,
        image_url=vehicle_photo,
        app_deep_link=f"mytravel://trip/{trip_id}",
        web_canonical_url=f"https://mytravel.taxi/trips/{trip_id}",
        badge_text="ដំណើរកម្សាន្តផ្លូវជាតិ",
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
