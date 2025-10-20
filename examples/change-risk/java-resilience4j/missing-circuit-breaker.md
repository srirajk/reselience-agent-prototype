# Example: RestClient Without Circuit Breaker (Spring Boot 3 + Resilience4j)

## Scenario
New HTTP call to payment service using Spring Boot 3's RestClient without Resilience4j circuit breaker protection. This is a modern example using the current Spring framework stack (not deprecated RestTemplate or Feign).

## Code

### After (Problematic Change)
```java
// src/main/java/com/example/service/OrderService.java
package com.example.service;

import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class OrderService {
    private final RestClient restClient;

    public OrderService(RestClient.Builder builder) {
        // RestClient is the modern replacement for RestTemplate in Spring Boot 3
        this.restClient = builder
            .baseUrl("https://payment-api.internal.company.com")
            .build();
    }

    public PaymentResponse processPayment(String orderId, double amount) {
        // ❌ Missing @CircuitBreaker annotation
        // ❌ No fallback method
        // ❌ No @TimeLimiter (timeout)
        // ❌ No @Retry

        return restClient.post()
            .uri("/api/v1/payments")
            .body(new PaymentRequest(orderId, amount))
            .retrieve()
            .body(PaymentResponse.class);
    }
}
```

## Expected Analysis

```json
{
  "risk_score": 78,
  "risk_level": "HIGH",
  "confidence": "HIGH",
  "findings": [
    {
      "category": "RESILIENCE",
      "severity": "HIGH",
      "file": "src/main/java/com/example/service/OrderService.java",
      "line": 17,
      "description": "RestClient HTTP call to payment-api.internal.company.com without Resilience4j circuit breaker protection. If the payment service becomes slow or unavailable, this will cause cascading failures.",
      "impact": "Without circuit breaker: 1) Thread pool exhaustion when payment service is slow (threads blocked waiting for response), 2) Continued failed attempts instead of failing fast, 3) Cascading failures propagating to upstream services, 4) Complete service outage affecting all order processing. Production impact: Orders cannot be processed, revenue loss, customer experience degradation.",
      "recommendation": "Implement Resilience4j circuit breaker pattern with fallback:\n\n```java\nimport io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;\nimport io.github.resilience4j.retry.annotation.Retry;\nimport io.github.resilience4j.timelimiter.annotation.TimeLimiter;\nimport org.springframework.stereotype.Service;\n\n@Service\npublic class OrderService {\n    \n    @CircuitBreaker(name = \"paymentService\", fallbackMethod = \"processPaymentFallback\")\n    @Retry(name = \"paymentService\")\n    @TimeLimiter(name = \"paymentService\")\n    public PaymentResponse processPayment(String orderId, double amount) {\n        return restClient.post()\n            .uri(\"/api/v1/payments\")\n            .body(new PaymentRequest(orderId, amount))\n            .retrieve()\n            .body(PaymentResponse.class);\n    }\n    \n    // Fallback method MUST have same signature + Exception parameter\n    private PaymentResponse processPaymentFallback(String orderId, double amount, Exception e) {\n        // Return cached response, queue for later processing, or graceful degradation\n        log.error(\"Payment service unavailable for order: {}\", orderId, e);\n        return PaymentResponse.builder()\n            .orderId(orderId)\n            .status(\"PENDING\")\n            .message(\"Payment queued for processing\")\n            .build();\n    }\n}\n```\n\nAdd to application.yml:\n```yaml\nresilience4j:\n  circuitbreaker:\n    instances:\n      paymentService:\n        registerHealthIndicator: true\n        failureRateThreshold: 50           # Open circuit at 50% failures\n        slowCallRateThreshold: 50          # Also consider slow calls\n        slowCallDurationThreshold: 2s       # Calls >2s are \"slow\"\n        slidingWindowSize: 10              # Evaluate last 10 calls\n        minimumNumberOfCalls: 5            # Need 5 calls before calculating\n        waitDurationInOpenState: 10s       # Wait 10s before half-open\n        permittedNumberOfCallsInHalfOpenState: 3\n        automaticTransitionFromOpenToHalfOpenEnabled: true\n        \n  timelimiter:\n    instances:\n      paymentService:\n        timeoutDuration: 2s                # Timeout after 2 seconds\n        \n  retry:\n    instances:\n      paymentService:\n        maxAttempts: 3\n        waitDuration: 500ms\n        retryExceptions:\n          - org.springframework.web.client.ResourceAccessException\n        ignoreExceptions:\n          - java.lang.IllegalArgumentException  # Don't retry validation errors\n```"
    },
    {
      "category": "DEPENDENCY",
      "severity": "MEDIUM",
      "file": "src/main/java/com/example/service/OrderService.java",
      "line": 12,
      "description": "New hard dependency on payment-api.internal.company.com. Service availability now coupled to external system uptime.",
      "impact": "Creates single point of failure. If payment API has lower SLA than this service (e.g., payment=99.5%, orders=99.9%), overall availability degrades to lowest common denominator. Deployment coupling: Cannot deploy orders service if payment API is down.",
      "recommendation": "1) Document SLA dependency in system architecture diagrams, 2) Implement async payment processing (queue payments for later), 3) Add monitoring for payment API health, 4) Consider circuit breaker dashboard for ops visibility, 5) Negotiate SLA alignment with payment team."
    }
  ],
  "test_recommendations": [
    "Integration test: Mock payment API with 5s delay, verify circuit breaker times out at 2s",
    "Integration test: Simulate 6 consecutive payment API failures, verify circuit opens and fallback is called",
    "Integration test: Verify circuit transitions from OPEN → HALF_OPEN → CLOSED after recovery",
    "Integration test: Verify fallback method returns PENDING status with queued message",
    "Load test: 200 concurrent order requests with payment API down, verify no thread pool exhaustion",
    "Chaos test: Kill payment API container mid-request, verify graceful degradation",
    "Monitoring test: Verify circuit breaker metrics exported to Prometheus (if using actuator)"
  ],
  "metadata": {
    "analyzed_files": 1,
    "patterns_checked": ["resilience4j", "circuit-breaker", "timeout", "retry", "fallback"],
    "spring_boot_version": "3.x",
    "analysis_duration_seconds": 3.5
  }
}
```

## Risk Assessment Rationale

**Impact Score: 35/40**
- HTTP call to critical payment service
- Affects all order processing (revenue-critical path)
- Can cause complete service outage
- Cascading failure potential to upstream services
- Thread pool exhaustion risk

**Likelihood Score: 35/40**
- External services WILL experience issues (network, load, deployments)
- Without circuit breaker, failures are guaranteed eventually
- High likelihood of production impact within first month
- Payment services are historically high-failure-rate dependencies

**Test Coverage Gap: 8/20**
- No resilience testing framework in place
- Circuit breaker tests needed
- Chaos testing required for confidence

**Total: 78/100 = HIGH**

---

## Why RestClient (Not RestTemplate or @FeignClient)?

### ✅ Modern Pattern (Spring Boot 3+)
```java
RestClient (Spring Boot 3.2+)  ← Use this
  - Fluent API
  - Better error handling
  - Reactive support ready
```

### ❌ Deprecated/Legacy Patterns
```java
@FeignClient                    ← Avoid (Netflix stack deprecated)
  - Requires spring-cloud-starter-openfeign
  - Heavier than needed
  - Most orgs migrating away

RestTemplate                    ← Avoid (maintenance mode since 2020)
  - Not removed but discouraged
  - RestClient is drop-in replacement
```

---

## Production Context

**Why This Matters:**
- Payment services are critical path
- Typical payment API p99 latency: 500ms-2s
- During incidents, can spike to 30s+
- Without timeout: threads blocked for 30s each
- With 50 concurrent orders: All 50 threads blocked = service down

**Real-World Example:**
```
Black Friday 2024: Payment API degraded (5s p99 latency)
Without circuit breaker: Orders service DOWN (thread exhaustion)
With circuit breaker: Orders service UP (failed fast, used fallback)
```

---

## Additional Notes

**Resilience4j vs Spring Cloud Circuit Breaker:**
- Resilience4j is the recommended library (lightweight, no Netflix dependencies)
- Spring Cloud Circuit Breaker is abstraction layer (can use Resilience4j underneath)
- For greenfield projects: Use Resilience4j directly

**Fallback Strategies:**
1. **Cached Response:** Return last successful payment status
2. **Async Queue:** Store payment request in queue for later processing
3. **Degraded Mode:** Allow order creation, mark payment as "PENDING"
4. **Alternative Provider:** Retry with backup payment processor

**Monitoring:**
- Enable Resilience4j actuator endpoints
- Export metrics to Prometheus/Grafana
- Alert on circuit state transitions (CLOSED → OPEN)
- Dashboard showing circuit health across all services
