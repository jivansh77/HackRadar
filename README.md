# Hackathon Aggregator

A web application that aggregates upcoming hackathons from multiple platforms (Unstop, Devfolio, and Devpost) and displays them in real-time. The website focuses on hackathons in Mumbai but also includes national-level hackathons. Users receive push notifications when new hackathons are added.

## Features

- **Hackathon Aggregation**: Scrapes hackathon data from Unstop, Devfolio, and Devpost
- **Real-Time Updates**: Automatically updates the list of hackathons as new ones are added
- **Notifications**: Sends push notifications to users when new hackathons are added
- **User-Friendly Frontend**: Built with Next.js and shadcn UI
- **Filtering**: Filter hackathons by location, date, and source platform

## Tech Stack

### Frontend
- **Framework**: Next.js
- **UI Library**: shadcn
- **Notifications**: Firebase Cloud Messaging (FCM)

### Backend
- **Framework**: FastAPI (Python)
- **Web Scraping**: BeautifulSoup, Selenium
- **Database**: PostgreSQL
- **Task Scheduler**: Celery with Redis

## Getting Started

### Prerequisites
- Node.js (v18+)
- Python (v3.8+)
- PostgreSQL
- Redis

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   export DATABASE_URL="postgresql://username:password@localhost/hackathon_db"
   export REDIS_URL="redis://localhost:6379/0"
   export FIREBASE_CREDENTIALS_PATH="path/to/firebase-credentials.json"
   ```

5. Initialize the database:
   ```
   python -m app.db.init_db
   ```

6. Start the FastAPI server:
   ```
   uvicorn app.main:app --reload
   ```

7. Start the Celery worker:
   ```
   celery -A app.worker worker --loglevel=info
   ```

8. Start the Celery beat scheduler:
   ```
   celery -A app.worker beat --loglevel=info
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Set up environment variables:
   Create a `.env.local` file with:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_firebase_auth_domain
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_firebase_project_id
   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_firebase_messaging_sender_id
   NEXT_PUBLIC_FIREBASE_APP_ID=your_firebase_app_id
   ```

4. Start the development server:
   ```
   npm run dev
   ```

## Firebase Setup

1. Create a Firebase project at [https://console.firebase.google.com/](https://console.firebase.google.com/)
2. Set up Firebase Cloud Messaging (FCM)
3. Download the service account key file and save it as `firebase-credentials.json` in the backend directory
4. Configure the web app to use Firebase

## License

This project is licensed under the MIT License - see the LICENSE file for details. 