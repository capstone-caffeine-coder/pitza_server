# pitza_server

A Django-based server application for the Pitza project.

## Project Structure

```
pitza_server/
├── backend/         # Backend codes
│   └── pitza/       # Django project directory
├── data/             # Persistent data storage
│   └── db/          # MySQL database files
├── mysql/            # MySQL configuration files
├── .env              # Environment variables
├── compose.yaml      # Docker Compose configuration
└── requirements.txt  # Python dependencies
```

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. Clone the repository:

```bash
git clone https://github.com/capstone-caffeine-coder/pitza_server.git
cd pitza_server
```

2. Put '.env' in directory

3. Start the services:

```bash
docker compose up
```

The application will be available at `http://localhost:8000`

## Services

### Web Service

- Django development server running on port 8000
- Automatically reloads on code changes
- Connected to MySQL database

### Database Service

- MySQL 8.0
- Persistent storage in `data/db` directory
- Custom configuration from `mysql` directory

## Development

To stop the services:

```bash
docker compose down
```

To rebuild the services:

```bash
docker compose up --build
```

To view logs:

```bash
docker compose logs -f
```
