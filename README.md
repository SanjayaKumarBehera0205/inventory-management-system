# Inventory Management System

A secure, portfolio-ready inventory REST API built with FastAPI, SQLAlchemy, JWT authentication, PostgreSQL, and Docker.

## Features

- User registration and JWT authentication
- Product CRUD with unique SKU validation
- Category and supplier management
- Stock-in, stock-out, and manual adjustment transactions
- Complete stock movement audit trail
- Protection against negative inventory
- Low-stock filtering and alerts
- Product search, filters, and pagination
- Dashboard with stock value and inventory statistics
- SQLite for quick local setup
- PostgreSQL and Docker support
- Automated tests and Swagger documentation

## Technology

Python 3.12, FastAPI, SQLAlchemy 2, Pydantic, SQLite/PostgreSQL, PyJWT, Argon2, Pytest, and Docker.

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open Swagger UI at http://127.0.0.1:8000/docs.

Generate a secure `SECRET_KEY` with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Main API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register` | Register a user |
| POST | `/api/v1/auth/login` | Get a JWT token |
| GET | `/api/v1/dashboard` | Inventory summary |
| POST/GET | `/api/v1/categories` | Create or list categories |
| POST/GET | `/api/v1/suppliers` | Create or list suppliers |
| POST/GET | `/api/v1/products` | Create or search products |
| GET/PATCH/DELETE | `/api/v1/products/{id}` | Manage one product |
| POST | `/api/v1/stock-movements` | Add, remove, or adjust stock |
| GET | `/api/v1/stock-movements` | View the audit trail |

Login uses form data: enter the email in the `username` field.

## Stock movement rules

- `stock_in`: adds the provided quantity.
- `stock_out`: subtracts the provided quantity and rejects insufficient stock.
- `adjustment`: sets inventory to the provided absolute quantity.

Each movement records the previous quantity, new quantity, user, note, and timestamp.

## Run tests

```bash
pytest
```

## Docker with PostgreSQL

```bash
docker compose up --build
```

Then visit http://localhost:8000/docs.

## Suggested improvements

- Role-based access control
- Barcode scanning
- Purchase and sales orders
- Warehouse locations
- CSV import/export
- Alembic migrations
- Email low-stock notifications
- GitHub Actions deployment

## License

MIT
