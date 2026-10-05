# MQIH - Offline Installable React + FastAPI App

This project provides a React frontend and FastAPI backend with support for **offline installation**.  
All required Python wheels and npm cache files are pre‑downloaded and stored under the `offline/` directory.

---

## 📦 Offline Setup Workflow

### 1. On a machine with internet
Download all dependencies once:

```powershell
powershell -ExecutionPolicy Bypass -File d:\MQIH\scripts\download_offline.ps1

## 2. On the offline machine
Run the install script:

powershell -ExecutionPolicy Bypass -File d:\MQIH\scripts\install_offline.ps1


MQIH/
├── backend/              # FastAPI backend
├── frontend/             # React frontend
├── offline/              # Cached packages
│   ├── wheels/           # Python wheels
│   └── npm-cache/        # Node.js cache
├── scripts/              # Offline install scripts
│   ├── download_offline.ps1
│   └── install_offline.ps1
├── sample_data/          # Example CSV data
├── schema_refe.sql       # Database schema reference
└── README.md             # Project documentation


