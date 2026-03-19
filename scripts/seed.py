#!/usr/bin/env python3
"""
OMNI Risk Engine — Seed Script
5 tenant + her biri için 3-5 facility
Çalıştır: python3 scripts/seed.py
"""
import uuid
import sys
import os
import httpx
from dotenv import dotenv_values

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DOTENV_PATH = os.path.join(os.path.dirname(__file__), "../.env")
if not os.path.exists(DOTENV_PATH):
    DOTENV_PATH = os.path.expanduser("~/Desktop/.env")

vals = dotenv_values(DOTENV_PATH)
SUPABASE_URL = vals.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
# service_role key — RLS'i bypass eder
SUPABASE_SERVICE_KEY = vals.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("HATA: SUPABASE_URL veya SUPABASE_SERVICE_KEY bulunamadı.")
    sys.exit(1)

BASE_HEADERS = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
}


def upsert(table: str, payload: dict):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {**BASE_HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"}
    with httpx.Client(timeout=20) as client:
        resp = client.post(url, headers=headers, json=payload)
    if resp.status_code not in (200, 201):
        print(f"  [HATA] UPSERT {table}: {resp.status_code} — {resp.text[:300]}")
        return None
    return resp.json()


def point_wkt(lon: float, lat: float) -> str:
    return f"SRID=4326;POINT({lon} {lat})"


# ─────────────────────────────────────────────
# SEED DATA
# Sector enum: MUNICIPALITY | HOSPITAL | BANK |
#              UNIVERSITY | INDUSTRIAL | INFRASTRUCTURE | HOTEL | EDUCATION
# ─────────────────────────────────────────────

TENANTS = [
    {
        "id": "11111111-0000-0000-0000-000000000001",
        "name": "Beylikdüzü Belediyesi",
        "slug": "beylikduzu-belediyesi",
        "sector": "MUNICIPALITY",
        "is_active": True,
        "settings": {"country": "TR", "city": "İstanbul", "district": "Beylikdüzü", "plan": "pro"},
    },
    {
        "id": "22222222-0000-0000-0000-000000000002",
        "name": "Akbank T.A.Ş.",
        "slug": "akbank",
        "sector": "BANK",
        "is_active": True,
        "settings": {"country": "TR", "city": "İstanbul", "swift": "AKBKTRIS", "plan": "enterprise"},
    },
    {
        "id": "33333333-0000-0000-0000-000000000003",
        "name": "Medical Park Hastaneleri",
        "slug": "medical-park-hastaneleri",
        "sector": "HOSPITAL",
        "is_active": True,
        "settings": {"country": "TR", "chain": "Medical Park Group", "bed_count_total": 4200, "plan": "enterprise"},
    },
    {
        "id": "44444444-0000-0000-0000-000000000004",
        "name": "Rixos Hotels",
        "slug": "rixos-hotels",
        "sector": "HOTEL",
        "is_active": True,
        "settings": {"country": "TR", "chain": "Rixos Premium Collection", "plan": "pro"},
    },
    {
        "id": "55555555-0000-0000-0000-000000000005",
        "name": "Türkiye İş Bankası A.Ş.",
        "slug": "is-bankasi",
        "sector": "BANK",
        "is_active": True,
        "settings": {"country": "TR", "city": "İstanbul", "swift": "ISBKTRIS", "founded": 1924, "plan": "enterprise"},
    },
]

FACILITIES = [
    # ──────────────────────────────────────────
    # 1. BEYLİKDÜZÜ BELEDİYESİ  (5 tesis)
    # ──────────────────────────────────────────
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "11111111-0000-0000-0000-000000000001",
        "code": "BLD-001",
        "name": "Beylikdüzü Belediye Sarayı",
        "sector": "MUNICIPALITY",
        "is_active": True,
        "geom": point_wkt(28.6456, 41.0047),
        "il_kodu": "34",
        "ilce_kodu": "3499",
        "address": "Adnan Kahveci Mah. Lale Cad. No:1, Beylikdüzü / İstanbul",
        "elevation_m": 45.0,
        "building_age": 18,
        "construction_type": "RC",
        "floor_count": 6,
        "total_area_m2": 8500.0,
        "soil_class": "ZC",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 320,
        "operates_24h": False,
        "asset_value_usd": 12000000.0,
        "extra_data": {"sub_sector": "administration", "daily_visitors": 1200, "backup_generator": True, "is_critical_infra": True},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "11111111-0000-0000-0000-000000000001",
        "code": "BLD-002",
        "name": "Beylikdüzü Kapalı Spor Salonu",
        "sector": "MUNICIPALITY",
        "is_active": True,
        "geom": point_wkt(28.6503, 41.0087),
        "il_kodu": "34",
        "ilce_kodu": "3499",
        "address": "Kavaklı Mah. Spor Cad. No:12, Beylikdüzü / İstanbul",
        "elevation_m": 48.0,
        "building_age": 12,
        "construction_type": "steel",
        "floor_count": 2,
        "total_area_m2": 3200.0,
        "soil_class": "ZC",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 45,
        "operates_24h": False,
        "asset_value_usd": 3500000.0,
        "extra_data": {"sub_sector": "sports_facility", "capacity_persons": 2000, "is_critical_infra": False},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "11111111-0000-0000-0000-000000000001",
        "code": "BLD-003",
        "name": "Beylikdüzü Kültür ve Sanat Merkezi",
        "sector": "MUNICIPALITY",
        "is_active": True,
        "geom": point_wkt(28.6532, 41.0063),
        "il_kodu": "34",
        "ilce_kodu": "3499",
        "address": "Cumhuriyet Mah. Kültür Parkı, Beylikdüzü / İstanbul",
        "elevation_m": 46.5,
        "building_age": 8,
        "construction_type": "RC",
        "floor_count": 3,
        "total_area_m2": 4800.0,
        "soil_class": "ZC",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 65,
        "operates_24h": False,
        "asset_value_usd": 6000000.0,
        "extra_data": {"sub_sector": "culture", "theater_capacity": 350, "exhibition_halls": 4},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "11111111-0000-0000-0000-000000000001",
        "code": "BLD-004",
        "name": "Beylikdüzü İtfaiye Müdürlüğü",
        "sector": "MUNICIPALITY",
        "is_active": True,
        "geom": point_wkt(28.6488, 41.0022),
        "il_kodu": "34",
        "ilce_kodu": "3499",
        "address": "Dereağzı Mah. İtfaiye Cad. No:3, Beylikdüzü / İstanbul",
        "elevation_m": 42.0,
        "building_age": 10,
        "construction_type": "RC",
        "floor_count": 2,
        "total_area_m2": 1800.0,
        "soil_class": "ZD",
        "seismic_zone": 1,
        "flood_zone": "medium",
        "employee_count": 80,
        "operates_24h": True,
        "asset_value_usd": 4500000.0,
        "extra_data": {"sub_sector": "emergency_services", "vehicle_count": 12, "response_time_min": 4, "is_critical_infra": True},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "11111111-0000-0000-0000-000000000001",
        "code": "BLD-005",
        "name": "Beylikdüzü Su ve Kanalizasyon İşletmesi",
        "sector": "MUNICIPALITY",
        "is_active": True,
        "geom": point_wkt(28.6521, 41.0010),
        "il_kodu": "34",
        "ilce_kodu": "3499",
        "address": "Büyükşehir Mah. Su Tesisi Yolu No:7, Beylikdüzü / İstanbul",
        "elevation_m": 40.0,
        "building_age": 22,
        "construction_type": "RC",
        "floor_count": 1,
        "total_area_m2": 2200.0,
        "soil_class": "ZD",
        "seismic_zone": 1,
        "flood_zone": "high",
        "employee_count": 55,
        "operates_24h": True,
        "asset_value_usd": 8000000.0,
        "extra_data": {"sub_sector": "utility", "daily_capacity_m3": 15000, "backup_pump": True, "is_critical_infra": True},
    },

    # ──────────────────────────────────────────
    # 2. AKBANK  (4 tesis)
    # ──────────────────────────────────────────
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "22222222-0000-0000-0000-000000000002",
        "code": "AKB-001",
        "name": "Akbank Genel Müdürlük — Sabancı Center",
        "sector": "BANK",
        "is_active": True,
        "geom": point_wkt(29.0168, 41.0760),
        "il_kodu": "34",
        "ilce_kodu": "3418",
        "address": "Sabancı Center, 4. Levent, Beşiktaş / İstanbul",
        "elevation_m": 62.0,
        "building_age": 28,
        "construction_type": "steel",
        "floor_count": 38,
        "total_area_m2": 45000.0,
        "soil_class": "ZB",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 2800,
        "operates_24h": False,
        "asset_value_usd": 350000000.0,
        "extra_data": {"sub_sector": "headquarters", "data_center_tier": 3, "ups_capacity_kva": 2000, "is_critical_infra": True},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "22222222-0000-0000-0000-000000000002",
        "code": "AKB-002",
        "name": "Akbank Teknoloji ve Operasyon Merkezi — Esenyurt",
        "sector": "BANK",
        "is_active": True,
        "geom": point_wkt(28.6721, 41.0330),
        "il_kodu": "34",
        "ilce_kodu": "3434",
        "address": "Esenkent Mah. Teknoloji Cad. No:24, Esenyurt / İstanbul",
        "elevation_m": 38.0,
        "building_age": 6,
        "construction_type": "RC",
        "floor_count": 4,
        "total_area_m2": 12000.0,
        "soil_class": "ZD",
        "seismic_zone": 1,
        "flood_zone": "medium",
        "employee_count": 450,
        "operates_24h": True,
        "asset_value_usd": 120000000.0,
        "extra_data": {"sub_sector": "data_center", "data_center_tier": 4, "redundancy": "2N", "cooling_type": "precision_ac", "is_critical_infra": True},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "22222222-0000-0000-0000-000000000002",
        "code": "AKB-003",
        "name": "Akbank Çağrı Merkezi — Şişli",
        "sector": "BANK",
        "is_active": True,
        "geom": point_wkt(28.9940, 41.0625),
        "il_kodu": "34",
        "ilce_kodu": "3440",
        "address": "Mecidiyeköy Mah. Büyükdere Cad. No:102, Şişli / İstanbul",
        "elevation_m": 55.0,
        "building_age": 15,
        "construction_type": "RC",
        "floor_count": 8,
        "total_area_m2": 6500.0,
        "soil_class": "ZC",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 1200,
        "operates_24h": True,
        "asset_value_usd": 40000000.0,
        "extra_data": {"sub_sector": "call_center", "seats": 900, "is_critical_infra": False},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "22222222-0000-0000-0000-000000000002",
        "code": "AKB-004",
        "name": "Akbank Beylikdüzü Şubesi",
        "sector": "BANK",
        "is_active": True,
        "geom": point_wkt(28.6460, 41.0052),
        "il_kodu": "34",
        "ilce_kodu": "3499",
        "address": "Adnan Kahveci Mah. Alkent 2000 AVM, Beylikdüzü / İstanbul",
        "elevation_m": 44.0,
        "building_age": 9,
        "construction_type": "RC",
        "floor_count": 1,
        "total_area_m2": 280.0,
        "soil_class": "ZC",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 18,
        "operates_24h": False,
        "asset_value_usd": 2500000.0,
        "extra_data": {"sub_sector": "branch", "atm_count": 4, "safe_room": True, "is_critical_infra": False},
    },

    # ──────────────────────────────────────────
    # 3. MEDICAL PARK HASTANELERİ  (5 tesis)
    # ──────────────────────────────────────────
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "33333333-0000-0000-0000-000000000003",
        "code": "MPK-001",
        "name": "Medical Park Göztepe Hastanesi",
        "sector": "HOSPITAL",
        "is_active": True,
        "geom": point_wkt(29.0573, 40.9693),
        "il_kodu": "34",
        "ilce_kodu": "3446",
        "address": "Fahrettin Kerim Gökay Cad. No:49, Göztepe / Kadıköy, İstanbul",
        "elevation_m": 25.0,
        "building_age": 14,
        "construction_type": "RC",
        "floor_count": 12,
        "total_area_m2": 22000.0,
        "soil_class": "ZD",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 680,
        "operates_24h": True,
        "asset_value_usd": 85000000.0,
        "extra_data": {"sub_sector": "general_hospital", "bed_count": 280, "icu_beds": 32, "or_rooms": 8, "helipad": True, "is_critical_infra": True},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "33333333-0000-0000-0000-000000000003",
        "code": "MPK-002",
        "name": "Medical Park Florya Hastanesi",
        "sector": "HOSPITAL",
        "is_active": True,
        "geom": point_wkt(28.7736, 40.9803),
        "il_kodu": "34",
        "ilce_kodu": "3454",
        "address": "Şenlikköy Mah. Florya Cad. No:1, Bakırköy / İstanbul",
        "elevation_m": 18.0,
        "building_age": 10,
        "construction_type": "RC",
        "floor_count": 10,
        "total_area_m2": 18500.0,
        "soil_class": "ZD",
        "seismic_zone": 1,
        "flood_zone": "medium",
        "employee_count": 540,
        "operates_24h": True,
        "asset_value_usd": 72000000.0,
        "extra_data": {"sub_sector": "general_hospital", "bed_count": 230, "icu_beds": 24, "or_rooms": 6, "helipad": False, "is_critical_infra": True},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "33333333-0000-0000-0000-000000000003",
        "code": "MPK-003",
        "name": "Medical Park Bahçelievler Hastanesi",
        "sector": "HOSPITAL",
        "is_active": True,
        "geom": point_wkt(28.8605, 41.0014),
        "il_kodu": "34",
        "ilce_kodu": "3404",
        "address": "Yenibosna Merkez Mah. Adnan Adıvar Cad. No:2, Bahçelievler / İstanbul",
        "elevation_m": 50.0,
        "building_age": 7,
        "construction_type": "RC",
        "floor_count": 9,
        "total_area_m2": 15000.0,
        "soil_class": "ZC",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 420,
        "operates_24h": True,
        "asset_value_usd": 58000000.0,
        "extra_data": {"sub_sector": "general_hospital", "bed_count": 180, "icu_beds": 18, "or_rooms": 5, "helipad": False, "is_critical_infra": True},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "33333333-0000-0000-0000-000000000003",
        "code": "MPK-004",
        "name": "Medical Park Gebze Hastanesi",
        "sector": "HOSPITAL",
        "is_active": True,
        "geom": point_wkt(29.4313, 40.8031),
        "il_kodu": "41",
        "ilce_kodu": "4106",
        "address": "Güzeller Mah. Kooperatif Cad. No:25, Gebze / Kocaeli",
        "elevation_m": 70.0,
        "building_age": 5,
        "construction_type": "RC",
        "floor_count": 8,
        "total_area_m2": 14000.0,
        "soil_class": "ZC",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 380,
        "operates_24h": True,
        "asset_value_usd": 52000000.0,
        "extra_data": {"sub_sector": "general_hospital", "bed_count": 160, "icu_beds": 16, "or_rooms": 4, "helipad": False, "is_critical_infra": True},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "33333333-0000-0000-0000-000000000003",
        "code": "MPK-005",
        "name": "Medical Park İstanbul Hastanesi — Bağcılar",
        "sector": "HOSPITAL",
        "is_active": True,
        "geom": point_wkt(28.8430, 41.0367),
        "il_kodu": "34",
        "ilce_kodu": "3403",
        "address": "Güneşli Mah. Abdi İpekçi Cad. No:4, Bağcılar / İstanbul",
        "elevation_m": 53.0,
        "building_age": 11,
        "construction_type": "RC",
        "floor_count": 11,
        "total_area_m2": 19500.0,
        "soil_class": "ZC",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 560,
        "operates_24h": True,
        "asset_value_usd": 78000000.0,
        "extra_data": {"sub_sector": "general_hospital", "bed_count": 250, "icu_beds": 28, "or_rooms": 7, "helipad": True, "is_critical_infra": True},
    },

    # ──────────────────────────────────────────
    # 4. RİXOS HOTELS  (4 tesis)
    # ──────────────────────────────────────────
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "44444444-0000-0000-0000-000000000004",
        "code": "RXS-001",
        "name": "Rixos Premium Belek",
        "sector": "HOTEL",
        "is_active": True,
        "geom": point_wkt(31.0648, 36.8612),
        "il_kodu": "07",
        "ilce_kodu": "0703",
        "address": "Çamyuva Mah. Lara Cad., Belek / Antalya",
        "elevation_m": 5.0,
        "building_age": 20,
        "construction_type": "RC",
        "floor_count": 7,
        "total_area_m2": 85000.0,
        "soil_class": "ZD",
        "seismic_zone": 3,
        "flood_zone": "medium",
        "employee_count": 1200,
        "operates_24h": True,
        "asset_value_usd": 180000000.0,
        "extra_data": {"sub_sector": "resort", "room_count": 672, "stars": 5, "beach_length_m": 800, "pool_count": 12},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "44444444-0000-0000-0000-000000000004",
        "code": "RXS-002",
        "name": "Rixos Pera Istanbul",
        "sector": "HOTEL",
        "is_active": True,
        "geom": point_wkt(28.9770, 41.0322),
        "il_kodu": "34",
        "ilce_kodu": "3456",
        "address": "Meşrutiyet Cad. No:67, Tepebaşı / Beyoğlu, İstanbul",
        "elevation_m": 60.0,
        "building_age": 16,
        "construction_type": "RC",
        "floor_count": 19,
        "total_area_m2": 12000.0,
        "soil_class": "ZB",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 280,
        "operates_24h": True,
        "asset_value_usd": 95000000.0,
        "extra_data": {"sub_sector": "city_hotel", "room_count": 198, "stars": 5, "spa": True, "conference_halls": 4},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "44444444-0000-0000-0000-000000000004",
        "code": "RXS-003",
        "name": "Rixos Downtown Antalya",
        "sector": "HOTEL",
        "is_active": True,
        "geom": point_wkt(30.7133, 36.8969),
        "il_kodu": "07",
        "ilce_kodu": "0701",
        "address": "Konyaaltı Mah. Atatürk Cad. No:45, Konyaaltı / Antalya",
        "elevation_m": 12.0,
        "building_age": 9,
        "construction_type": "RC",
        "floor_count": 16,
        "total_area_m2": 18000.0,
        "soil_class": "ZC",
        "seismic_zone": 3,
        "flood_zone": "low",
        "employee_count": 350,
        "operates_24h": True,
        "asset_value_usd": 110000000.0,
        "extra_data": {"sub_sector": "city_hotel", "room_count": 310, "stars": 5, "spa": True, "conference_halls": 6},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "44444444-0000-0000-0000-000000000004",
        "code": "RXS-004",
        "name": "Rixos Sungate Antalya",
        "sector": "HOTEL",
        "is_active": True,
        "geom": point_wkt(30.6230, 36.8560),
        "il_kodu": "07",
        "ilce_kodu": "0709",
        "address": "Kundu Mah. Lara Turizm Bölgesi, Kepez / Antalya",
        "elevation_m": 8.0,
        "building_age": 17,
        "construction_type": "RC",
        "floor_count": 5,
        "total_area_m2": 62000.0,
        "soil_class": "ZD",
        "seismic_zone": 3,
        "flood_zone": "medium",
        "employee_count": 950,
        "operates_24h": True,
        "asset_value_usd": 145000000.0,
        "extra_data": {"sub_sector": "resort", "room_count": 524, "stars": 5, "beach_length_m": 600, "pool_count": 8},
    },

    # ──────────────────────────────────────────
    # 5. TÜRKİYE İŞ BANKASI  (5 tesis)
    # ──────────────────────────────────────────
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "55555555-0000-0000-0000-000000000005",
        "code": "ISB-001",
        "name": "İş Bankası Genel Müdürlük — İş Kuleleri",
        "sector": "BANK",
        "is_active": True,
        "geom": point_wkt(29.0116, 41.0807),
        "il_kodu": "34",
        "ilce_kodu": "3418",
        "address": "İş Kuleleri, 4. Levent, Beşiktaş / İstanbul",
        "elevation_m": 65.0,
        "building_age": 32,
        "construction_type": "steel",
        "floor_count": 42,
        "total_area_m2": 60000.0,
        "soil_class": "ZB",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 4200,
        "operates_24h": False,
        "asset_value_usd": 600000000.0,
        "extra_data": {"sub_sector": "headquarters", "data_center_tier": 3, "ups_capacity_kva": 5000, "iconic_landmark": True, "is_critical_infra": True},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "55555555-0000-0000-0000-000000000005",
        "code": "ISB-002",
        "name": "İş Bankası Veri Merkezi — Gebze",
        "sector": "BANK",
        "is_active": True,
        "geom": point_wkt(29.4421, 40.8050),
        "il_kodu": "41",
        "ilce_kodu": "4106",
        "address": "OSB Mah. Bilişim Cad. No:8, Gebze / Kocaeli",
        "elevation_m": 72.0,
        "building_age": 8,
        "construction_type": "RC",
        "floor_count": 3,
        "total_area_m2": 20000.0,
        "soil_class": "ZB",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 320,
        "operates_24h": True,
        "asset_value_usd": 200000000.0,
        "extra_data": {"sub_sector": "data_center", "data_center_tier": 4, "redundancy": "2N+1", "cooling_type": "liquid", "pue": 1.35, "is_critical_infra": True},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "55555555-0000-0000-0000-000000000005",
        "code": "ISB-003",
        "name": "İş Bankası Ödeme Sistemleri Merkezi — Maslak",
        "sector": "BANK",
        "is_active": True,
        "geom": point_wkt(29.0198, 41.1104),
        "il_kodu": "34",
        "ilce_kodu": "3402",
        "address": "Büyükdere Cad. No:123, Maslak / Sarıyer, İstanbul",
        "elevation_m": 68.0,
        "building_age": 11,
        "construction_type": "RC",
        "floor_count": 12,
        "total_area_m2": 18000.0,
        "soil_class": "ZB",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 880,
        "operates_24h": True,
        "asset_value_usd": 160000000.0,
        "extra_data": {"sub_sector": "payment_ops", "transactions_per_day": 12000000, "atm_network_size": 8700, "is_critical_infra": True},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "55555555-0000-0000-0000-000000000005",
        "code": "ISB-004",
        "name": "İş Bankası Kültür Vakfı — Şişli",
        "sector": "BANK",
        "is_active": True,
        "geom": point_wkt(28.9880, 41.0640),
        "il_kodu": "34",
        "ilce_kodu": "3440",
        "address": "Halaskargazi Cad. No:1, Şişli / İstanbul",
        "elevation_m": 58.0,
        "building_age": 45,
        "construction_type": "masonry",
        "floor_count": 5,
        "total_area_m2": 5500.0,
        "soil_class": "ZC",
        "seismic_zone": 1,
        "flood_zone": "low",
        "employee_count": 120,
        "operates_24h": False,
        "asset_value_usd": 18000000.0,
        "extra_data": {"sub_sector": "corporate_culture", "historical_building": True, "renovation_year": 2015, "library": True},
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": "55555555-0000-0000-0000-000000000005",
        "code": "ISB-005",
        "name": "İş Bankası Anadolu Bölge Müdürlüğü — Ankara",
        "sector": "BANK",
        "is_active": True,
        "geom": point_wkt(32.8597, 39.9334),
        "il_kodu": "06",
        "ilce_kodu": "0602",
        "address": "Atatürk Bulvarı No:31, Kızılay / Çankaya, Ankara",
        "elevation_m": 890.0,
        "building_age": 38,
        "construction_type": "RC",
        "floor_count": 8,
        "total_area_m2": 7200.0,
        "soil_class": "ZC",
        "seismic_zone": 2,
        "flood_zone": "low",
        "employee_count": 430,
        "operates_24h": False,
        "asset_value_usd": 35000000.0,
        "extra_data": {"sub_sector": "regional_office", "regional_branches": 142, "safe_vault": True},
    },
]


# ─────────────────────────────────────────────
# RUNNER
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("OMNI Risk Engine — Seed Data")
    print(f"Hedef: {SUPABASE_URL}")
    print("=" * 60)

    # ── 1. Tenants ───────────────────────────
    print("\n[1/2] Tenants ekleniyor...")
    tenant_ok, tenant_fail = 0, 0
    for t in TENANTS:
        result = upsert("tenants", t)
        if result is not None:
            print(f"  ✓ {t['name']}  [{t['sector']}]")
            tenant_ok += 1
        else:
            tenant_fail += 1

    # ── 2. Facilities ────────────────────────
    print("\n[2/2] Facilities ekleniyor...")
    tenant_map = {t["id"]: t["name"] for t in TENANTS}
    fac_ok, fac_fail = 0, 0

    for f in FACILITIES:
        result = upsert("facilities", f)
        if result is not None:
            owner = tenant_map.get(f["tenant_id"], f["tenant_id"])
            print(f"  ✓ [{f['code']}] {f['name']}")
            fac_ok += 1
        else:
            fac_fail += 1

    # ── Özet ─────────────────────────────────
    print("\n" + "=" * 60)
    print(f"Tenants   : {tenant_ok}/{len(TENANTS)} başarılı")
    print(f"Facilities: {fac_ok}/{len(FACILITIES)} başarılı")
    if tenant_fail + fac_fail == 0:
        print("Tüm kayıtlar başarıyla eklendi.")
    else:
        print(f"UYARI: {tenant_fail + fac_fail} kayıt başarısız.")
    print("=" * 60)


if __name__ == "__main__":
    main()
