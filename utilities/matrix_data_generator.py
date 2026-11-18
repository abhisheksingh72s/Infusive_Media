"""
Multi-Currency Enterprise Client & POC Matrix Data Generator
=============================================================
Provides 20 distinct corporate clients from 20 different countries,
each configured with 10 distinct POCs/Projects across 10 global currencies.
All delivered emails route to qa.tekinspirations@gmail.com for automated verification.
"""

from typing import List, Dict, Any

NOTIFICATION_EMAIL = "qa.tekinspirations@gmail.com"

# The 10 Target Currencies with realistic small test budgets and services
CURRENCY_CONFIGS = [
    {"code": "USD", "symbol": "$", "budget": "25.00", "service": "PPC", "title": "Director of Global Operations"},
    {"code": "EUR", "symbol": "€", "budget": "25.00", "service": "Meta Ads", "title": "VP of European Markets"},
    {"code": "GBP", "symbol": "£", "budget": "20.00", "service": "SEO", "title": "Head of UK Engagements"},
    {"code": "INR", "symbol": "₹", "budget": "2500.00", "service": "UI/UX Design", "title": "Chief Strategy Officer (APAC)"},
    {"code": "CAD", "symbol": "$", "budget": "35.00", "service": "PPC", "title": "Managing Director (Americas)"},
    {"code": "AUD", "symbol": "$", "budget": "30.00", "service": "Meta Ads", "title": "Head of Australasia Growth"},
    {"code": "SGD", "symbol": "$", "budget": "35.00", "service": "SEO", "title": "Director of Southeast Asia Commercials"},
    {"code": "AED", "symbol": "AED", "budget": "100.00", "service": "UI/UX Design", "title": "VP of Middle East Initiatives"},
    {"code": "JPY", "symbol": "¥", "budget": "3500.00", "service": "PPC", "title": "Country Head of East Asia"},
    {"code": "CHF", "symbol": "CHF", "budget": "25.00", "service": "Meta Ads", "title": "Chief Financial Operations Officer"},
]

# 20 Enterprise Companies from 20 Distinct Countries
COUNTRIES_20 = [
    {
        "id": 1,
        "company_name": "Apex Global Solutions LLC",
        "initial": "AGS",
        "country": "United States",
        "country_code": "+1",
        "poc_first": "John",
        "poc_last": "Carter",
        "phone": "2025550143",
        "address": "One World Trade Center, Suite 4500, New York, NY 10007",
    },
    {
        "id": 2,
        "company_name": "Vanguard Strategic Systems Ltd",
        "initial": "VSS",
        "country": "United Kingdom",
        "country_code": "+44",
        "poc_first": "Arthur",
        "poc_last": "Pendleton",
        "phone": "2079460192",
        "address": "25 Bank Street, Canary Wharf, London E14 5JP",
    },
    {
        "id": 3,
        "company_name": "Zenith Infotech Solutions Pvt Ltd",
        "initial": "ZIS",
        "country": "India",
        "country_code": "+91",
        "poc_first": "Rajesh",
        "poc_last": "Sharma",
        "phone": "9811012345",
        "address": "Cyber City, Tower B, 8th Floor, DLF Phase 2, Gurugram, Haryana 122002",
    },
    {
        "id": 4,
        "company_name": "Northstar Meridian Technologies Inc",
        "initial": "NMT",
        "country": "Canada",
        "country_code": "+1",
        "poc_first": "David",
        "poc_last": "Tremblay",
        "phone": "4165550187",
        "address": "100 King Street West, Suite 5600, Toronto, ON M5X 1C9",
    },
    {
        "id": 5,
        "company_name": "Pacific Crest Advisory Group Pty Ltd",
        "initial": "PCA",
        "country": "Australia",
        "country_code": "+61",
        "poc_first": "Liam",
        "poc_last": "O'Connor",
        "phone": "298765432",
        "address": "100 Barangaroo Avenue, Tower One, Sydney, NSW 2000",
    },
    {
        "id": 6,
        "company_name": "Bavaria Industrie Automation GmbH",
        "initial": "BIA",
        "country": "Germany",
        "country_code": "+49",
        "poc_first": "Klaus",
        "poc_last": "Weber",
        "phone": "892018450",
        "address": "Willy-Brandt-Allee 4, 81829 Munich",
    },
    {
        "id": 7,
        "company_name": "Luminaire Digital Media SAS",
        "initial": "LDM",
        "country": "France",
        "country_code": "+33",
        "poc_first": "Julien",
        "poc_last": "Moreau",
        "phone": "142685500",
        "address": "12 Rond-Point des Champs-Élysées, 75008 Paris",
    },
    {
        "id": 8,
        "company_name": "Al-Futtaim Horizon Logistics FZ-LLC",
        "initial": "AHL",
        "country": "United Arab Emirates",
        "country_code": "+971",
        "poc_first": "Tariq",
        "poc_last": "Al-Mansoor",
        "phone": "43912345",
        "address": "Dubai Internet City, Building 3, Dubai",
    },
    {
        "id": 9,
        "company_name": "SingaTech Innovations Pte Ltd",
        "initial": "STI",
        "country": "Singapore",
        "country_code": "+65",
        "poc_first": "Wei",
        "poc_last": "Chen",
        "phone": "67891234",
        "address": "10 Marina Boulevard, Marina Bay Financial Centre, Singapore 018983",
    },
    {
        "id": 10,
        "company_name": "Nippon Nexus Corporation",
        "initial": "NNC",
        "country": "Japan",
        "country_code": "+81",
        "poc_first": "Kenji",
        "poc_last": "Sato",
        "phone": "355551234",
        "address": "Roppongi Hills Mori Tower, 6-10-1 Roppongi, Minato-ku, Tokyo 106-6108",
    },
    {
        "id": 11,
        "company_name": "Helvetia Analytics AG",
        "initial": "HAA",
        "country": "Switzerland",
        "country_code": "+41",
        "poc_first": "Beat",
        "poc_last": "Schneider",
        "phone": "442157890",
        "address": "Bahnhofstrasse 45, 8001 Zurich",
    },
    {
        "id": 12,
        "company_name": "Amsterdam Capital Partners BV",
        "initial": "ACP",
        "country": "Netherlands",
        "country_code": "+31",
        "poc_first": "Lars",
        "poc_last": "van der Meer",
        "phone": "205041234",
        "address": "Gustav Mahlerlaan 10, 1082 PP Amsterdam",
    },
    {
        "id": 13,
        "company_name": "Nordic Pulse Biotech AB",
        "initial": "NPB",
        "country": "Sweden",
        "country_code": "+46",
        "poc_first": "Erik",
        "poc_last": "Lindqvist",
        "phone": "812345678",
        "address": "Regeringsgatan 56, 111 56 Stockholm",
    },
    {
        "id": 14,
        "company_name": "Paulista Engenharia e Software S.A.",
        "initial": "PES",
        "country": "Brazil",
        "country_code": "+55",
        "poc_first": "Gabriel",
        "poc_last": "Santos",
        "phone": "1132547890",
        "address": "Avenida Paulista, 1374, Bela Vista, São Paulo - SP, 01310-100",
    },
    {
        "id": 15,
        "company_name": "Cape Horizon Minerals Pty Ltd",
        "initial": "CHM",
        "country": "South Africa",
        "country_code": "+27",
        "poc_first": "Sipho",
        "poc_last": "Nkosi",
        "phone": "118901234",
        "address": "1 Sandton Drive, Sandton, Johannesburg, 2196",
    },
    {
        "id": 16,
        "company_name": "Sol Azteca Telecomunicaciones S.A. de C.V.",
        "initial": "SAT",
        "country": "Mexico",
        "country_code": "+52",
        "poc_first": "Carlos",
        "poc_last": "Ramirez",
        "phone": "5552345678",
        "address": "Paseo de la Reforma 222, Cuauhtémoc, 06600 Ciudad de México",
    },
    {
        "id": 17,
        "company_name": "Milano Finanza Digitale S.p.A.",
        "initial": "MFD",
        "country": "Italy",
        "country_code": "+39",
        "poc_first": "Marco",
        "poc_last": "Rossi",
        "phone": "287654321",
        "address": "Piazza Gae Aulenti 1, 20154 Milano",
    },
    {
        "id": 18,
        "company_name": "Iberian Soluciones Cloud S.L.",
        "initial": "ISC",
        "country": "Spain",
        "country_code": "+34",
        "poc_first": "Alejandro",
        "poc_last": "Navarro",
        "phone": "917654321",
        "address": "Paseo de la Castellana 89, 28046 Madrid",
    },
    {
        "id": 19,
        "company_name": "Southern Cross AgriTech Ltd",
        "initial": "SCA",
        "country": "New Zealand",
        "country_code": "+64",
        "poc_first": "Oliver",
        "poc_last": "Hampton",
        "phone": "93021234",
        "address": "23 Customs Street East, Auckland CBD, Auckland 1010",
    },
    {
        "id": 20,
        "company_name": "Emerald Isle CyberSecurity DAC",
        "initial": "EIC",
        "country": "Ireland",
        "country_code": "+353",
        "poc_first": "Conor",
        "poc_last": "Fitzgerald",
        "phone": "16789012",
        "address": "Grand Canal Dock, 1 Grand Canal Quay, Dublin 2, D02 H2H4",
    },
]


# Word-based numbering to strictly avoid numeric digits in POC Name
WORD_NUMBERS = [
    "One", "Two", "Three", "Four", "Five",
    "Six", "Seven", "Eight", "Nine", "Ten"
]


def get_matrix_clients() -> List[Dict[str, Any]]:
    """
    Returns the complete list of 20 clients from 20 countries,
    each with 10 child POC configurations across the 10 target currencies.
    POC Names contain purely alphabetic characters (no digits): e.g. 'AGS POC One'.
    """
    clients = []
    for comp in COUNTRIES_20:
        c_id = comp["id"]
        c_name = comp["company_name"]
        initial = comp["initial"]
        country = comp["country"]
        code = comp["country_code"]
        
        pocs = []
        for p_idx, curr in enumerate(CURRENCY_CONFIGS, start=1):
            poc_name = f"{initial}_POC_{curr['code']}"
            project_title = f"{c_name} - {curr['code']} {curr['service']} Initiative"
            # Unique email alias per POC routing to qa.tekinspirations@gmail.com
            poc_email = f"qa.tekinspirations+{initial.lower()}_{curr['code'].lower()}@gmail.com"
            # Unique phone per POC so CRM does not trigger duplicate lead detection
            base_phone = comp["phone"]
            if len(base_phone) >= 4:
                poc_phone = f"{base_phone[:-2]}{p_idx:02d}"
            else:
                poc_phone = f"{base_phone}{p_idx:02d}"

            pocs.append({
                "poc_index": p_idx,
                "poc_name": poc_name,
                "email": poc_email,
                "designation": "Manager",
                "country_code": code,
                "phone": poc_phone,
                "whatsapp": poc_phone,
                "currency": curr["code"],
                "currency_symbol": curr["symbol"],
                "budget": curr["budget"],
                "service": curr["service"],
                "project_title": project_title,
            })

        clients.append({
            "client_id": c_id,
            "company_name": c_name,
            "country": country,
            "country_code": code,
            "address": comp["address"],
            "primary_poc": f"{comp['poc_first']} {comp['poc_last']}",
            "primary_phone": comp["phone"],
            "primary_email": NOTIFICATION_EMAIL,
            "pocs": pocs,
        })

    return clients


def get_client_by_id(client_id: int) -> Dict[str, Any]:
    """Retrieve client definition by ID (1 to 20)."""
    clients = get_matrix_clients()
    for c in clients:
        if c["client_id"] == client_id:
            return c
    raise ValueError(f"Client ID {client_id} not found in matrix (range: 1-20).")
