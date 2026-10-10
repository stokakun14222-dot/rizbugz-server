# RizBugz Server

Backend server untuk APK RizBugz.

## Deploy ke Railway

1. Upload repo ini ke GitHub
2. Connect ke Railway
3. Deploy otomatis

## API Endpoints

- GET / → status server
- POST /otp → OTP bomb (body: {phone, count})
- POST /spam → spam (body: {phone, count, msg})
- GET /status/{task_id} → cek progress
- POST /cancel/{task_id} → stop task
- GET /ping → ping server
