```ascii

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      DATA FLOW                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘

GitHub PR Event  →  EventBridge  →  Lambda  →  ALB  →  FastAPI (ECS)  →  S3


┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         Solution Design for Resilient Agent                                            │
│                         DEPLOYMENT ARCHITECTURE - AWS Cloud Infrastructure                             │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘


                                    ┌──────────────┐
                                    │              │
                                    │   GitHub     │
                                    │   PR Event   │
                                    │              │
                                    └──────┬───────┘
                                           │
                                           │ Webhook (HTTPS)
                                           │
                                           ▼
                    ┌──────────────────────────────────────────┐
                    │                                          │
                    │      Amazon EventBridge                  │
                    │      (Event Bus + Rules)                 │
                    │                                          │
                    └──────────────────┬───────────────────────┘
                                       │
                                       │ Event Trigger
                                       │
                                       ▼
                    ┌──────────────────────────────────────────┐
                    │                                          │
                    │      AWS Lambda                          │
                    │      (PR Handler Function)               │
                    │                                          │
                    │      • Validate Payload                  │
                    │      • Extract PR Data                   │
                    │      • Enrich Metadata                   │
                    │                                          │
                    └──────────────────┬───────────────────────┘
                                       │
                                       │ HTTP POST /analyze-pr
                                       │
                                       ▼
                    ┌──────────────────────────────────────────┐
                    │                                          │
                    │   Application Load Balancer (ALB)        │
                    │                                          │
                    └──────────────────┬───────────────────────┘
                                       │
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                                                             │
        │              Amazon ECS Cluster (Fargate)                   │
        │                                                             │
        │   ┌─────────────────────────────────────────────────┐       │
        │   │                                                 │       │
        │   │         FastAPI Application                     │       │
        │   │         (ECS Service)                           │       │
        │   │                                                 │       │
        │   │   Endpoints:                                    │       │
        │   │   • POST /analyze-pr (async, returns job_id)    │       │
        │   │   • GET  /status/{job_id}                       │       │
        │   │   • GET  /report/{job_id}                       │       │
        │   │   • GET  /health                                │       │
        │   │                                                 │       │
        │   │   Process:                                      │       │
        │   │   1. POST /analyze-pr → returns job_id          │       │
        │   │   2. Spawn subprocess (background)              │       │
        │   │   3. Run analysis pipeline                      │       │
        │   │   4. Generate artifacts                         │       │
        │   │   5. Upload to S3                               │       │
        │   │   6. GET /report/{job_id} → returns summary     │       │
        │   │                                                 │       │
        │   └─────────────────────────────────────────────────┘       │
        │                                                             │
        └────────────────────────────┬────────────────────────────────┘
                                     │
                                     │ Upload Artifacts
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │                     │
                          │     Amazon S3       │
                          │                     │
                          │   Bucket Structure: │
                          │   └── {repo}/       │
                          │       └── pr-{NUM}/ │
                          │                     │
                          └─────────────────────┘





┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    KEY COMPONENTS                                                       │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│   EventBridge       │  • Receives GitHub webhooks
│                     │  • Routes PR events to Lambda
└─────────────────────┘

┌─────────────────────┐
│   Lambda            │  • Processes PR events
│   (PR Handler)      │  • Calls FastAPI endpoint
└─────────────────────┘

┌─────────────────────┐
│   ALB               │  • Load balances requests
│                     │  • Internal only
└─────────────────────┘

┌─────────────────────┐
│   ECS Cluster       │  • Runs FastAPI container
│                     │  • Auto-scaling (2-x tasks)
└─────────────────────┘

┌─────────────────────┐
│   FastAPI           │  • Analysis orchestration
│                     │  • Subprocess management
└─────────────────────┘

┌─────────────────────┐
│   S3                │  • Stores analysis results
│                     │  • Artifacts & reports
└─────────────────────┘




```