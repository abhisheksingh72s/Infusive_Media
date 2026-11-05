import os
import requests
from dotenv import load_dotenv

load_dotenv()
BASE = "https://infusive-back.jobvritta.com/api"

res = requests.post(f"{BASE}/user/login", json={"email": "Admin@infusive.com", "password": "123456"})
token = res.json().get("token")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Test different date ranges
ranges = [
    ("2026-09-01", "2026-09-30"),
    ("2026-09-01", "2026-09-15"),
    ("2026-09-16", "2026-09-29"),
    ("2026-01-01", "2026-12-31"),
    ("2025-01-01", "2026-12-31")
]

for start, end in ranges:
    params = {
        "lazyParams": '{"first":0,"rows":50,"page":0,"sortField":"","sortOrder":1}',
        "search": "",
        "filter": "{}",
        "timezone": "Asia/Calcutta",
        "startDate": start,
        "endDate": end
    }
    r = requests.get(f"{BASE}/SourceWiseReport", headers=headers, params=params)
    data = r.json().get("data", [])
    total_leads = sum(item.get("totalLeads", 0) for item in data)
    print(f"Date Range {start} -> {end} | Total Leads in Response: {total_leads}")
    for item in data:
        if item.get("totalLeads", 0) > 0:
            print(f"   Source: {item.get('sourceName')} -> Total Leads: {item.get('totalLeads')}, Won: {item.get('won')}")
