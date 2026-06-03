#!/bin/bash
# scripts/init-git.sh

# Initialize git repository
echo "Initializing git repository..."
git init

# Add all files
echo "Adding files to git..."
git add .

# Initial commit
echo "Creating initial commit..."
git commit -m "feat: initial project structure

- Backend: FastAPI + SQLAlchemy + Celery
- Frontend: React + TypeScript + Zustand
- Database: PostgreSQL + Redis
- Deployment: Docker + Nginx
- Documentation: Technical design document"

echo "✅ Git repository initialized successfully!"
echo ""
echo "Next steps:"
echo "1. Create a remote repository on GitHub"
echo "2. Add remote: git remote add origin <your-repo-url>"
echo "3. Push: git push -u origin main"
