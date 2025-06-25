
# 📚 Online Bookstore Web App

A cloud-based bookstore web application built with **Flask** and **MySQL**, deployed using **Docker** on **Google Cloud Run**, and connected to **Cloud SQL**.

---

## 🌐 Live Application

👉 [https://bookstore-612587411481.asia-south1.run.app](https://bookstore-612587411481.asia-south1.run.app)

---

## 🚀 Key Features

- 👤 User Registration & Login (with password hashing)
- 📖 Browse and Search Books
- 🛒 Add to Cart & Checkout
- 🗃️ SQLAlchemy ORM with connection pooling
- 🌍 Fully deployed using Docker + Cloud Run

---

## 🛠️ Technologies Used

### 📌 Backend
- Python 3.11
- Flask 2.0.1
- SQLAlchemy + PyMySQL
- Gunicorn

### 📌 Frontend
- HTML5, CSS3 (Jinja2 Templates)

### 📌 Cloud (GCP)
- Cloud Run
- Cloud SQL (MySQL)
- Cloud Build
- Artifact Registry
- IAM & Cloud Shell

---

## 📦 Folder Structure

```
bookstore/
├── main.py
├── requirements.txt
├── Dockerfile
├── runtime.txt
├── Procfile
├── templates/
│   ├── home.html
│   ├── books.html
│   └── ...
├── static/
│   └── css/
```

---

## 🔧 Deployment on GCP (Steps)

1. **Build Docker Image**
```bash
gcloud builds submit --tag asia-south1-docker.pkg.dev/YOUR_PROJECT/bookstore-gcp/bookstore-app
```

2. **Deploy to Cloud Run**
```bash
gcloud run deploy bookstore   --image asia-south1-docker.pkg.dev/YOUR_PROJECT/bookstore-gcp/bookstore-app   --region asia-south1   --allow-unauthenticated   --set-env-vars "DB_HOST=YOUR_DB_IP,DB_USER=root,DB_PASS=yourpass,DB_NAME=bookstore_db,SECRET_KEY=secret"
```

---

## 📊 View Database in Cloud SQL

1. Go to: [https://console.cloud.google.com/sql](https://console.cloud.google.com/sql)
2. Select your SQL instance → Click "Connect using Cloud Shell"
3. Run:
```sql
USE bookstore_db;
SHOW TABLES;
SELECT * FROM users;
SELECT * FROM books;
```

---

## 📍 GitHub Workflow Used

- ✅ Version control with Git
- ✅ Commit, push, and pull on GitHub
- ✅ README documentation
- ✅ GitHub repo for deployment source

---

## 🙋‍♀️ Author

**Diksha Parulekar**  
Second Year Computer Engineering Student  
Built for Cloud Computing mini-project ☁️

---

## 📬 Feedback

Feel free to ⭐ the repo or [raise an issue](https://github.com/your-username/bookstore-gcp/issues) if you'd like to contribute or suggest improvements.
