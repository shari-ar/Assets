# DevOps & Deployment

## Overview

The **Assets** project uses a **monorepo** architecture to manage both backend (Django) and frontend (Next.js) applications. This guide outlines the CI/CD workflows, environment configurations, Docker setup, and deployment strategies for production and staging environments.

---

## Goals

- Streamline deployment through automation.
- Maintain consistency between development, staging, and production.
- Ensure scalability, observability, and fault tolerance.
- Simplify developer onboarding via Dockerized environments.

---

## Repository Structure

```
Assets/
├── backend/                 # Django + Django Ninja API
├── frontend/                # Next.js + HeroUI app
├── docs/                    # Documentation for contributors
├── .github/workflows/       # CI/CD pipelines
├── compose.yml              # Multi-service orchestration
├── .env.example             # Sample environment file
└── Makefile                 # Common build and test commands
```

---

## CI/CD Workflow

The project uses **GitHub Actions** for automated testing, linting, building, and deployment.

### Workflow Overview

1. **Pull Request Validation**
   - Lint backend and frontend code.
   - Run unit and integration tests.
2. **Build & Push Docker Images**
   - Tag and push images to GHCR.
3. **Deploy to Production**
   - Trigger remote deployment.

---

## Environment Configuration

All environment variables are centralized in the `.env` file.

---

## Docker Setup

Both backend and frontend are containerized for consistent environments.

---

## Local Development

### Setup

```bash
git clone https://github.com/shari-ar/Assets.git
cd Assets
cp .env.example .env
docker-compose up --build
```

Backend available at → `http://localhost:8000`  
Frontend available at → `http://localhost:3000`

### Common Commands

```bash
make test         # Run tests
make format       # Lint and format code
make migrate      # Run Django migrations
make seed         # Load seed data
```

---

## Deployment Targets

| Environment    | Platform           | Description                |
| -------------- | ------------------ | -------------------------- |
| **Staging**    | Local Docker Setup | Preview deployments for QA |
| **Production** | VPS                | Available Online           |

---

## Monitoring & Logging

| Tool           | Purpose                    |
| -------------- | -------------------------- |
| **Sentry**     | Application error tracking |
| **Prometheus** | Metrics collection         |
| **Grafana**    | Visualization and alerting |

---

## Backup & Recovery

- Automated PostgreSQL backups using `pg_dump`.
- Daily snapshot retention policy for 30 days.
- Restore tested quarterly via CI scripts.

**Example Backup Script:**

```bash
pg_dump $DATABASE_URL > backup_$(date +%F).sql
```

---

## Security Considerations

- Use **Nginx** for reverse proxy.
- Use **Docker secrets** for credentials instead of plain `.env`.
- Enforce least privilege on database users.
- Enable **firewall rules** and **VPC isolation**.
- Use **fail2ban** or **UFW** for SSH protection.
- Auto-renew SSL certificates via **Let’s Encrypt**.

---

## Future Improvements

- Horizontal scaling via Kubernetes.
- Zero-downtime migrations.
- Canary deployments and rollback automation.
- Terraform for infrastructure as code (IaC).
