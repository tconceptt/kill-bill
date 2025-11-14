# Kill Bill - Subscription Manager MVP

A Django-based subscription management system for tracking clients, subscriptions, invoices, and payments.

## Project Structure

```
kill_bill/
├── manage.py                 # Django management script
├── db.sqlite3                # SQLite database (development)
├── venv/                     # Python virtual environment
├── kill_bill/                # Django project directory
│   ├── __init__.py
│   ├── settings.py           # Django settings
│   ├── urls.py               # Root URL configuration
│   ├── wsgi.py               # WSGI configuration
│   ├── asgi.py               # ASGI configuration
│   ├── requirements.txt      # Python dependencies
│   ├── core/                 # Main application
│   │   ├── models.py         # Database models
│   │   ├── views.py          # View functions
│   │   ├── forms.py          # Form definitions
│   │   ├── urls.py           # URL routing
│   │   ├── admin.py          # Django admin configuration
│   │   ├── migrations/       # Database migrations
│   │   └── management/       # Custom management commands
│   │       └── commands/
│   │           └── daily_reminders.py
│   ├── templates/            # HTML templates
│   │   ├── base.html         # Base template
│   │   ├── auth/
│   │   │   └── login.html
│   │   ├── clients/
│   │   ├── subscriptions/
│   │   ├── invoices/
│   │   ├── payments/
│   │   └── dashboard.html
│   └── static/               # Static files (CSS, JS, images)
└── README.md
```

## Features

- **Client Management**: Track company information and contact details
- **Subscription Management**: Manage subscription plans and active subscriptions
- **Invoice Management**: Generate and track invoices with status (Unpaid, Paid, Overdue)
- **Payment Tracking**: Record and monitor payment transactions
- **Dashboard**: Overview of active subscriptions, expiring subscriptions, and overdue invoices
- **Reminders**: View upcoming and overdue invoice reminders
- **Authentication**: User login/logout functionality

## Requirements

- Python 3.13+
- Django 5.2.x
- PostgreSQL (optional, SQLite used by default)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd kill_bill
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r kill_bill/requirements.txt
```

### 4. Set Up Database (Neon PostgreSQL)

This project supports both SQLite (default) and PostgreSQL. For production, we recommend using Neon PostgreSQL.

#### Option A: Using Neon PostgreSQL (Recommended for Production)

1. **Create a Neon Account and Project**
   - Go to [neon.tech](https://neon.tech) and sign up
   - Create a new project
   - Note: Neon provides connection guides for Next.js, React, and JavaScript, but for Django, you'll use the PostgreSQL connection string directly

2. **Get Your Connection String**
   - In your Neon dashboard, go to your project
   - Click on "Connection Details" or "Connection String"
   - Copy the connection string (it will look like: `postgresql://user:password@host.neon.tech/dbname?sslmode=require`)

3. **Set the DATABASE_URL Environment Variable**
   ```bash
   export DATABASE_URL="postgresql://user:password@host.neon.tech/dbname?sslmode=require"
   ```
   
   Or create a `.env` file in the project root:
   ```bash
   echo 'DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require' > .env
   ```

4. **The project will automatically use Neon** - The `settings.py` file is already configured to parse the `DATABASE_URL` and connect to PostgreSQL when it's set.

#### Option B: Using SQLite (Default for Development)

If you don't set `DATABASE_URL`, the project will use SQLite by default (no additional setup needed).

### 5. Run Migrations

**Important**: Due to the nested project structure, you need to set the `PYTHONPATH` environment variable. Make sure you're in the project root (where `manage.py` is located):

```bash
# You should already be in the kill_bill directory after cloning
export PYTHONPATH=$(pwd)/kill_bill:$PYTHONPATH
python manage.py migrate
```

### 6. Create Superuser

```bash
export PYTHONPATH=$(pwd)/kill_bill:$PYTHONPATH
python manage.py createsuperuser
```

Or create one programmatically:

```bash
export PYTHONPATH=$(pwd)/kill_bill:$PYTHONPATH
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('username', '', 'password')"
```

## Running the Project

### Development Server

**Important**: Always set the `PYTHONPATH` before running Django commands. Make sure you're in the project root:

```bash
# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH (you're already in the project root)
export PYTHONPATH=$(pwd)/kill_bill:$PYTHONPATH

# Run the server
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/`

### Quick Start Script

You can create a helper script (`run.sh`) to simplify running the server:

```bash
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH=$(pwd)/kill_bill:$PYTHONPATH
python manage.py runserver
```

Make it executable: `chmod +x run.sh`

## Database

### Location

- **Development**: `db.sqlite3` (located in the project root)
- **Production**: Can be configured via `DATABASE_URL` environment variable for PostgreSQL

### Database Configuration

The project uses SQLite by default for development. To use PostgreSQL:

1. Set the `DATABASE_URL` environment variable
2. The `settings.py` will automatically parse and configure the database connection
3. Run migrations: `python manage.py migrate`

### Database Models

- **Client**: Company information and contact details
- **SubscriptionPlan**: Subscription plan definitions (monthly/annual pricing)
- **Subscription**: Active subscriptions linked to clients
- **Invoice**: Generated invoices with status tracking
- **Payment**: Payment records linked to subscriptions

## Default Login Credentials

After creating a superuser, you can log in at `http://127.0.0.1:8000/login/`

Default superuser (if created):
- Username: `mediator`
- Password: `architecture`

## Management Commands

### Daily Reminders

Send reminder emails for upcoming and overdue invoices:

```bash
export PYTHONPATH=$(pwd)/kill_bill:$PYTHONPATH
python manage.py daily_reminders
```

## Important Notes

### Project Structure Quirk

This project has a nested structure where the Django project directory (`kill_bill/kill_bill/`) is inside the repository root. This requires:

1. Setting `PYTHONPATH` to include `kill_bill/kill_bill/` directory
2. Template paths in `settings.py` are configured as `BASE_DIR / "kill_bill" / "templates"`
3. Static files path is configured as `BASE_DIR / "kill_bill" / "static"`

### Template Syntax

This project uses Django template syntax (not Jinja2). Use `{% tag %}` instead of `{%- tag -%}`.

## URL Routes

- `/` - Dashboard
- `/login/` - Login page
- `/logout/` - Logout
- `/clients/` - Client list
- `/clients/new/` - Create client
- `/clients/<id>/` - Client detail
- `/subscriptions/` - Subscription list
- `/subscriptions/new/` - Create subscription
- `/subscriptions/<id>/` - Subscription detail
- `/invoices/` - Invoice list
- `/invoices/new/` - Create invoice
- `/invoices/<id>/` - Invoice detail
- `/payments/` - Payment list
- `/payments/new/` - Record payment
- `/reminders/` - View reminders

## Development

### Running Tests

```bash
export PYTHONPATH=$(pwd)/kill_bill:$PYTHONPATH
python manage.py test
```

### Creating Migrations

```bash
export PYTHONPATH=$(pwd)/kill_bill:$PYTHONPATH
python manage.py makemigrations
python manage.py migrate
```

### Django Admin

Access the Django admin interface at `http://127.0.0.1:8000/admin/`

## Troubleshooting

### Template Errors

If you encounter template errors, ensure:
1. Template paths in `settings.py` point to `BASE_DIR / "kill_bill" / "templates"`
2. You're using Django template syntax, not Jinja2

### Import Errors

If you see `ModuleNotFoundError: No module named 'core'`:
1. Ensure you're in the project root directory (where `manage.py` is located)
2. Set `PYTHONPATH` to include the `kill_bill/kill_bill/` directory:
   ```bash
   export PYTHONPATH=$(pwd)/kill_bill:$PYTHONPATH
   ```
3. Verify the path: `echo $PYTHONPATH`

### Database Errors

If migrations fail:
1. Check that the database file (`db.sqlite3`) has proper permissions
2. For PostgreSQL, verify the `DATABASE_URL` is correct
3. Ensure all migrations are applied: `python manage.py migrate`

## Future Updates

This README will be updated as the project evolves. Check back for:
- New features and functionality
- Deployment instructions
- API documentation
- Testing guidelines

## License

[Add your license here]

## Contact

[Add contact information here]

