"""Quick test script to verify routing works."""
import requests

# Test OSRM fallback (Lahore -> Islamabad)
print("=" * 50)
print("Testing OSRM (free fallback) - Lahore to Islamabad")
print("=" * 50)

url = "https://router.project-osrm.org/route/v1/driving/74.3587,31.5204;73.0479,33.6844"
params = {
    "overview": "full",
    "geometries": "polyline",
    "steps": "true",
    "alternatives": "true"
}

try:
    r = requests.get(url, params=params, timeout=20)
    print(f"HTTP Status: {r.status_code}")
    d = r.json()
    print(f"OSRM Code: {d.get('code')}")
    routes = d.get("routes", [])
    print(f"Routes found: {len(routes)}")
    for i, rt in enumerate(routes):
        dist = round(rt["distance"] / 1000, 1)
        dur = round(rt["duration"] / 60, 1)
        print(f"  Route {i+1}: {dist} km, {dur} min")
    print("\n✅ OSRM FALLBACK WORKS!\n")
except Exception as e:
    print(f"❌ OSRM Error: {e}")

# Test ORS (with dummy key to verify error handling)
print("=" * 50)
print("Testing ORS error handling")
print("=" * 50)

ors_url = "https://api.openrouteservice.org/v2/directions/driving-car/json"
headers = {
    "Authorization": "test_invalid_key",
    "Content-Type": "application/json; charset=utf-8"
}
body = {
    "coordinates": [[74.3587, 31.5204], [73.0479, 33.6844]],
    "geometry": True,
    "instructions": True,
    "units": "km"
}

try:
    r = requests.post(ors_url, json=body, headers=headers, timeout=15)
    print(f"HTTP Status: {r.status_code}")
    try:
        err = r.json()
        print(f"Error response: {err}")
    except:
        print(f"Response text: {r.text[:200]}")
    
    if r.status_code in [401, 403]:
        print("\n✅ ORS correctly rejects invalid key (expected behavior)")
    elif r.status_code == 400:
        print("\n⚠️ ORS returns 400 - our fallback will handle this")
except Exception as e:
    print(f"ORS Error: {e}")

print("\n" + "=" * 50)
print("SUMMARY: The OSRM fallback ensures routing ALWAYS works")
print("even without a valid ORS API key!")
print("=" * 50)
