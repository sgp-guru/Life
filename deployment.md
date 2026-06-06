# LifeLink - Deployment Guide

This document provides step-by-step instructions to set up **LifeLink** both locally for development and on a production server.

---

## Step 1: Prerequisites

Ensure you have the following installed:
- **Python 3.9+** → `python --version`
- **pip** (Python package manager) → `pip --version`
- A **Google Firebase account** → [console.firebase.google.com](https://console.firebase.google.com)
- A modern web browser (Chrome recommended)

---

## Step 2: Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com) and click **Add Project**.
2. Name the project `LifeLink` and click **Continue**.
3. Disable Google Analytics (optional) and click **Create Project**.

### 2a. Enable Firebase Authentication
1. In the Firebase console, click **Authentication** in the left sidebar.
2. Click **Get Started**.
3. Under **Sign-in method**, enable **Email/Password** and click **Save**.

### 2b. Create Firestore Database
1. Click **Firestore Database** in the left sidebar.
2. Click **Create Database**.
3. Choose **Start in test mode** (we will add rules later) and click **Next**.
4. Select your preferred location (e.g., `asia-south1` for India) and click **Enable**.

### 2c. Generate Service Account Credentials
1. In the Firebase Console, click the **gear icon ⚙️** next to "Project Overview".
2. Click **Project Settings**.
3. Navigate to the **Service accounts** tab.
4. Click **Generate new private key** and confirm.
5. A JSON file will be downloaded.
6. **Rename this file to `firebase_credentials.json`** and place it in the project root directory:
   ```
   c:\Users\gurup\Desktop\blood\firebase_credentials.json
   ```

> ⚠️ **IMPORTANT:** Never commit `firebase_credentials.json` to a public Git repository. Add it to `.gitignore`.

### 2d. Get Your Firebase Web API Key
1. In **Project Settings**, click the **General** tab.
2. Scroll to **Your apps** section. If no app exists, click **Add App** → choose **Web (</>)**.
3. Register the app, and note the `apiKey` value.
4. Set it as the `FIREBASE_API_KEY` environment variable (see Step 4).

---

## Step 3: Local Development Setup

### 3a. Navigate to the Project Directory
```powershell
cd c:\Users\gurup\Desktop\blood
```

### 3b. Create and Activate a Virtual Environment
```powershell
# Create environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
.\venv\Scripts\activate.bat

# Activate (macOS/Linux)
source venv/bin/activate
```

### 3c. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3d. Configure Environment Variables

**Option A - Inline for quick testing (Windows PowerShell):**
```powershell
$env:FIREBASE_API_KEY = "YOUR_FIREBASE_WEB_API_KEY_HERE"
```

**Option B - Create a `.env` file in the project root:**
```
FIREBASE_API_KEY=YOUR_FIREBASE_WEB_API_KEY_HERE
```
Then install `python-dotenv` and load it in `app.py` if desired.

### 3e. Run the Application
```bash
python app.py
```

You will see output like:
```
Firebase Admin SDK initialized successfully in PRODUCTION mode.
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

Open your browser and navigate to: **http://127.0.0.1:5000**

---

## Step 4: Apply Firestore Security Rules

1. In the Firebase Console, go to **Firestore Database** → **Rules** tab.
2. Replace the existing rules with the contents of your `firestore.rules` file:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    function isAuthenticated() {
      return request.auth != null;
    }
    function isAdmin() {
      return isAuthenticated() && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
    }
    match /users/{userId} {
      allow read: if isAuthenticated() && (request.auth.uid == userId || isAdmin());
      allow write: if isAuthenticated() && (request.auth.uid == userId || isAdmin());
    }
    match /donors/{donorId} {
      allow read: if isAuthenticated();
      allow write: if isAuthenticated() && (request.auth.uid == donorId || isAdmin());
    }
    match /blood_requests/{requestId} {
      allow read: if true;
      allow create: if isAuthenticated();
      allow update, delete: if isAdmin();
    }
  }
}
```

3. Click **Publish**.

---

## Step 5: Create the First Admin User

After signing up via the LifeLink `/register` page:

1. Open the [Firebase Console](https://console.firebase.google.com) → **Firestore Database** → `users` collection.
2. Find your newly created user document (identified by UID).
3. Edit the `role` field and change its value from `"user"` to `"admin"`.
4. The next time you log in, the Admin Dashboard tab will appear in the navbar.

---

## Step 6: Deploy to Production (Render)

[Render](https://render.com) is a free-tier cloud platform ideal for Flask applications.

### 6a. Create a `Procfile` in the project root:
```
web: gunicorn app:app
```

### 6b. Install gunicorn:
```bash
pip install gunicorn
pip freeze > requirements.txt
```

### 6c. Push to GitHub:
```bash
git init
git add .
git commit -m "Initial LifeLink commit"
git remote add origin https://github.com/YOUR_USERNAME/lifelink.git
git push -u origin main
```

> Add `firebase_credentials.json` and `.env` to `.gitignore`:
> ```
> firebase_credentials.json
> .env
> venv/
> __pycache__/
> *.db
> ```

### 6d. Deploy on Render:
1. Go to [render.com](https://render.com) and sign up with GitHub.
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository.
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `gunicorn app:app`
6. Under **Environment** → Add the following:
   - `FIREBASE_API_KEY` → Your Firebase Web API Key
   - `FIREBASE_CREDENTIALS_JSON` → Paste the entire JSON content of `firebase_credentials.json`
7. Click **Create Web Service**.

> Note: For production, update `app.py` to read credentials from the environment variable string instead of a file, using `json.loads(os.environ.get('FIREBASE_CREDENTIALS_JSON'))`.

---

## Step 7: Alternative Deploy - Railway

[Railway](https://railway.app) supports Flask natively with zero configuration.

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

Set environment variables via the Railway Dashboard → **Variables** tab.

---

## Testing Locally Without Firebase

The app ships with a **Simulated Mode** that runs automatically if `firebase_credentials.json` is not present. In this mode:

| Test Account | Email | Password |
|---|---|---|
| Admin | admin@lifelink.org | admin123 |
| Donor 1 | john@gmail.com | password123 |
| Donor 2 | jane@gmail.com | password123 |

> In Simulated Mode, all data is stored in-memory and resets when the server restarts.
