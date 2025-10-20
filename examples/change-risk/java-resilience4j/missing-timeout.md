# Example: @Async Method Without Timeout (Spring Boot + Resilience4j)

## Scenario
New asynchronous method for sending notifications without timeout configuration. Uses Spring's @Async but lacks timeout protection, which can exhaust thread pools if the external notification service hangs.

## Code

### After (Problematic Change)
```java
// src/main/java/com/example/service/NotificationService.java
package com.example.service;

import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class NotificationService {
    private final RestClient restClient;

    public NotificationService(RestClient.Builder builder) {
        this.restClient = builder
            .baseUrl("https://notification-api.external.com")
            .build();
    }

    @Async
    public void sendOrderConfirmation(String userId, String orderId) {
        // ❌ No timeout configured
        // ❌ No @TimeLimiter annotation
        // ❌ No circuit breaker for external API
        // ❌ Thread will block indefinitely if notification-api is slow

        NotificationRequest request = new NotificationRequest(
            userId,
            "ORDER_CONFIRMATION",
            Map.of("orderId", orderId)
        );

        restClient.post()
            .uri("/api/v1/notifications")
            .body(request)
            .retrieve()
            .toBodilessEntity();
    }
}
```

### Configuration (Also Problematic)
```java
// src/main/java/com/example/config/AsyncConfig.java
package com.example.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;

@Configuration
@EnableAsync
public class AsyncConfig {
    // ❌ No custom executor configured
    // ❌ Uses default SimpleAsyncTaskExecutor (unlimited threads!)
    // ❌ No thread pool limits
}
```

## Expected Analysis

```json
{
  "risk_score": 72,
  "risk_level": "HIGH",
  "confidence": "HIGH",
  "findings": [
    {
      "category": "RESILIENCE",
      "severity": "HIGH",
      "file": "src/main/java/com/example/service/NotificationService.java",
      "line": 18,
      "description": "@Async method calling external notification-api.external.com without timeout configuration. Combined with missing thread pool limits, this can cause thread exhaustion and memory issues.",
      "impact": "Without timeout: 1) Threads block indefinitely if notification API is slow or unresponsive, 2) Default SimpleAsyncTaskExecutor creates unlimited threads (can exhaust memory with OutOfMemoryError), 3) Notification backlogs accumulate without visibility, 4) Application becomes unresponsive, 5) Cascading failures to all async operations. Production impact: Service crashes with OOM, requires restart, potential data loss of in-flight notifications.",
      "recommendation": "Implement Resilience4j TimeLimiter with bounded thread pool:\n\n**Step 1: Add @TimeLimiter annotation**\n```java\nimport io.github.resilience4j.timelimiter.annotation.TimeLimiter;\nimport io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;\nimport java.util.concurrent.CompletableFuture;\n\n@Service\npublic class NotificationService {\n    \n    @Async(\"notificationExecutor\")  // Use named executor\n    @CircuitBreaker(name = \"notificationApi\", fallbackMethod = \"sendNotificationFallback\")\n    @TimeLimiter(name = \"notificationApi\")\n    public CompletableFuture<Void> sendOrderConfirmation(String userId, String orderId) {\n        NotificationRequest request = new NotificationRequest(\n            userId,\n            \"ORDER_CONFIRMATION\",\n            Map.of(\"orderId\", orderId)\n        );\n        \n        restClient.post()\n            .uri(\"/api/v1/notifications\")\n            .body(request)\n            .retrieve()\n            .toBodilessEntity();\n            \n        return CompletableFuture.completedFuture(null);\n    }\n    \n    // Fallback: Log failure and queue for retry\n    private CompletableFuture<Void> sendNotificationFallback(String userId, String orderId, Exception e) {\n        log.error(\"Notification failed for order: {}, user: {}\", orderId, userId, e);\n        // Queue for later retry or send via alternative channel\n        notificationQueue.add(new NotificationJob(userId, orderId));\n        return CompletableFuture.completedFuture(null);\n    }\n}\n```\n\n**Step 2: Configure bounded thread pool**\n```java\nimport org.springframework.context.annotation.Bean;\nimport org.springframework.context.annotation.Configuration;\nimport org.springframework.scheduling.annotation.EnableAsync;\nimport org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;\nimport java.util.concurrent.Executor;\n\n@Configuration\n@EnableAsync\npublic class AsyncConfig {\n    \n    @Bean(name = \"notificationExecutor\")\n    public Executor notificationExecutor() {\n        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();\n        executor.setCorePoolSize(5);           // Start with 5 threads\n        executor.setMaxPoolSize(10);           // Max 10 threads\n        executor.setQueueCapacity(100);        // Queue up to 100 tasks\n        executor.setThreadNamePrefix(\"notification-\");\n        executor.setRejectedExecutionHandler(\n            new ThreadPoolExecutor.CallerRunsPolicy()  // Backpressure\n        );\n        executor.initialize();\n        return executor;\n    }\n}\n```\n\n**Step 3: Add Resilience4j configuration**\n```yaml\nresilience4j:\n  timelimiter:\n    instances:\n      notificationApi:\n        timeoutDuration: 3s          # Timeout after 3 seconds\n        cancelRunningFuture: true    # Cancel the task on timeout\n        \n  circuitbreaker:\n    instances:\n      notificationApi:\n        failureRateThreshold: 50\n        slowCallRateThreshold: 50\n        slowCallDurationThreshold: 2s\n        slidingWindowSize: 10\n        waitDurationInOpenState: 30s  # Longer wait for external service\n```"
    },
    {
      "category": "RESILIENCE",
      "severity": "MEDIUM",
      "file": "src/main/java/com/example/config/AsyncConfig.java",
      "line": 8,
      "description": "Missing custom executor configuration for @Async. Uses default SimpleAsyncTaskExecutor which creates unbounded threads.",
      "impact": "SimpleAsyncTaskExecutor creates a new thread for each task without pooling. Under load (e.g., 1000 simultaneous notifications), this creates 1000 threads, leading to: 1) Memory exhaustion (each thread ~1MB stack), 2) CPU thrashing from context switching, 3) OutOfMemoryError crashes, 4) Slow garbage collection.",
      "recommendation": "Replace with ThreadPoolTaskExecutor (see code above). Key benefits: 1) Bounded thread count prevents resource exhaustion, 2) Task queue provides backpressure, 3) RejectedExecutionHandler controls overload behavior, 4) Thread reuse improves performance."
    }
  ],
  "test_recommendations": [
    "Integration test: Mock notification API with 10s delay, verify timeout triggers at 3s",
    "Integration test: Verify fallback method is called on timeout",
    "Integration test: Verify notification is queued for retry after fallback",
    "Load test: Send 200 simultaneous notifications, verify thread pool doesn't exceed 10 threads",
    "Load test: Send 150 notifications (>queue capacity 100), verify CallerRunsPolicy provides backpressure",
    "Chaos test: Kill notification API mid-request, verify circuit breaker opens",
    "Monitoring test: Verify thread pool metrics (active threads, queue size) are exposed",
    "Stress test: Continuously send notifications while API is down for 2 minutes, verify no memory leak"
  ],
  "metadata": {
    "analyzed_files": 2,
    "patterns_checked": ["async", "timeout", "thread-pool", "timelimiter", "circuit-breaker"],
    "spring_boot_version": "3.x",
    "analysis_duration_seconds": 4.2
  }
}
```

## Risk Assessment Rationale

**Impact Score: 32/40**
- Can cause OutOfMemoryError (service crash)
- Affects all async operations (not just notifications)
- Memory exhaustion is high-severity issue
- Requires service restart (downtime)

**Likelihood Score: 30/40**
- External notification services frequently experience slowness
- High load scenarios (Black Friday) will trigger issue
- Async + unlimited threads is common anti-pattern
- Likely to manifest within first high-traffic event

**Test Coverage Gap: 10/20**
- No async load testing
- No thread pool monitoring
- No timeout validation

**Total: 72/100 = HIGH**

---

## Why @TimeLimiter (Not Just RestClient Timeout)?

### ❌ RestClient Timeout Alone (Insufficient)
```java
RestClient restClient = builder
    .requestFactory(new SimpleClientHttpRequestFactory() {{
        setConnectTimeout(Duration.ofSeconds(2));
        setReadTimeout(Duration.ofSeconds(3));
    }})
    .build();
```
**Problem:** Timeout applies to HTTP call, but @Async thread remains allocated until timeout expires. With slow external API (3s timeout) × 100 concurrent calls = 100 threads blocked for 3s each.

### ✅ @TimeLimiter (Correct)
```java
@TimeLimiter(name = "notificationApi")  // Wraps entire async operation
@Async("boundedExecutor")              // Uses bounded thread pool
```
**Benefits:**
1. Cancels operation at timeout (doesn't wait for HTTP timeout)
2. Frees thread immediately for reuse
3. Works with CompletableFuture for composable async
4. Integrates with circuit breaker

---

## Production Context

**Real-World Scenario:**

```
Day 1: Notification API p99 = 200ms (normal)
  → 5 core threads handle 50 notifications/second easily

Day 30: Marketing campaign sends 10,000 notifications
  → Notification API degrades to 5s p99
  → Without timeout: 10,000 threads created
  → Memory: 10,000 threads × 1MB = 10GB (OOM!)
  → Service crashes

With TimeLimiter:
  → Timeout at 3s
  → Max 10 threads + 100 queued
  → Circuit breaker opens after 50% failures
  → Service continues operating (degraded mode)
  → Notifications queued for retry
```

**Monitoring Metrics to Track:**
```java
// Expose via Spring Boot Actuator
- notification.executor.active.threads      // Should stay ≤10
- notification.executor.queue.size          // Alert if >80
- resilience4j.timelimiter.calls.timeout    // Track timeout rate
- resilience4j.circuitbreaker.state         // CLOSED/OPEN/HALF_OPEN
```

---

## Common Pitfalls

### ❌ Pitfall 1: Void Return Type
```java
@Async
@TimeLimiter(name = "api")
public void sendNotification() {  // Won't work!
    // TimeLimiter requires CompletableFuture return type
}
```

### ✅ Correct:
```java
@Async
@TimeLimiter(name = "api")
public CompletableFuture<Void> sendNotification() {
    // ...
    return CompletableFuture.completedFuture(null);
}
```

### ❌ Pitfall 2: Forgetting Named Executor
```java
@Async  // Uses default unbounded executor!
```

### ✅ Correct:
```java
@Async("notificationExecutor")  // Uses bounded pool
```

---

## Alternative: CompletableFuture.orTimeout()

For simple cases without Resilience4j:

```java
public void sendNotification(String userId, String orderId) {
    CompletableFuture
        .supplyAsync(() -> {
            return restClient.post()...
        }, boundedExecutor)
        .orTimeout(3, TimeUnit.SECONDS)  // Built-in timeout
        .exceptionally(e -> {
            log.error("Notification timeout", e);
            return null;  // Fallback
        });
}
```

**When to use:**
- Simple timeout needs
- No circuit breaker required
- Prefer lightweight approach

**When to use @TimeLimiter:**
- Need circuit breaker integration
- Want centralized config (YAML)
- Need metrics/monitoring
- Production resilience requirements
