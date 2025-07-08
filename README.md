# Sertifikatet - Driving Theory Platform

A modern, comprehensive web application for Norwegian driving theory test preparation, featuring AI-powered personalization, gamification, and extensive learning tools.

## 🚀 Project Overview

Sertifikatet is an all-in-one driving theory platform that helps users pass their Norwegian driver's theory test through:

- Interactive quizzes with detailed explanations
- Video learning with checkpoints
- Gamification with achievements and leaderboards
- ML-powered adaptive learning
- Progressive Web App (PWA) support
- Comprehensive subscription system

## 🏗️ Infrastructure & Deployment

### Production Setup

- **Domain**: [sertifikatet.no](https://sertifikatet.no)
- **Hosting**: Windows Desktop (32GB RAM, D: drive storage)
- **Tunnel**: Cloudflare Tunnel (automatic SSL, DDoS protection)
- **Process Management**: NVVM (Flask auto-restart)
- **Database**: MySQL on Windows desktop
- **CI/CD**: GitHub Actions with self-hosted runner

### Development Workflow

1. **MacBook**: Code development, connects to Windows MySQL
2. **GitHub**: Push to main branch triggers auto-deployment
3. **Windows**: Automatic pull, restart, and deploy via GitHub Actions
4. **Live**: Changes appear on sertifikatet.no automatically

### Automatic Services

- ✅ Cloudflare tunnel starts on Windows boot
- ✅ Flask app managed by NVVM (auto-restart)
- ✅ GitHub Actions runner service
- ✅ MySQL database service

The entire stack auto-starts and auto-deploys for seamless development! 🚀

### Service Runners & System Services

The platform runs on Windows with the following critical services that auto-start on system boot:

#### Core Infrastructure Services

**MySQL80**
- Service Name: `MySQL80`
- Description: MySQL database server
- Status Check: `sc query "MySQL80"`
- Port: 3306
- Critical: Database backend for all application data

**Cloudflared**
- Service Name: `Cloudflared`
- Description: Cloudflare tunnel service for sertifikatet.no
- Status Check: `sc query "Cloudflared"`
- Function: Secure tunnel with automatic SSL and DDoS protection
- Critical: Required for public website access

**SertifikatetFlask**
- Service Name: `SertifikatetFlask`
- Description: Flask application server (managed by NVVM)
- Status Check: `sc query "SertifikatetFlask"`
- Port: 8000 (local)
- Function: Main web application server with auto-restart capabilities

**GitHub Actions Runner**
- Service Name: `actions.runner.viktor-mq-sertifikatet.VIKTORIOUS-DESK`
- Description: Self-hosted CI/CD runner for automatic deployments
- Status Check: `sc query "actions.runner.viktor-mq-sertifikatet.VIKTORIOUS-DESK"`
- Function: Handles automatic deployment from GitHub to production
- GitHub Status: Should show "Idle" (green) when ready

#### Service Management Commands

**Check All Services Status:**
```cmd
sc query "MySQL80"
sc query "Cloudflared"
sc query "SertifikatetFlask"
sc query "actions.runner.viktor-mq-sertifikatet.VIKTORIOUS-DESK"
```

**Start Services Manually (if needed):**
```cmd
net start MySQL80
net start Cloudflared
net start SertifikatetFlask
net start "actions.runner.viktor-mq-sertifikatet.VIKTORIOUS-DESK"
```

**Stop Services:**
```cmd
net stop MySQL80
net stop Cloudflared
net stop SertifikatetFlask
net stop "actions.runner.viktor-mq-sertifikatet.VIKTORIOUS-DESK"
```

#### Service Dependencies

1. **MySQL80** - Must start first (database dependency)
2. **SertifikatetFlask** - Depends on MySQL80
3. **Cloudflared** - Routes traffic to Flask app
4. **GitHub Runner** - Independent, handles CI/CD

#### Post-Restart Verification

After system restart, verify all services are operational:

1. **Service Status**: Run status check commands above
2. **Website Access**: Visit [https://sertifikatet.no](https://sertifikatet.no)
3. **GitHub Runner**: Check GitHub → Settings → Actions → Runners (should show "Idle")
4. **Database**: Confirm MySQL is accepting connections on port 3306

#### Troubleshooting

**If services fail to start:**
- Check Windows Event Viewer for service-specific errors
- Verify user permissions for service accounts
- Ensure no port conflicts (3306 for MySQL, 8000 for Flask)
- Check disk space on D: drive where application is hosted

**GitHub Runner Issues:**
- Runner should auto-reconnect after restart
- If showing offline, restart the service
- Check runner logs in the application directory

This infrastructure setup ensures zero-manual-intervention startup and professional-grade service management! 🎯

## 🏗️ Tech Stack

### Backend

- **Framework**: Flask with SQLAlchemy ORM
- **Database**: MySQL (Production) / SQLite (Testing)
- **Caching**: Redis with fallback mechanisms
- **Tasks**: Celery for background processing
- **ML Stack**: scikit-learn, pandas, numpy (local processing)

### Frontend

- **UI**: React components with Tailwind CSS
- **Charts**: Chart.js for analytics
- **Games**: Phaser.js for interactive content

### Infrastructure

- **Containers**: Docker & Docker Compose
- **CI/CD**: GitHub Actions with self-hosted runner
- **Testing**: pytest with database isolation
- **Code Quality**: black, flake8, isort, mypy
- **Security**: bandit, safety, Trivy scanning

## 🔍 SEO & Search Engine Optimization

### Development vs Production SEO Protection

Sertifikatet includes **enterprise-level SEO protection** that automatically prevents search engine indexing during development while enabling full SEO optimization in production.

#### 🔒 **Development Mode Protection**

When `ENVIRONMENT=development` or `DEBUG=True`:

```html
<!-- Automatic meta robots protection -->
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
<meta name="environment" content="development">
```

```
# Development robots.txt blocks all crawlers
User-agent: *
Disallow: /
```

**Benefits:**
- ✅ **Zero accidental indexing** of development content
- ✅ **No SEO penalties** from unfinished features
- ✅ **Protected developer authentication** pages
- ✅ **Safe testing environment** for SEO features

#### 🚀 **Production Mode SEO**

When `ENVIRONMENT=production`:

- ✅ **Full search engine optimization** enabled
- ✅ **Dynamic meta tag generation** with Norwegian localization
- ✅ **JSON-LD structured data** for rich snippets
- ✅ **Automatic sitemap.xml** generation
- ✅ **Google Search Console** integration (DNS verified)
- ✅ **Open Graph and Twitter Cards** for social sharing

### Environment Configuration

**Development setup:**
```bash
# In .env file
DEBUG=True
ENVIRONMENT=development

# Result: All search engines blocked
```

**Production deployment:**
```bash
# In .env file
DEBUG=False
ENVIRONMENT=production

# Result: Full SEO optimization active
```

### SEO Features

#### **Dynamic Meta Tags**
- Page-specific titles and descriptions
- Norwegian keyword optimization
- Automatic canonical URLs
- Geo-targeting for Norway

#### **Structured Data (JSON-LD)**
- Educational organization schema
- Course and quiz markup
- Breadcrumb navigation
- Video object schemas

#### **Performance Optimization**
- Resource preloading for critical CSS
- DNS prefetch for external resources
- Optimized favicon delivery
- PWA manifest integration

#### **Search Console Integration**
- DNS verification via Cloudflare (enterprise-grade)
- Automatic sitemap submission
- Search performance monitoring
- Index status tracking

### Testing SEO Implementation

**Verify development protection:**
```bash
# Check robots meta tag
curl -s http://localhost:8000 | grep "noindex"

# Check robots.txt
curl -s http://localhost:8000/robots.txt
```

**Validate production SEO:**
```bash
# Test structured data
curl -s https://sertifikatet.no | grep "application/ld+json"

# Verify meta tags
curl -s https://sertifikatet.no | grep "<meta"
```

## 🧪 Testing Framework & Database Safety

### Critical Safety Features

Our testing framework includes **multiple layers of protection** to prevent accidental production database access:

#### Layer 1: Environment Variables

```python
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['TESTING'] = '1'
os.environ['FLASK_ENV'] = 'testing'
```

#### Layer 2: Runtime Safety Checks

```python
# Prevents any accidental production DB access
if 'sertifikatet' in os.environ.get('DATABASE_URL', ''):
    raise RuntimeError("DANGER: Tests attempting to use production database!")

if 'mysql' in app.config.get('SQLALCHEMY_DATABASE_URI', '').lower():
    raise RuntimeError("CRITICAL: Test trying to use MySQL production database!")
```

#### Layer 3: In-Memory Database

All tests use `sqlite:///:memory:` - a temporary database that exists only in RAM and is automatically destroyed after tests.

### Test Structure

```
tests/
├── conftest.py          # Test configuration and fixtures
├── test_basic.py        # Basic functionality tests
├── test_auth.py         # Authentication tests
└── test_models.py       # Database model tests
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_basic.py -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test
pytest tests/test_auth.py::TestAuthentication::test_user_login_success -v
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Our CI/CD pipeline includes both **testing** and **automatic deployment**:

#### 1. **Automated Testing**

- Runs on every push to `main` and `develop` branches
- Runs on all pull requests
- Uses isolated in-memory database
- Includes Redis service for caching tests

#### 2. **Code Quality Checks**

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting and style
- **mypy**: Type checking

#### 3. **SEO Development Protection**

- **Environment-aware SEO**: Automatic search engine blocking during development
- **robots.txt control**: Dynamic crawler directives based on environment
- **Meta robots protection**: `noindex, nofollow` during development mode
- **Production SEO**: Full search engine optimization when `ENVIRONMENT=production`

#### 4. **Security Scanning**

- **bandit**: Python security analysis
- **safety**: Dependency vulnerability scanning
- **Trivy**: Container and filesystem vulnerability scanning

#### 4. **Coverage Reporting**

- Test coverage analysis
- Integration with Codecov
- HTML coverage reports

#### 5. **Automatic Deployment (Self-Hosted Runner)**

- **Self-hosted runner**: Windows desktop with automatic deployment
- **Feature branches**: Tests only (no deployment)
- **Main branch**: Tests + automatic deployment to production
- **Zero-downtime**: NVVM manages Flask restarts seamlessly

### Self-Hosted CI/CD Architecture

```
MacBook (Development)
    ↓ git push to main
GitHub Repository
    ↓ triggers webhook
Windows Desktop (Self-Hosted Runner)
    ↓ pulls changes & restarts
Sertifikatet.no Live Website
```

The self-hosted runner on Windows desktop:

- Pulls latest code automatically
- Installs/updates dependencies
- Runs database migrations
- Restarts Flask application via NVVM
- Makes changes live on sertifikatet.no

### Pre-commit Hooks

Install pre-commit hooks for local development:

```bash
pip install pre-commit
pre-commit install
```

## 🐳 Docker Setup

### Development Environment

```bash
# Start development environment
docker-compose up

# Run tests in Docker
docker-compose --profile test run test

# Build production image
docker build -t sertifikatet .
```

### Docker Configuration

- **Dockerfile**: Production-ready container
- **docker-compose.yml**: Development environment with MySQL and Redis
- **Multi-stage builds**: Optimized for production
- **Health checks**: Container monitoring

## 🗄️ Database Management

### Automated Backup System

Sertifikatet includes a comprehensive automated backup system that protects your data with daily backups, compression, verification, and email alerts.

#### 🕐 **Backup Schedule**

- **Frequency**: Every day at 2:30 AM
- **Format**: Compressed MySQL dumps (.sql.gz)
- **Retention**: 30 days (automatic cleanup)
- **Location**: `backups/database/`
- **Compression**: ~84% size reduction
- **Verification**: Automatic integrity checking

#### 🔧 **Setup Instructions**

1. **Install the backup system**:

   ```bash
   cd /Users/viktorigesund/Documents/teoritest
   chmod +x scripts/setup_backup_system.sh
   ./scripts/setup_backup_system.sh
   ```

2. **Verify cron job installation**:

   ```bash
   crontab -l | grep sertifikatet
   ```

   Should show:

   ```
   30 2 * * * cd /path/to/teoritest && venv/bin/python scripts/database_backup.py
   ```

3. **Check cron service is running**:
   ```bash
   sudo launchctl list | grep cron
   ```
   Should show: `com.vix.cron` with a process ID

#### 📊 **Backup Features**

- **Complete Data**: All tables, indexes, triggers, stored procedures
- **Consistent Snapshots**: Single-transaction dumps ensure data integrity
- **Compression**: Automatic gzip compression saves ~84% disk space
- **Verification**: Validates backup integrity and table count
- **Email Alerts**: Automatic notifications if backup fails
- **Cleanup**: Removes backups older than 30 days
- **Logging**: Detailed logs in `backups/database/backup.log`

#### 🚨 **Requirements & Limitations**

**Your Mac must be:**

- ✅ **Powered on or sleeping** (not shut down) at 2:30 AM
- ✅ **Connected to network** (WiFi/Ethernet)
- ✅ **MySQL service running** on localhost:3306

**What happens if:**

- 🔴 **Mac is off**: Backup skipped, no notification
- 🟢 **Mac is sleeping**: Backup runs normally
- 🟡 **No network**: Backup fails, email alert sent
- 🟡 **MySQL down**: Backup fails, email alert sent

#### 📧 **Email Alerts**

Automatic notifications sent to `SUPER_ADMIN_EMAIL` for:

- Backup failures
- Database connection issues
- Verification failures
- Script errors

#### 🖥️ **Manual Backup Operations**

**Create immediate backup**:

```bash
cd /Users/viktorigesund/Documents/teoritest
python scripts/database_backup.py
```

**View recent backups**:

```bash
ls -la backups/database/*.sql.gz
```

**Check backup logs**:

```bash
tail -f backups/database/backup.log
```

### Database Recovery

#### 🔄 **Restore from Backup**

1. **Find the backup to restore**:

   ```bash
   ls -la backups/database/sertifikatet_backup_*.sql.gz
   ```

2. **Restore using one-liner** (recommended):

   ```bash
   gunzip -c backups/database/sertifikatet_backup_YYYYMMDD_HHMMSS.sql.gz | mysql -u root -p sertifikatet
   ```

3. **Alternative two-step method**:
   ```bash
   gunzip backups/database/sertifikatet_backup_YYYYMMDD_HHMMSS.sql.gz
   mysql -u root -p sertifikatet < backups/database/sertifikatet_backup_YYYYMMDD_HHMMSS.sql
   ```

#### 🚨 **Emergency Recovery Procedure**

If tests accidentally affect production database:

1. **Immediate action**:

   ```bash
   # Stop all processes accessing the database
   sudo brew services stop mysql
   ```

2. **Restore from latest backup**:

   ```bash
   sudo brew services start mysql
   gunzip -c backups/database/$(ls -t backups/database/*.sql.gz | head -1) | mysql -u root -p sertifikatet
   ```

3. **Verify data integrity**:

   ```bash
   mysql -u root -p sertifikatet -e "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM questions;"
   ```

4. **Check test configuration** for safety violations

#### 🏢 **Production Backup Strategy**

For server deployment, implement these additional backup layers:

**Server-Side Backups**:

```bash
# Production server cron job
0 2 * * * /usr/bin/mysqldump --single-transaction sertifikatet | gzip > /backups/daily/backup_$(date +\%Y\%m\%d).sql.gz
```

**Cloud Backup Options**:

- **AWS RDS**: Automated backups with point-in-time recovery
- **Google Cloud SQL**: Daily backups with 7-day retention
- **DigitalOcean Managed Databases**: Automatic daily backups

**Off-site Storage**:

```bash
# Upload to cloud storage
aws s3 cp backup.sql.gz s3://your-backup-bucket/$(date +%Y/%m/%d)/
```

### Migration Management

```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Downgrade if needed
flask db downgrade
```

## 🔧 Development Setup

### Prerequisites

- **Python 3.10** (Required - matches CI/CD and production)
- MySQL 8.0+
- Redis 7+
- Node.js (for frontend assets)

### Python Version Management

This project requires **Python 3.10** for compatibility with all dependencies and production environment.

**Using pyenv (recommended)**:

```bash
# Install Python 3.10 if not already installed
pyenv install 3.10.15

# Set Python 3.10 for this project
pyenv local 3.10.15

# Verify version
python --version  # Should show Python 3.10.x
```

### System Dependencies

For production deployment, install these system packages:

```bash
# On Ubuntu/Debian:
sudo apt-get update
sudo apt-get install nginx supervisor

# On macOS:
brew install nginx supervisor

# On CentOS/RHEL:
sudo yum install nginx supervisor
```

**Note**: These are system packages (not Python packages) required for production deployment:

- **nginx**: Web server for reverse proxy and static file serving
- **supervisor**: Process management for running the application

### Installation

1. **Clone repository**:

   ```bash
   git clone [repository-url]
   cd teoritest
   ```

2. **Create virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**:

   ```bash
   flask db upgrade
   python scripts/init_db.py
   ```

6. **Run application**:
   ```bash
   python run.py
   ```

## 🌊 Git Flow Strategy

### Branch Structure

```
main (production)
├── develop (staging)
    ├── feature/user-authentication
    ├── feature/quiz-improvements
    └── feature/payment-integration
```

### Workflow

1. **Feature Development**:

   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/my-new-feature
   # Develop feature...
   git push origin feature/my-new-feature
   ```

2. **Create Pull Request**: `feature/my-new-feature` → `develop`

   - Automatic CI/CD testing
   - Code review required
   - Deploys to staging after merge

3. **Production Release**: `develop` → `main`
   - Comprehensive testing
   - Automatic deployment to sertifikatet.no via self-hosted runner

## 📊 Project Status

### Completed Phases ✅

- **Phase 1-15**: All core functionality implemented
- **Authentication & Authorization**: Complete
- **Quiz System**: Advanced with ML personalization
- **Gamification**: Comprehensive achievement system
- **Video Learning**: Interactive with checkpoints
- **Payment System**: Stripe integration with Norwegian methods
- **ML Personalization**: Adaptive learning algorithms
- **CI/CD Infrastructure**: Complete pipeline with self-hosted runner
- **Testing Framework**: Comprehensive with safety measures
- **Production Infrastructure**: Automatic deployment to sertifikatet.no

### Current Features

- 🎯 **Adaptive Learning**: ML-powered question selection
- 🏆 **Gamification**: 25+ achievements, leaderboards, streaks
- 📹 **Video Learning**: Interactive checkpoints and notes
- 💳 **Payments**: Stripe + Vipps integration
- 📱 **PWA**: Offline support and mobile optimization
- 🔒 **Security**: Comprehensive error handling and monitoring
- 📈 **Analytics**: Detailed progress tracking and insights
- 🚀 **Auto-deployment**: Seamless CI/CD with self-hosted runner

## 🛡️ Security & Monitoring

### Error Handling

- Centralized error logging via `AdminReport` model
- Custom error pages (404, 500)
- API-specific JSON error responses
- Automatic admin notifications for critical errors

### Caching Strategy

- Redis-based caching with fallback mechanisms
- Decorator-based caching for performance
- Pattern-based cache invalidation
- Performance monitoring integration

### Security Measures

- Input validation and sanitization
- SQL injection protection
- XSS protection
- CSRF protection
- Rate limiting capabilities
- Vulnerability scanning in CI/CD

## 📝 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=mysql+pymysql://user:password@localhost/sertifikatet
REDIS_URL=redis://localhost:6379/0

# Flask
SECRET_KEY=your-secret-key
FLASK_ENV=development

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Payments
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# Admin
SUPER_ADMIN_EMAIL=admin@example.com
```

## 🚀 Deployment

### Production Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Backup system active
- [ ] Monitoring configured
- [ ] CI/CD pipeline tested
- [ ] Error tracking enabled
- [ ] Self-hosted runner operational
- [ ] Cloudflare tunnel configured

### Staging Environment

Automatically deployed from `develop` branch:

- Full feature testing
- Integration testing
- Performance validation

### Production Environment

Deployed from `main` branch with automatic CI/CD:

- All tests passing
- Security scans clean
- Code review approved
- Automatic deployment to sertifikatet.no
- NVVM ensures zero-downtime restarts

## 📚 Additional Resources

### Documentation

- [Payment Setup Guide](PAYMENT_SETUP.md)
- [MySQL Migration Guide](README_MYSQL_MIGRATION.md)
- [Mobile Testing Checklist](mobile_testing_checklist.md)

### Support

- **Issues**: Use GitHub Issues for bug reports
- **Development**: Check project checklist for status
- **Security**: Report security issues privately

## 🤝 Contributing

1. Fork the repository
2. Create feature branch from `develop`
3. Follow code style guidelines (enforced by pre-commit)
4. Write tests for new functionality
5. Ensure all CI/CD checks pass
6. Submit pull request with detailed description

## 📄 License

[License information]

---

**Note**: This platform includes comprehensive safety measures to protect production data during development and testing. The multi-layered database protection system ensures that tests cannot accidentally affect production data. The project features a professional CI/CD pipeline with automatic deployment to the live domain at sertifikatet.no.
