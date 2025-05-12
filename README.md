# open-quiz

we are inspired from opentdb.com
and some questions source we are using from them.

folder structure
<pre lang="markdown"> <code>
quiz-api/
├── .dockerignore
├── .gitignore
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── LICENSE
├── Makefile
├── README.md
├── requirements.txt
│
├── src/
|   ├── tests/
│   │   ├── conftest.py     # Pytest fixtures
│   │   ├── test_quizzes.py
│   │   └── test_auth.py
│   └── app/
│       ├── core/
│       │   ├── config.py       # Configuration settings
│       │   ├── database.py     # Database connection
│       │   └── security.py     # Authentication utils
│       │
│       ├── models/
│       │   ├── quiz.py         # Quiz models
│       │   ├── question.py     # Question models
│       │   └── base.py         # Base model
│       │
│       ├── routes/
│       │   ├── quiz.py         # Quiz endpoints
│       │   ├── auth.py         # Authentication endpoints
│       │   └── __init__.py
│       │
│       ├── services/
│       │   ├── quiz_service.py # Quiz business logic
│       │   └── auth_service.py # Authentication logic
│       │
│       ├── schemas/
│       │   ├── quiz.py         # Pydantic models for quizzes
│       │   └── user.py         # Pydantic models for users
│       │
│       ├── utils/
│       │   ├── exceptions.py   # Custom exceptions
│       │   └── helpers.py      # Helper functions
│       │
│       ├── static/             # Optional for static files
│       ├── templates/          # Optional for HTML templates
│       ├── main.py             # FastAPI app creation
│       └── __init__.py
│
├── database/
│   ├── seeders/                 # database seeders
│   └── migrations/                 # If using Alembic for DB migrations
│       └── versions/
│
└── docs/                       # Optional for documentation
    └── API_DOCS.md
</code> </pre>

Here's a comprehensive Makefile for a FastAPI/Docker project that includes common development and deployment tasks:

Key Commands Explained:

1. Essential Workflow:
makefile
build   # Rebuild containers from scratch
up      # Start the application
down    # Stop and clean up

2. Development Tools:
makefile
test    # Run tests with coverage reporting
lint    # Check code style (Black, Flake8, Isort)
format  # Auto-format code

3. Database Operations:
makefile
migrate # Apply database migrations
db-shell # Connect to PostgreSQL directly

4. Debugging:
makefile
shell   # Get bash access to web container
logs    # Follow application logs

5. Maintenance:
makefile
clean   # Remove all build artifacts and Docker items

Usage Examples:
bash
make build  # Rebuild containers after dependency changes
make up     # Start the application stack
make test   # Run all unit tests
make shell  # Access the running container

Features:

1. Self-documenting help (make help)
2. Containerized development environment
3. Consistent commands across different environments
4. Integration with code quality tools
5. Database migration support

Best Practices Included:

* Uses --rm flag for ephemeral test/lint containers
* Separate DB shell access command
* Coverage reporting for tests
* Automatic code formatting
* Proper cleanup commands
* Version-agnostic Docker Compose reference

To use this Makefile effectively:

1. Place it in your project root
2. Ensure all required tools are in your Dockerfile:
 RUN pip install black flake8 isort pytest coverage
 Make the commands executable:
 chmod +x Makefile

For generate SESSION_SECRET_KEY value in .env
<code>python3 -c "import secrets; print(secrets.token_urlsafe(32))"</code>

For generate JWT SECRET_KEY value in .env
<code>python3 -c "import secrets; print(secrets.token_urlsafe(64))"</code>

for generate CRYPTO_SECRET_KEY value in .env
<code>python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"</code>
