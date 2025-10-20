# Example: New External Dependency Without Resilience Patterns

## Scenario
Added a new HTTP call to an external API (`external-api.com`) without implementing timeout, retry logic, or circuit breaker pattern.

## Code

```python
# src/services/profile_service.py
import requests

class ProfileService:
    def get_user_profile(self, user_id: str):
        # NEW: Call to external API without resilience patterns
        response = requests.get(
            f"https://external-api.com/users/{user_id}"
        )
        # No timeout parameter ❌
        # No retry logic ❌
        # No circuit breaker ❌
        # No fallback mechanism ❌

        return response.json()
```

## Expected Analysis

```json
{
  "risk_score": 75,
  "risk_level": "HIGH",
  "confidence": "HIGH",
  "findings": [
    {
      "category": "RESILIENCE",
      "severity": "HIGH",
      "file": "src/services/profile_service.py",
      "line": 8,
      "description": "New external API call to external-api.com without timeout configuration. This can cause cascading failures if the external service is slow or unresponsive.",
      "impact": "If external-api.com experiences slowness or becomes unresponsive, this service will hang indefinitely, exhausting thread pools and blocking other requests. This can lead to: 1) Complete service outage, 2) Cascading failures across dependent systems, 3) Resource exhaustion (threads, connections), 4) Degraded user experience across the entire platform.",
      "recommendation": "Implement comprehensive resilience patterns: 1) Add explicit timeout (recommended: 5 seconds for external APIs), 2) Implement retry logic with exponential backoff (max 3 retries), 3) Add circuit breaker pattern to prevent cascading failures, 4) Implement fallback mechanism or graceful degradation, 5) Add monitoring and alerting for external API latency."
    },
    {
      "category": "DEPENDENCY",
      "severity": "MEDIUM",
      "file": "src/services/profile_service.py",
      "line": 8,
      "description": "New hard dependency on external-api.com. Service availability now depends on external system uptime.",
      "impact": "If external-api.com is down, this service cannot function. Creates a single point of failure. External API SLAs may not match internal service requirements.",
      "recommendation": "1) Implement graceful degradation (return partial data or cached data when external API fails), 2) Consider caching strategy to reduce dependency on external service, 3) Document dependency and add to system architecture diagrams, 4) Negotiate SLA with external API provider."
    }
  ],
  "test_recommendations": [
    "Add timeout tests: Verify behavior when external API is slow (>5s response time)",
    "Add retry tests: Verify exponential backoff works correctly and doesn't cause retry storms",
    "Add circuit breaker tests: Verify circuit opens after failure threshold and closes after recovery",
    "Add failure mode tests: Verify graceful degradation when external API returns 500 errors or is unreachable",
    "Add load tests: Verify performance under high request volume with external API calls",
    "Add integration tests: Test actual integration with external-api.com in staging environment"
  ],
  "metadata": {
    "analyzed_files": 1,
    "patterns_checked": ["timeout", "retry", "circuit-breaker", "fallback"],
    "analysis_duration_seconds": 3.2
  }
}
```

## Risk Assessment Rationale

**Impact Score: 35/40**
- Can cause complete service outage
- Affects all users of this service
- Cascading failure potential
- Production stability risk

**Likelihood Score: 35/40**
- External services WILL experience issues
- Without timeout, failures are guaranteed eventually
- High likelihood of impact in production

**Test Coverage Gap: 5/20**
- No resilience tests exist yet
- Integration tests needed

**Total: 75/100 = HIGH**
