# FastAPI Template

![Tests](https://github.com/yourusername/fastapi-template/workflows/Tests/badge.svg)
![Security Analysis](https://github.com/yourusername/fastapi-template/workflows/Security%20Analysis/badge.svg)
![Deploy](https://github.com/yourusername/fastapi-template/workflows/Deploy/badge.svg)

A modern, production-ready template for FastAPI projects with authentication, CRUD, caching, rate limiting, and more.

## Features

- **FastAPI Framework**: High performance, easy to learn, fast to code
- **JWT Authentication**: Secure authentication with refresh tokens
- **RBAC**: Role-based access control
- **PostgreSQL & MySQL**: Support for multiple databases
- **SQLAlchemy ORM**: Database ORM with latest SQLAlchemy 2.0 syntax
- **Alembic Migrations**: Database versioning and migrations
- **Pydantic Validation**: Schema validation with Pydantic v2
- **OpenAPI Documentation**: Auto-generated API documentation
- **Redis Caching**: High-performance caching
- **Rate Limiting**: Protection against abuse
- **Docker**: Containerization for development and production
- **CI/CD**: GitHub Actions workflows for testing and deployment
- **Logging**: Structured JSON logging
- **Testing**: Pytest configuration with coverage reports
- **Code Quality**: Black, Flake8, mypy, isort configuration
- **Security**: Security scanning and best practices

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11 or higher (for local development)
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Ibrahimzongo/fastapi-template.git
cd fastapi-template
```

2. Create a `.env` file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the development environment:
```bash
docker-compose up --build
```

4. Access the API at http://localhost:8000

5. Access the API documentation at http://localhost:8000/docs

### Local Development

For local development without Docker:

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/dev.txt

# Set environment variables
export DATABASE_TYPE=postgresql
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_USER=postgres
export DATABASE_PASSWORD=password123
export DATABASE_NAME=fastapi_db
export SECRET_KEY=your-secret-key

# Run the application
uvicorn src.main:app --reload
```

## Database Migrations

To manage database migrations:

```bash
# Initialize the database
python scripts/migrate.py init

# Create a new migration
python scripts/migrate.py create --message "description"

# Apply migrations
python scripts/migrate.py migrate

# Revert migrations
python scripts/migrate.py rollback
```

See [migrations documentation](docs/migrations.md) for more information.

## Authentication

The API uses JWT tokens for authentication with refresh token mechanism.

```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "username",
    "password": "password123",
    "full_name": "User Name"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=username&password=password123"

# Access protected endpoint
curl -X GET http://localhost:8000/api/v1/posts/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Refresh token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

## Caching

The API uses Redis for caching:

- Automatic caching for GET endpoints (posts, tags)
- Cache invalidation on POST, PUT, DELETE requests
- Configurable cache expiration

See [caching documentation](docs/caching.md) for more information.

## CI/CD

This template includes GitHub Actions workflows for:

- Running tests and code quality checks
- Security scanning
- Building and pushing Docker images
- Automated deployment to staging and production

See [CI/CD documentation](docs/ci-cd.md) for more information.

## Project Structure

```
fastapi-template/
├── .github/                   # GitHub Actions workflows
├── alembic/                   # Database migrations
├── docker/                    # Docker configurations
│   ├── dev/                   # Development Docker config
│   └── prod/                  # Production Docker config
├── src/                       # Application source code
│   ├── api/                   # API routes and endpoints
│   ├── core/                  # Core configurations
│   ├── db/                    # Database models and repositories
│   ├── models/                # SQLAlchemy models
│   └── schemas/               # Pydantic schemas
├── tests/                     # Test suite
├── scripts/                   # Utility scripts
└── docs/                      # Documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.