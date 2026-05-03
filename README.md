# WOACC EVO Tracker

Local tracker for **Assetto Corsa EVO** with leaderboard, records and optional **WOACC global data sharing**.

---

## 🚀 Features

* 📊 Session tracking (Practice / Qualifying / Race)
* 🏁 Leaderboard per track, car and driver
* 📈 Records and statistics
* 🌍 Optional integration with **WOACC global network**
* 🔌 API Bridge for external tools (ACC_JSON_Monitor_Plus 2)
* 🧠 Automatic JSON ingestion and processing
* 🎮 Designed for **private servers and communities**

---

## 🌐 WOACC Integration

This tracker can connect to the **WOACC global ecosystem**.

* Your tracker stays **local and independent**
* You can **choose to share data**
* WOACC aggregates data across multiple communities

👉 To join the network:

* Open the tracker
* Go to **WOACC section**
* Send your public tracker URL

---

## ⚙️ Installation

### Requirements

* Python 3.10+
* Windows (tested)

### Steps

```bash
git clone https://github.com/mostrotarlo/woacc-evo-tracker.git
cd woacc-evo-tracker
pip install -r requirements.txt
```

Run:

```bash
python run.py
```

Then open:

```text
http://127.0.0.1:5055
```

---

## 🔗 API (WOACC Bridge)

Available endpoints:

```
/api/woacc/ping
/api/woacc/sessions
/api/woacc/session/<id>/original.json
```

Used by:
👉 ACC_JSON_Monitor_Plus 2

---

## 🔒 Security Model

* API access can be restricted via key
* Data sharing is **optional**
* Community page is **local-only**
* No public exposure unless configured

---

## 🤝 Contributing

Feel free to fork, improve and suggest features.

---

## 📬 Contact

Discord: **Fabio / WOACC**

---

## 📄 License

MIT License
