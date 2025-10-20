# Example: Low Risk - Added Logging Statement

## Scenario
Added a logging statement to an existing function. This is a low-risk, non-functional change that improves observability without affecting business logic.

## Code

```python
# src/services/order_service.py
import logging

logger = logging.getLogger(__name__)

class OrderService:
    def process_order(self, order_id: str):
        # NEW: Added logging for observability
        logger.info(f"Processing order: {order_id}", extra={"order_id": order_id})

        # Existing business logic (unchanged)
        order = self.repository.get_order(order_id)
        order.status = "PROCESSING"
        self.repository.save(order)

        return order
```

## Expected Analysis

```json
{
  "risk_score": 5,
  "risk_level": "LOW",
  "confidence": "HIGH",
  "findings": [],
  "test_recommendations": [
    "Verify logging output in development environment to ensure correct format",
    "Confirm no sensitive data (PII, credentials) is logged",
    "Validate that logging does not impact performance (logging should be asynchronous)",
    "Ensure log level is appropriate (INFO for business events, DEBUG for detailed traces)"
  ],
  "metadata": {
    "analyzed_files": 1,
    "patterns_checked": ["logging", "pii-exposure"],
    "analysis_duration_seconds": 1.2
  }
}
```

## Risk Assessment Rationale

**Impact Score: 5/40**
- Non-functional change
- No business logic affected
- Improves observability (positive)
- No user-facing impact

**Likelihood Score: 0/40**
- Adding logs very rarely causes issues
- No breaking changes possible
- Negligible failure likelihood

**Test Coverage Gap: 0/20**
- No tests needed for logging
- Existing tests still valid

**Total: 5/100 = LOW**

**Note:** While this is low risk, it's still important to:
- Check for PII in logs (GDPR/privacy compliance)
- Verify log volume doesn't impact performance
- Ensure structured logging format is followed
