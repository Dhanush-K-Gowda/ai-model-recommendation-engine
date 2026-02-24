# Model Recommendation Engine

An AI-powered system that analyzes LLM usage patterns and recommends optimal model switches to reduce costs, improve performance, or enhance capabilities.

## Overview

This project is a full-stack application consisting of:

- **Backend**: Django (Python) - REST API for data ingestion, analysis, and recommendations
- **Frontend**: React + TypeScript + Vite - Dashboard for viewing applications, traces, and recommendations
- **Database**: PostgreSQL/SQLite - Stores models, traces, usage analytics, and recommendations

## Features

### Core Functionality

1. **LLM Trace Ingestion**
   - Single and bulk trace ingestion API endpoints
   - Automatic model name resolution
   - Token estimation and cost calculation

2. **Usage Analysis**
   - Aggregates usage patterns per application
   - Calculates average costs, tokens, latency
   - Identifies tool usage requirements

3. **Model Recommendations**
   - Generates intelligent model switch recommendations
   - Considers: cost savings, performance, capabilities, benchmarks
   - Supports multiple recommendation types:
     - Cost Savings (cheaper alternatives)
     - Performance (faster models)
     - Enhanced Capabilities (more features)
     - Balanced Improvements

4. **Model Catalog**
   - Stores AI models from multiple providers (OpenAI, Anthropic, Google, Azure)
   - Tracks pricing, context windows, capabilities
   - Benchmark scores for quality assessment

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/traces` | POST | Ingest single trace |
| `/api/traces/bulk` | POST | Bulk ingest traces |
| `/api/applications` | GET | List all applications |
| `/api/applications/<id>` | GET | Application details |
| `/api/recommendations` | GET/POST | List or generate recommendations |
| `/api/recommendations/generate` | POST | Generate for specific app |
| `/api/dashboard/stats` | GET | Dashboard statistics |

## Architecture

```
model-recommendation-engine/
├── backend/
│   ├── engine/              # Main Django app
│   │   ├── models.py       # Database models
│   │   ├── views.py        # API views
│   │   ├── serializers.py  # Data validation
│   │   ├── urls.py         # URL routing
│   │   └── services/      # Business logic
│   │       ├── recommendation_engine.py
│   │       ├── usage_analyzer.py
│   │       ├── model_resolver.py
│   │       └── model_tester.py
│   ├── backend/            # Django project settings
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/          # Dashboard pages
│   │   ├── components/     # Reusable components
│   │   └── lib/           # Utilities & API client
│   ├── package.json
│   └── vite.config.ts
│
└── scripts/                # Utility scripts
```

### Database Models

- **Provider** - AI model providers (OpenAI, Anthropic, Google)
- **AIModel** - Individual models with capabilities, pricing, benchmarks
- **Pricing** - Token pricing per model
- **Application** - User applications using LLMs
- **LLMTrace** - Individual API call records
- **UsageAnalysis** - Aggregated usage statistics
- **Recommendation** - Generated model switch recommendations

## Current Issues & Improvements

### Critical Issues (FIXED)

1. **~~Performance - N+1 Queries~~** ✅ FIXED
   - Views now use Django ORM `.aggregate()` for cost/token calculations
   - Location: `views.py:applications_list`, `application_detail`, `dashboard_stats`

2. **~~Division by Zero~~** ✅ FIXED
   - Added null/zero checks in recommendation engine
   - Location: `recommendation_engine.py:235, 241-243`

3. **~~Performance - Inefficient Bulk Ingestion~~** ✅ FIXED
   - Now uses `bulk_create()` for batch trace creation
   - Location: `serializers.py:339`

4. **~~Silent Error Handling~~** ✅ FIXED
   - Bulk ingestion now collects and reports validation errors in response
   - Location: `serializers.py:335, 342`, `views.py:83-99`

5. **Hardcoded Provider Names**
   - Provider names hardcoded in recommendation engine
   - Should be configurable via database

6. **Database-Specific Code**
   - Separate SQLite vs PostgreSQL logic for JSON fields
   - Should use database-agnostic approaches or proper migrations

7. **Missing Pagination**
   - Endpoints return unlimited results
   - Should add pagination for large datasets

8. **Inconsistent Type Handling**
   - Mixing Decimal and Float for financial data
   - Can cause precision issues

### Architecture Improvements

9. **Add Celery for Background Tasks**
   - Usage analysis and recommendation generation should run async
   - Current synchronous processing blocks API

10. **Implement Caching**
    - Cache frequently accessed data (models, providers)
    - Use Redis for distributed caching

11. **Add Rate Limiting**
    - Protect ingestion endpoints from abuse
    - Use Django-ratelimit or custom middleware

12. **Comprehensive Testing**
    - Add unit tests for services
    - Add integration tests for API endpoints

13. **API Documentation**
    - Add OpenAPI/Swagger documentation
    - Use drf-spectacular for auto-generated docs

### Potential Bugs

13. **~~Division by Zero~~** ✅ FIXED
    - `recommendation_engine.py` - added proper null/zero checks

14. **~~Unused Variables~~** ✅ FIXED
    - `views.py` - optimized queries to use DB aggregation

### Missing Features

15. **Auto Category Derivation**
    - Application categories should auto-update from assigned model

16. **Recommendation Testing**
    - Integrate model testing/validation workflow

17. **Audit Logging**
    - Track changes to recommendations and applications

## Optimization Opportunities

### Database Optimizations

1. **Add Database Indexes**
   - Review query patterns and add composite indexes
   - Consider partial indexes for filtered queries

2. **Query Optimization**
   - Use `select_related()` and `prefetch_related()` consistently
   - Avoid `count()` on large querysets - use estimated counts

3. **Connection Pooling**
   - Configure database connection pooling for production
   - Use pgbouncer for PostgreSQL

### Code Optimizations

4. **Bulk Operations**
   - Use `bulk_create()` for trace ingestion
   - Use `bulk_update()` for recommendation updates

5. **Lazy Evaluation**
   - Use Django QuerySet chaining
   - Avoid premature evaluation

### Scalability

6. **Horizontal Scaling**
   - Stateless API design for easy scaling
   - Separate read/write concerns

7. **Data Archival**
   - Archive old traces to separate storage
   - Implement data retention policies

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (recommended) or SQLite

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Ingest Sample Data

```bash
# Using Django shell
python manage.py shell

# Import models
from engine.management.commands.import_models import Command
cmd = Command()
cmd.handle()
```

## Environment Variables

### Backend

```
DATABASE_URL=postgres://user:pass@localhost:5432/recommendations
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Frontend

```
VITE_API_URL=http://localhost:8000/api
```

## License

MIT License
