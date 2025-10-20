# Example: Database Connection Pool Size Increase

## Scenario
Increased database connection pool size from 10 to 50 in production configuration. This is a 5x increase that could exhaust database connections if not properly validated.

## Code

```yaml
# config/production.yml

# BEFORE:
database:
  host: prod-db.internal
  port: 5432
  pool_size: 10        # Was 10
  timeout: 30

# AFTER:
database:
  host: prod-db.internal
  port: 5432
  pool_size: 50        # Changed to 50 (5x increase!)
  timeout: 30
```

## Expected Analysis

```json
{
  "risk_score": 58,
  "risk_level": "MEDIUM",
  "confidence": "HIGH",
  "findings": [
    {
      "category": "CONFIG",
      "severity": "MEDIUM",
      "file": "config/production.yml",
      "line": 6,
      "description": "Database connection pool size increased from 10 to 50 (5x increase). This significant change may cause database connection exhaustion if not properly validated against database server limits.",
      "impact": "If the database server has a max_connections limit (e.g., PostgreSQL default is 100), and multiple application instances are deployed, total connections could be: instances × pool_size. For example, 3 instances × 50 = 150 connections, exceeding database limits. This can cause: 1) Database refusing new connections, 2) Application startup failures, 3) Connection timeout errors, 4) Service degradation or outage.",
      "recommendation": "Before deployment: 1) Verify database server's max_connections setting (PostgreSQL: SHOW max_connections), 2) Calculate total expected connections: (number_of_app_instances × pool_size) + (other_services_pool_sizes), 3) Ensure total is well below database max_connections (leave 20% buffer), 4) Load test with new pool size to validate performance improvement, 5) Monitor connection usage in staging for 24-48 hours, 6) Implement gradual rollout (increase to 25 first, then 50)."
    }
  ],
  "test_recommendations": [
    "Add load tests to validate performance with 50 concurrent database connections",
    "Add connection leak tests to ensure connections are properly released back to the pool",
    "Monitor database connection metrics in staging environment for at least 24 hours before production deployment",
    "Add connection exhaustion tests to verify graceful handling when pool is exhausted",
    "Test application behavior when database reaches max_connections limit"
  ],
  "metadata": {
    "analyzed_files": 1,
    "patterns_checked": ["config-changes", "database-settings"],
    "analysis_duration_seconds": 2.5
  }
}
```

## Risk Assessment Rationale

**Impact Score: 30/40**
- Can cause service outage if mishandled
- Affects all database operations
- Recoverable with configuration rollback
- Not data loss risk

**Likelihood Score: 20/40**
- Configuration changes often go wrong
- But this is a common operation
- Medium likelihood with proper validation

**Test Coverage Gap: 8/20**
- Load testing may not cover this
- Connection monitoring needed

**Total: 58/100 = MEDIUM**
