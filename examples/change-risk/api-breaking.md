# Example: API Breaking Change - Removed Optional Field

## Scenario
Removed the optional field `phone` from the `UserResponse` API model. While the field was marked as optional, some consumers may still depend on it.

## Code

### Before
```python
# src/api/models.py
from pydantic import BaseModel
from typing import Optional

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]  # This field exists
    created_at: str
```

### After
```python
# src/api/models.py
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    # phone field REMOVED
    created_at: str
```

## Expected Analysis

```json
{
  "risk_score": 45,
  "risk_level": "MEDIUM",
  "confidence": "HIGH",
  "findings": [
    {
      "category": "API_CHANGE",
      "severity": "MEDIUM",
      "file": "src/api/models.py",
      "line": 12,
      "description": "Removed optional field 'phone' from UserResponse. This is a breaking change if any consumers rely on this field, even though it was marked as optional.",
      "impact": "Downstream services or frontend applications expecting the 'phone' field will receive incomplete data. Depending on client implementation, this could cause: 1) Display issues (missing phone numbers), 2) Validation errors if clients check for field presence, 3) Data synchronization problems if phone numbers are stored elsewhere.",
      "recommendation": "1. Add deprecation warning to API documentation first. 2. Use API analytics to check if any consumers access the 'phone' field. 3. If yes, consider keeping the field with a null value for backward compatibility. 4. Add contract tests to verify API compatibility with all known consumers. 5. Coordinate with consumer teams before deployment."
    }
  ],
  "test_recommendations": [
    "Add contract tests using Pact or Spring Cloud Contract to verify API compatibility with all known consumers",
    "Add integration tests to ensure clients can handle the missing 'phone' field gracefully (test with existing client SDKs)",
    "Add API versioning tests if multiple API versions are supported",
    "Test error handling for legacy clients that may still expect the 'phone' field"
  ],
  "metadata": {
    "analyzed_files": 1,
    "patterns_checked": ["api-schema-changes"],
    "analysis_duration_seconds": 2.1
  }
}
```

## Risk Assessment Rationale

**Impact Score: 25/40**
- Field removal affects API contract
- Potentially impacts multiple consumers
- Data completeness issue but not data loss
- Not revenue-critical (contact info, not payment info)

**Likelihood Score: 15/40**
- Field was optional, so some clients may already handle absence
- However, clients often rely on optional fields being present
- Medium likelihood of actual breakage

**Test Coverage Gap: 5/20**
- Assuming some API tests exist
- But contract tests likely missing

**Total: 45/100 = MEDIUM**
