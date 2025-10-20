# Example: @Retry Without @CircuitBreaker (ANTI-PATTERN)

## Scenario
Developer added @Retry annotation to handle transient failures when calling inventory service, but forgot to add @CircuitBreaker. This creates a dangerous "retry storm" that can overwhelm a failing service instead of protecting it.

## Code

### After (Dangerous Anti-Pattern)
```java
// src/main/java/com/example/service/InventoryService.java
package com.example.service;

import io.github.resilience4j.retry.annotation.Retry;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class InventoryService {
    private final RestClient restClient;

    public InventoryService(RestClient.Builder builder) {
        this.restClient = builder
            .baseUrl("https://inventory-api.internal.company.com")
            .build();
    }

    // ⚠️ ANTI-PATTERN: @Retry WITHOUT @CircuitBreaker
    @Retry(name = "inventoryService")
    public InventoryResponse checkStock(String productId) {
        // ❌ Will retry 3x even if service is completely down
        // ❌ No circuit breaker to stop retry storm
        // ❌ Multiplies load on failing service
        // ❌ No timeout configured

        return restClient.get()
            .uri("/api/v1/inventory/{productId}", productId)
            .retrieve()
            .body(InventoryResponse.class);
    }
}
```

### Configuration (Also Problematic)
```yaml
# application.yml
resilience4j:
  retry:
    instances:
      inventoryService:
        maxAttempts: 3              # ⚠️ Retries 3 times
        waitDuration: 500ms         # ⚠️ Only 500ms between retries
        # ❌ No exponential backoff!
        # ❌ No circuit breaker configured!
```

## Expected Analysis

```json
{
  "risk_score": 85,
  "risk_level": "CRITICAL",
  "confidence": "HIGH",
  "findings": [
    {
      "category": "RESILIENCE_ANTI_PATTERN",
      "severity": "CRITICAL",
      "file": "src/main/java/com/example/service/InventoryService.java",
      "line": 18,
      "description": "CRITICAL ANTI-PATTERN: @Retry annotation used WITHOUT @CircuitBreaker. This can create a 'retry storm' that overwhelms failing services instead of protecting them. Research shows retries should NEVER be used between microservices without circuit breakers.",
      "impact": "Catastrophic failure mode during inventory service outage: 1) Each failed request retries 3 times (3x traffic amplification), 2) With 100 concurrent requests, failing service receives 300 requests instead of 100, 3) Retry storm prevents service recovery (cannot heal under increased load), 4) Cascading failures spread to other services also retrying, 5) Complete distributed system meltdown. Production impact: Multi-hour outage affecting all services, manual intervention required, potential data inconsistencies.",
      "recommendation": "⚠️ URGENT: This pattern MUST be fixed before production deployment.\n\n**Required Changes:**\n\n**1. Add Circuit Breaker (MANDATORY)**\n```java\nimport io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;\nimport io.github.resilience4j.retry.annotation.Retry;\nimport io.github.resilience4j.timelimiter.annotation.TimeLimiter;\n\n@Service\npublic class InventoryService {\n    \n    // ✅ Correct pattern: Circuit Breaker + Retry + Timeout\n    @CircuitBreaker(name = \"inventoryService\", fallbackMethod = \"checkStockFallback\")\n    @Retry(name = \"inventoryService\")  // Now safe because circuit breaker stops retry storm\n    @TimeLimiter(name = \"inventoryService\")\n    public InventoryResponse checkStock(String productId) {\n        return restClient.get()\n            .uri(\"/api/v1/inventory/{productId}\", productId)\n            .retrieve()\n            .body(InventoryResponse.class);\n    }\n    \n    private InventoryResponse checkStockFallback(String productId, Exception e) {\n        log.error(\"Inventory service unavailable for product: {}\", productId, e);\n        // Return cached inventory or mark as \"unavailable\"\n        return InventoryResponse.builder()\n            .productId(productId)\n            .available(false)\n            .message(\"Inventory check unavailable, please try again later\")\n            .build();\n    }\n}\n```\n\n**2. Update Configuration (CRITICAL)**\n```yaml\nresilience4j:\n  circuitbreaker:\n    instances:\n      inventoryService:\n        failureRateThreshold: 50\n        slowCallRateThreshold: 50\n        slowCallDurationThreshold: 2s\n        slidingWindowSize: 10\n        minimumNumberOfCalls: 5\n        waitDurationInOpenState: 30s   # Stop retry storm for 30s\n        automaticTransitionFromOpenToHalfOpenEnabled: true\n        \n  timelimiter:\n    instances:\n      inventoryService:\n        timeoutDuration: 2s\n        \n  retry:\n    instances:\n      inventoryService:\n        maxAttempts: 2                # Reduce to 2 (circuit breaker handles failures)\n        waitDuration: 1s              # Increase delay between retries\n        enableExponentialBackoff: true    # CRITICAL: Add exponential backoff\n        exponentialBackoffMultiplier: 2   # 1s, 2s, 4s...\n        retryExceptions:\n          - org.springframework.web.client.ResourceAccessException\n          - java.net.SocketTimeoutException\n        ignoreExceptions:\n          - java.lang.IllegalArgumentException\n          - org.springframework.web.client.HttpClientErrorException.NotFound\n```\n\n**Why This Pattern is Dangerous:**\n\nWithout circuit breaker:\n```\nInventory service goes down at 10:00 AM\n→ 100 requests/second × 3 retries = 300 requests/second\n→ Service under 3x load while trying to recover\n→ Cannot recover due to retry storm\n→ All dependent services also retrying\n→ Total system collapse by 10:05 AM\n```\n\nWith circuit breaker:\n```\nInventory service goes down at 10:00 AM\n→ Circuit opens after 5 failed calls (< 1 second)\n→ No retries for 30 seconds (circuit in OPEN state)\n→ Service can recover without additional load\n→ Circuit automatically tests recovery (HALF_OPEN)\n→ Normal operation resumes by 10:00:30 AM\n```"
    },
    {
      "category": "CONFIG",
      "severity": "HIGH",
      "file": "application.yml",
      "line": 5,
      "description": "Retry configuration lacks exponential backoff. Fixed 500ms delay can create synchronized retry waves across all clients.",
      "impact": "All clients retry at same fixed intervals, creating 'thundering herd' effect. When service recovers, all clients retry simultaneously, causing immediate re-failure. Service cannot stabilize.",
      "recommendation": "Enable exponential backoff with jitter (see configuration above). This spreads retry attempts over time, allowing service to recover gradually."
    }
  ],
  "test_recommendations": [
    "⚠️ CRITICAL: DO NOT DEPLOY without these tests passing",
    "Integration test: Simulate inventory service returning 500 errors, verify circuit breaker opens after threshold",
    "Integration test: Verify NO retries occur while circuit is OPEN (prevent retry storm)",
    "Integration test: Verify circuit transitions to HALF_OPEN after waitDuration",
    "Integration test: Verify only 1 test request in HALF_OPEN state (not full retry)",
    "Load test: 200 concurrent requests with service down, verify circuit opens within 1 second",
    "Load test: Measure actual load on failing service, verify it's NOT 3x incoming traffic",
    "Chaos test: Kill inventory service, monitor for 5 minutes, verify no retry storm in metrics",
    "Chaos test: Bring inventory service back up, verify smooth recovery without thundering herd",
    "Monitoring test: Verify circuit breaker state changes are logged and alerted"
  ],
  "metadata": {
    "analyzed_files": 2,
    "patterns_checked": ["retry", "circuit-breaker", "exponential-backoff", "anti-patterns"],
    "spring_boot_version": "3.x",
    "analysis_duration_seconds": 5.1,
    "research_reference": "Resilience4j best practices: Retries should never be used between services without circuit breakers"
  }
}
```

## Risk Assessment Rationale

**Impact Score: 40/40 (MAXIMUM)**
- Can cause complete distributed system failure
- Multi-service cascading collapse
- Requires manual intervention to recover
- Extended multi-hour outage potential
- Affects entire microservices ecosystem

**Likelihood Score: 35/40**
- Pattern will definitely cause issues during first inventory service incident
- Microservices experience failures regularly (deployments, scaling, network)
- Retry storms are well-documented catastrophic failure mode
- Almost certain to manifest within first 30 days

**Test Coverage Gap: 10/20**
- No chaos testing
- No circuit breaker validation
- No retry storm prevention tests

**Total: 85/100 = CRITICAL**

---

## Why This is an Anti-Pattern

### 🔴 The Problem Explained

**Normal Operation:**
```
Client → [100 req/s] → Service (healthy)
```

**Service Fails (No Circuit Breaker):**
```
Client → [100 req/s × 3 retries] → Service (down)
       = 300 req/s hitting dying service

Multiple Clients:
10 clients × 100 req/s × 3 retries = 3,000 req/s
Service cannot recover under 30x normal load
```

**Service Fails (With Circuit Breaker):**
```
Client → [100 req/s] → Circuit Breaker (OPEN)
                    → Fallback response
                    → Service gets 0 req/s
                    → Service recovers
                    → Circuit tests recovery (HALF_OPEN)
                    → Circuit closes, normal operation resumes
```

---

## Real-World Production Incident

**Scenario:** E-commerce platform, Black Friday 2023

```
Timeline:
10:00:00 - Inventory service deploys new version
10:00:15 - Service has bug, starts returning 500 errors
10:00:16 - Order service retries (no circuit breaker)
10:00:17 - 50 order service instances × 200 req/s × 3 retries
         = 30,000 requests/s to failing inventory service
10:00:20 - Inventory service collapses under load
10:00:25 - Payment service also starts retrying
10:00:30 - Complete platform outage
10:45:00 - Manual kill switch activated
11:30:00 - Services restarted one by one
12:00:00 - Platform back online

Impact:
- 2 hours of downtime
- $2.3M in lost revenue
- 15,000 failed orders
- Customer trust damaged

Root Cause:
@Retry without @CircuitBreaker in 3 different services
```

---

## Correct Pattern: Layered Resilience

```java
// ✅ Recommended: Combine all three patterns
@CircuitBreaker(name = "service", fallbackMethod = "fallback")
@Retry(name = "service")           // Safe because circuit breaker protects
@TimeLimiter(name = "service")     // Prevents thread exhaustion

// Execution order (inside-out):
// 1. TimeLimiter wraps the call (timeout protection)
// 2. Retry wraps TimeLimiter (handles transient failures)
// 3. CircuitBreaker wraps Retry (stops retry storms)
```

### Pattern Interaction:

**Transient Failure (Network Blip):**
1. Call fails → TimeLimiter timeout
2. Retry catches → waits 1s
3. Retry succeeds → Circuit stays CLOSED
4. ✅ Resilient to transient issues

**Persistent Failure (Service Down):**
1. Call fails → TimeLimiter timeout
2. Retry #1 fails → waits 1s
3. Retry #2 fails → Circuit records failures
4. After 5 failures → Circuit OPENS
5. ❌ No more retries (circuit is OPEN)
6. ✅ Failing service protected from retry storm

---

## Configuration Best Practices

### ❌ Bad Configuration (Retry Storm Risk)
```yaml
resilience4j:
  retry:
    instances:
      api:
        maxAttempts: 5           # Too many retries
        waitDuration: 100ms      # Too short delay
        # No exponential backoff
        # No circuit breaker
```

### ✅ Good Configuration (Production Safe)
```yaml
resilience4j:
  circuitbreaker:
    instances:
      api:
        failureRateThreshold: 50
        waitDurationInOpenState: 30s  # Give service time to recover

  retry:
    instances:
      api:
        maxAttempts: 2                      # Fewer retries (circuit breaker handles rest)
        waitDuration: 1s                    # Longer initial delay
        enableExponentialBackoff: true      # CRITICAL
        exponentialBackoffMultiplier: 2     # 1s, 2s, 4s
        randomizationFactor: 0.5            # Add jitter (prevent thundering herd)
```

---

## Detection in Code Review

**Red Flags:**
- ✅ @Retry without @CircuitBreaker (CRITICAL)
- ✅ maxAttempts > 3
- ✅ waitDuration < 1s
- ✅ enableExponentialBackoff = false
- ✅ No fallback method defined

**Questions to Ask:**
1. "What happens if the downstream service is completely down for 5 minutes?"
2. "With 100 concurrent calls, how many requests hit the failing service?"
3. "How does the system prevent retry storms?"
4. "What's the fallback behavior when circuit is open?"

---

## Monitoring & Alerts

**Required Metrics:**
```yaml
# Alert when circuit opens
resilience4j.circuitbreaker.state == OPEN

# Alert on high retry rate
rate(resilience4j.retry.calls.total[1m]) > 10

# Alert on no circuit breaker with retries
@Retry present AND @CircuitBreaker absent
```

**Dashboard:**
- Circuit state timeline (CLOSED/OPEN/HALF_OPEN)
- Retry success/failure rate
- Downstream service load (should not spike during failures)
- Fallback invocation count
