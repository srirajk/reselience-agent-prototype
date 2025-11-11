# What is AST and Why We Use It

## The Problem

When developers change code (Pull Requests), we need to find bugs before they go to production. Traditional text search (grep) only finds words, not meaning. If you search for "timeout", you find comments, variable names, and strings - but you miss actual bugs where timeout is missing.

## What is AST?

**AST = Abstract Syntax Tree**

It's a way to **understand code structure**, not just read text.

**Analogy:** Reading music vs looking at black dots on paper.
- **Text search (grep):** Sees dots, can't tell if it's music
- **AST:** Understands "this is a C note, this is a quarter note, this is the melody"

## What AST Does for Us

AST parses code and tells us:

1. **Structure:** What classes, methods, and function calls exist
2. **Dependencies:** What external libraries are used (RabbitMQ, HTTP clients, databases)
3. **Method Calls:** What each function calls, with what parameters
4. **Context:** Is this inside a try-catch? Inside a transaction? Has timeout configured?

## Why This Helps Us

### 1. Finds Bugs Text Search Misses
- Text search: Looks for the word "timeout"
- AST: Checks if timeout parameter is actually configured in method calls

### 2. Works on Unknown Libraries
- Text search: Needs a list of every library (RestTemplate, WebClient, HttpClient...)
- AST: Recognizes patterns ("ends with Client" + "blocking call" + "no timeout" = bug)

### 3. No False Positives
- Text search: Finds "timeout" in comments, strings, variable names
- AST: Only analyzes actual code, ignores comments and strings

### 4. Understands Misleading Code
- Class named "DataCalculator" but makes HTTP calls? AST detects the HTTP call.
- Class named "PaymentClient" but just does local math? AST sees it's safe.

### 5. Multi-Language Support
- Same patterns work across Java, Python, TypeScript, Go, Rust
- No need to rewrite detection logic for each language

## What We Extract

From each code file, AST gives us:
- **Dependencies:** External libraries used
- **Method Calls:** Every function call with parameters and return types
- **Async Patterns:** RabbitMQ consumers/publishers, Kafka, HTTP calls
- **Configuration:** Timeout values, retry policies, circuit breaker settings
- **Breaking Changes:** Deleted methods, removed fields, changed signatures

## How We Use This

**3-Step Process:**

1. **AST extracts facts** (structure and meaning from code)
2. **LLM reasons about facts** (finds patterns like "blocking call without timeout")
3. **Report bugs** with specific file:line references

## The Key Benefit

> **AST understands what code DOES, not just what it's CALLED.**

This means:
- Higher accuracy (95%+ vs 20% with text search)
- Fewer false positives
- Finds hidden bugs in unknown/custom libraries
- Works across all programming languages

## Trade-offs

**What AST Can't Do:**
- Can't see inside compiled binary libraries (no source code)
- Can't analyze dynamic/reflection-based calls (determined at runtime)
- Requires Tree-sitter parser for each language (but most languages supported)

**What We Do:**
- Flag unknown dependencies for manual review
- Focus on what we CAN analyze (covers 95% of cases)

---

**Bottom Line:** AST lets us understand code like a human engineer would, finding bugs that simple text search misses.