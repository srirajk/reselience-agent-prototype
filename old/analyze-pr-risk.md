---
name: analyze-pr-risk
description: Analyze PR changes for production risks and get test recommendations
example: analyze-pr-risk
---

# PR Risk Analysis

Analyzes code changes in a PR for production risks including:
- New failure modes (missing timeouts, circuit breakers, retries)
- Breaking API changes
- Test coverage gaps

## Usage

```bash
# Analyze current branch against main
analyze-pr-risk

# Analyze specific branch
analyze-pr-risk --branch feature/payment-api

# Analyze specific files
analyze-pr-risk src/main/java/payment/PaymentService.java
```

## What it analyzes

**Languages Supported:**
- Java (Spring Boot, Feign, JPA)
- Node.js (Express, axios, fetch)
- React (fetch, error boundaries)
- Android (Retrofit, Kotlin coroutines)

**Risks Detected:**
- External API calls without circuit breakers
- HTTP calls without timeouts
- Async operations without error handling
- Breaking REST API changes
- Missing test coverage

## Output

Returns JSON with:
- Risk severity (HIGH/MEDIUM/LOW)
- Specific findings with file:line references
- Impact explanations
- Fix recommendations
- Required test types

## Examples

**High Risk Finding:**
```json
{
  "severity": "HIGH",
  "file": "PaymentService.java",
  "line": 45,
  "pattern": "@FeignClient without @CircuitBreaker",
  "test_needed": "Integration test with circuit breaker simulation"
}
```

## When to use

- ✅ Before submitting PR for review
- ✅ During code review process
- ✅ Before merging to main
- ✅ As part of CI/CD pipeline
