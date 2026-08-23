# SearchIntel AI — Data Model V1

## Core Entities

### Project
Represents one SearchIntel monitoring project.

Examples:
- ChargeOps AI GEO Monitoring
- Company X Search Visibility

### Brand
Represents any brand discovered or monitored.

Examples:
- ChargeOps AI
- Competitor A
- Competitor B

We do NOT create a separate Competitor table.
A competitor is simply another Brand with a different role.

### ProjectBrand
Links brands to projects.

Roles:
- target
- competitor

### Website
Represents a brand's website/domain.

### Page
Represents an individual crawled webpage.

### Prompt
Represents a reusable AI-search question.

### AIEngine
Represents the user-facing AI/search system.

Examples:
- ChatGPT
- Gemini
- Claude
- Perplexity
- Google AI Overviews

### AIModel
Represents the underlying model when known.

### AIRun
Represents one execution of one prompt.

A single prompt can have many runs over time.

### AIResponse
Stores the response produced by an AI run.

### BrandMention
Stores brands detected in an AI response.

### Citation
Stores URLs/domains cited in an AI response.

### MetricSnapshot
Stores calculated visibility metrics at a point in time.