# DETECTIFY v1.0.0

🎉 **Initial Release**

We are excited to announce the first release of DETECTIFY! This version includes the core foundation of the application and key features.

## 🚀 Features

- **User Authentication**: Secure user registration and login using JWT.
- **Analysis Module**: Core functionality for data analysis.
- **Payment Integration**: Payment processing endpoints.
- **Infrastructure**: Docker support for easy deployment.
- **Database**: SQLite/PostgreSQL support with migration capabilities.

## 🛠️ Tech Stack

- **Framework**: Flask
- **Database**: SQLAlchemy
- **Authentication**: Flask-JWT-Extended
- **deployment**: Docker

## 📦 Installation

1.  Clone the repository.
2.  Set up the environment variables:
    - Copy `.env.example` to `.env`: `cp .env.example .env`
    - Open `.env` and fill in your configuration (database, API keys, etc).
3.  Run `flask db upgrade` to initialize the database.
4.  Start the application with `flask run` or use Docker.

Thank you for using DETECTIFY!
