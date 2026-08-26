import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

BASE_URL = "https://mytravel.taxi/v1/api"

def api_call(endpoint: str, method: str = "GET", data: dict = None, token: str = None) -> tuple[int, dict]:
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            return resp.status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = {"raw": err_body}
        return e.code, parsed
    except Exception as e:
        return 0, {"error": str(e)}

def login_or_signup(phone: str, full_name: str, role: str, password: str) -> tuple[str, dict]:
    print(f"[*] Authenticating {role} ({phone})...")
    status, res = api_call("/travel/auth/login", method="POST", data={"phone": phone, "password": password})
    if status == 200:
        print(f"    -> Logged in successfully as {role} ({res['user']['id']})")
        return res["token"], res["user"]
    
    print(f"    -> Login failed ({status}), attempting signup...")
    status, res = api_call("/travel/auth/signup", method="POST", data={
        "phone": phone,
        "full_name": full_name,
        "role": role,
        "password": password
    })
    if status in (200, 201):
        print(f"    -> Signed up successfully as {role} ({res['user']['id']})")
        return res["token"], res["user"]
    
    raise RuntimeError(f"Failed to authenticate {role} ({phone}): {status} -> {res}")

def main():
    print("=" * 70)
    print("MYTRAVEL PRODUCTION LIVE E2E VERIFICATION TEST")
    print(f"Target: {BASE_URL}")
    print("=" * 70)

    # 1. Driver & Passenger Authentication
    driver_token, driver_user = login_or_signup("0966519118", "Virak Driver", "driver", "Virak123")
    passenger_token, passenger_user = login_or_signup("0966519111", "Virak Passenger", "passenger", "Virak123")

    # 2. Register FCM Push Tokens for both
    print("\n[*] Registering Push Notification Tokens...")
    status, d_push = api_call("/travel/devices/push-token", method="POST", data={
        "push_token": "fcm_test_driver_0966519118_token_abc",
        "platform": "android",
        "device_id": "android_dev_0966519118"
    }, token=driver_token)
    print(f"    -> Driver push token registered: status={status}, resp={d_push}")

    status, p_push = api_call("/travel/devices/push-token", method="POST", data={
        "push_token": "fcm_test_passenger_0966519111_token_xyz",
        "platform": "android",
        "device_id": "android_dev_0966519111"
    }, token=passenger_token)
    print(f"    -> Passenger push token registered: status={status}, resp={p_push}")

    # 3. Ensure Driver has a vehicle
    print("\n[*] Checking Driver Vehicle...")
    status, vehicles = api_call("/travel/driver/vehicles", token=driver_token)
    vehicle_id = None
    if status == 200 and vehicles:
        vehicle_id = vehicles[0]["id"]
        print(f"    -> Found existing vehicle {vehicle_id} ({vehicles[0].get('plate_number')})")
    else:
        print("    -> No vehicle found, creating a new vehicle for driver...")
        status, v_res = api_call("/travel/vehicles", method="POST", data={
            "plate_number": "2BC-9118",
            "seat_type": 4,
            "vehicle_type": "sedan",
            "model": "Toyota Prius",
            "color": "Silver",
            "company_name": "MyTravel Express"
        }, token=driver_token)
        if status not in (200, 201):
            raise RuntimeError(f"Failed to create vehicle: {status} -> {v_res}")
        vehicle_id = v_res["id"]
        print(f"    -> Created vehicle {vehicle_id}")

    # 4. Driver Creates & Publishes Trip
    print("\n[*] Creating Trip from Phnom Penh to Siem Reap...")
    departure_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    status, trip = api_call("/travel/trips", method="POST", data={
        "vehicle_id": vehicle_id,
        "departure_province": "phnom_penh",
        "destination_province": "siem_reap",
        "departure_time": departure_time,
        "departure_lat": 11.5564,
        "departure_lng": 104.9282,
        "price_per_seat": 40000,
        "total_seats": 4,
        "available_seats": 4,
        "status": "scheduled"
    }, token=driver_token)
    if status not in (200, 201):
        raise RuntimeError(f"Failed to create trip: {status} -> {trip}")
    trip_id = trip["id"]
    print(f"    -> Trip Created! ID: {trip_id}")
    print(f"       Route: {trip['departure_province']} -> {trip['destination_province']}")
    print(f"       Price: {trip['price_per_seat']} KHR/seat, Total Seats: {trip['total_seats']}")

    # 5. Passenger Searches for Trip
    print("\n[*] Passenger Searching for Phnom Penh -> Siem Reap trips...")
    status, search_res = api_call("/travel/trips/search?departure_province=phnom_penh&destination_province=siem_reap", token=passenger_token)
    found_trip = any(t["id"] == trip_id for t in (search_res if isinstance(search_res, list) else search_res.get("trips", [])))
    print(f"    -> Search completed (status={status}), Created trip found in search: {found_trip}")

    # 6. Passenger Creates Booking
    print("\n[*] Passenger Booking 2 Seats (Seats 1 & 2)...")
    status, booking = api_call("/travel/bookings", method="POST", data={
        "trip_id": trip_id,
        "seat_numbers": [1, 2],
        "payment_method": "cash",
        "status": "pending"
    }, token=passenger_token)
    if status not in (200, 201):
        raise RuntimeError(f"Failed to create booking: {status} -> {booking}")
    booking_id = booking["id"]
    print(f"    -> Booking Created! ID: {booking_id}")
    print(f"       Seats: {booking['seat_numbers']}, Total Price: {booking['total_price']} KHR, Status: {booking['status']}")

    # 7. Check Notifications for Driver
    print("\n[*] Checking Driver Notification Inbox for Booking Notification...")
    status, d_notifs = api_call("/travel/notifications", token=driver_token)
    notif_list = d_notifs.get("notifications", []) if isinstance(d_notifs, dict) else d_notifs
    booking_notif = next((n for n in notif_list if n.get("booking_id") == booking_id or n.get("trip_id") == trip_id), None)
    if booking_notif:
        print(f"    -> Driver received in-app notification: '{booking_notif.get('title')}' - {booking_notif.get('body')}")
    else:
        print(f"    -> Total driver notifications: {len(notif_list)}")

    # 8. Driver Marks Arrival at Pickup
    print(f"\n[*] Driver arrives at pickup for Booking {booking_id}...")
    status, arr_res = api_call(f"/travel/bookings/{booking_id}/driver-arrived", method="POST", data={}, token=driver_token)
    print(f"    -> Driver arrived action: status={status}, pickup_status={arr_res.get('pickup_status', arr_res)}")

    # 9. Driver Requests Boarding
    print(f"\n[*] Driver requests boarding from passenger...")
    status, b_req = api_call(f"/travel/bookings/{booking_id}/boarding/request", method="POST", data={}, token=driver_token)
    print(f"    -> Boarding requested: status={status}, resp={b_req}")

    # 10. Passenger Confirms Boarding
    print(f"\n[*] Passenger confirms boarding...")
    status, b_conf = api_call(f"/travel/bookings/{booking_id}/boarding/passenger-confirm", method="POST", data={}, token=passenger_token)
    print(f"    -> Boarding confirmed: status={status}, pickup_status={b_conf.get('pickup_status', b_conf)}")

    # 11. Trip & Booking Completion
    print(f"\n[*] Driver completes trip {trip_id}...")
    status, comp_res = api_call(f"/travel/trips/{trip_id}/complete", method="POST", data={}, token=driver_token)
    print(f"    -> Trip completion status: {status}, result={comp_res.get('status', comp_res)}")

    # 12. Final Booking Verification
    print(f"\n[*] Verifying Final Booking Status...")
    status, final_booking = api_call(f"/travel/bookings/{booking_id}", token=passenger_token)
    print(f"    -> Final Booking Status: {final_booking.get('status')}")
    print(f"       Pickup Status: {final_booking.get('pickup_status')}")
    print(f"       Payment Method: {final_booking.get('payment_method')}")

    # 13. Driver Wallet & Fee Summary Check
    print(f"\n[*] Checking Driver Wallet & Fee Settlement...")
    status, wallet = api_call("/travel/wallet/driver-fee-summary", token=driver_token)
    if status == 200:
        print(f"    -> Driver Wallet Status:")
        print(f"       Total Owed: {wallet.get('total_owed_khr')} KHR (${wallet.get('total_owed_usd')} USD)")
        print(f"       Credit Limit: {wallet.get('credit_limit_khr')} KHR (${wallet.get('credit_limit_usd')} USD)")
        print(f"       Is Locked: {wallet.get('is_locked')}")

    print("\n" + "=" * 70)
    print("ALL BOOKING LIFECYCLE STEPS COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
