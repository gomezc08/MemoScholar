# MemoScholar - AI Assistant Guide

## Project Overview
MemoScholar is a research and study resource gathering application that helps users collect and manage resources for their academic work. It's a fullstack application with a React + TypeScript frontend and a Python Flask backend.

Full tech spec: https://docs.google.com/document/d/1EDiuOM7pzMlwyO4g-ZQU2VtMs2yAtt-3llWDrcgQpJQ/edit?usp=sharing

## CRITICAL SECURITY RULES

### NEVER Check or Read .env Files
**IMPORTANT**: DO NOT read, inspect, or access any `.env` files in this codebase. These files contain sensitive API keys, database credentials, and other secrets. The `.env` file is in the `.gitignore` and should NEVER be examined or modified by AI assistants.

If you need to understand environment variables:
- Check `backend/src/config/constants.py` for how environment variables are used
- Refer to documentation or ask the user about required variables
- NEVER read the actual `.env` file

## Architecture

### Frontend (`frontend/memo-scholar/`)
- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with shadcn/ui components
- **UI Library**: Radix UI primitives
- **Animations**: Framer Motion
- **Icons**: Lucide React

**Key Frontend Files:**
- `src/pages/` - Main application pages (App.tsx, Project.tsx, HomeScreen.tsx)
- `src/components/ui/` - Reusable UI components (shadcn/ui based)
- `src/lib/api.ts` - API client for backend communication
- `src/lib/dataTransformers.ts` - Data transformation utilities
- `src/types/index.ts` - TypeScript type definitions

### Backend (`backend/`)
- **Framework**: Python Flask
- **Database**: PostgreSQL
- **AI/ML**: OpenAI API integration, text embeddings
- **Content Generation**: Paper and YouTube video generation
- **Recommendation System**: Jaccard coefficient-based similarity

**Key Backend Files:**
- `run_server.py` - Flask server entry point
- `src/routes/` - API route handlers (user_routes, submission_routes, like_dislike_routes)
- `src/db/` - Database connection and CRUD operations
  - `connector.py` - Database connection management
  - `db_crud/` - Database operations (insert, select, change)
  - `tables.sql` - Database schema
- `src/generate_content/` - Content generation logic
  - `create_query.py` - Query generation
  - `paper_generator.py` - Academic paper recommendations
  - `youtube_generator.py` - YouTube video recommendations
- `src/jaccard_coefficient/` - Recommendation algorithm
  - `features.py` - Feature extraction
  - `jaccard_papers.py` - Paper similarity calculation
  - `jaccard_videos.py` - Video similarity calculation
- `src/text_embedding/` - Text embedding functionality
- `src/openai/` - OpenAI API client
- `src/task_manager.py` - Background task management
- `src/utils/logging_config.py` - Logging configuration

## Development Workflow

### Prerequisites
- Node.js >= 22.19.0, npm >= 11.6.0
- Python 3.8+ with pip
- PostgreSQL database

### Quick Start Commands
```bash
# Install all dependencies
npm run install:all

# Run both frontend and backend
npm run dev

# Run frontend only
npm run dev:frontend

# Run backend only
npm run dev:backend

# Build frontend
npm run build

# Preview production build
npm run preview
```

### Development Servers
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000

## Coding Conventions

### TypeScript/React
- Use TypeScript for all new frontend code
- Follow React functional components with hooks
- Use Tailwind CSS classes for styling
- shadcn/ui components are located in `src/components/ui/`
- Keep components modular and reusable
- Type definitions should be in `src/types/index.ts`

### Python
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Keep route handlers in `src/routes/`
- Database operations should be in `src/db/db_crud/`
- Utility functions should be properly organized in relevant modules

### File Organization
- Frontend components: `frontend/memo-scholar/src/components/ui/`
- Frontend pages: `frontend/memo-scholar/src/pages/`
- Backend routes: `backend/src/routes/`
- Backend database operations: `backend/src/db/db_crud/`
- Backend business logic: Organized by feature in `backend/src/`

## Important Notes for AI Assistants

### When Making Changes
1. Always read existing files before modifying them
2. Follow the established patterns in the codebase
3. Test API changes on both frontend and backend
4. Ensure TypeScript types are properly defined
5. Database schema changes should be reflected in `tables.sql`

### Security Considerations
- NEVER read or access `.env` files
- Avoid hardcoding sensitive information
- Use environment variables through the config system
- Be aware of OWASP top 10 vulnerabilities (XSS, SQL injection, etc.)

### Database Operations
- All database operations should go through the CRUD functions in `backend/src/db/db_crud/`
- Don't write raw SQL queries outside of the db_crud module
- Use proper connection pooling through `connector.py`

### API Development
- Backend routes should return consistent JSON responses
- Use proper HTTP status codes
- Frontend API calls should go through `src/lib/api.ts`
- Handle errors gracefully on both frontend and backend

### Recommendation System
- The system uses Jaccard coefficient for similarity matching
- Features are extracted in `jaccard_coefficient/features.py`
- Separate implementations for papers and videos
- Text embeddings are used for semantic similarity

## Technology Stack Summary

**Frontend:**
- React 19
- TypeScript 5.8
- Vite 7
- Tailwind CSS
- shadcn/ui
- Radix UI
- Framer Motion
- Lucide React

**Backend:**
- Python 3.8+
- Flask
- PostgreSQL
- OpenAI API
- Text embeddings
- Jaccard coefficient algorithm

**Development:**
- ESLint for code linting
- Concurrently for running multiple processes
- Git for version control

## Common Patterns

### Adding a New Route
1. Create route handler in `backend/src/routes/`
2. Add database operations in `backend/src/db/db_crud/` if needed
3. Update frontend API client in `src/lib/api.ts`
4. Update TypeScript types in `src/types/index.ts`

### Adding a New UI Component
1. Create component in `frontend/memo-scholar/src/components/ui/`
2. Use Tailwind CSS and shadcn/ui patterns
3. Export from component file
4. Add TypeScript props interface

### Database Schema Updates
1. Update `backend/src/db/tables.sql`
2. Update corresponding CRUD operations
3. Update backend route handlers
4. Update frontend types and API calls

## Notes
- CSS tooling (Tailwind, PostCSS, Autoprefixer) is pre-configured
- The project uses monorepo structure with separate frontend/backend folders
- All dependencies are managed through npm (frontend) and pip (backend)
- The application runs both servers concurrently in development mode
