# ManipulatorAI

A human-like AI Agent microservice designed to conduct first-time conversations with potential customers and persuasively guide them toward registration, seamlessly transitioning the workflow to the Onboarder Agent.

## Stage

- **Primary Function**: The first direct communication with a potential customer

## Goal

- **Objective**: Proceed new potential customers to the onboarding agent through intelligent conversation and persuasion

## Description

ManipulatorAI is a critical component of a comprehensive multi-agent SaaS platform that replaces human-powered customer communication with intelligent AI agents. The system is designed to serve business owners who want to automate their consumer attraction and engagement processes.

### Core Functionality

The agent operates in social media environments (Facebook/Instagram) where business clients advertise their products. When a potential customer interacts with an ad (likes, comments, or clicks), ManipulatorAI is automatically triggered to initiate a human-like conversation.

**Key Features:**
- Cordial greeting and introductory conversation
- Product-focused dialogue based on user interaction
- Human-like persuasion techniques to encourage registration
- Seamless handoff to the Onboarding Agent upon successful conversion
- Cross-product recommendations for uninterested customers
- Persistent yet polite engagement strategies

### Platform Integration

ManipulatorAI is part of a larger ecosystem where multiple AI agents work together to:
- Attract and engage consumers automatically
- Provide business owners with comprehensive platform oversight
- Replace traditional human sales interactions with intelligent automation
- Guide customers through the entire engagement funnel

## Control Flow

### Overview

1. **Webhook Trigger**: Facebook/Instagram webhooks send notifications when users interact with ads or posts
2. **Queue Processing**: Redis queue system ensures no data loss during high-traffic periods
3. **AI Conversation**: The agent initiates and maintains customer conversations
4. **LLM Integration**: Azure OpenAI models power response generation through API calls

### Product Database (Knowledge-Base)

The system maintains a PostgreSQL database with comprehensive product information:

**Schema Structure:**
- `product_id` (Unique identifier)
- `product_attributes` (JSON data containing key-value pairs: price, color, type, etc.)
- `product_tag` (Critical for cross-referencing and product matching)
- `product_description` (Detailed product information)

The `product_tag` column is essential for correlation-based product matching and recommendations.

## Operational Branches

### Branch 1: Manipulator
**Trigger**: User interaction with ads/posts
- Direct product identification from interaction data
- Immediate access to relevant product descriptions via product ID
- Proactive engagement approach

### Branch 2: Convincer
**Trigger**: Customer-initiated contact
- Text analysis and keyword extraction required
- Two-step processing system for product identification

#### keyRetriever Sub-system
**Function**: Intelligent keyword extraction from customer text
- **Input**: Customer message + business product summary
- **Process**: LLM-powered topic selection and keyword identification
- **Output**: Relevant keywords related to business products

#### tagMatcher Sub-system
**Function**: Product correlation and matching
- **Input**: Keywords from keyRetriever + database product_tags
- **Process**: Correlation scoring and top-K retrieval (≥80% correlation threshold)
- **Output**: Matched product_id(s) for conversation context

## Conversation Management

### Pre-Conversation Setup
1. Product identification through appropriate branch workflow
2. Database query for product_description(s)
3. Context preparation for LLM interaction

### Prompt Engineering Strategy

**Welcome Protocol:**
- One-time welcoming prompt for first interactions
- Warm, human-like greeting
- Product genre summarization based on identified products
- Interest confirmation and assistance offering

**Conversation Guidelines:**
- Custom-tailored responses specific to business products
- Polite yet persuasive communication style
- Persistence with uninterested customers
- Cross-product recommendations (70-80% correlation threshold)
- Graceful conversation conclusion with future engagement invitation

### Database Management

**Conversation Storage**: MongoDB for conversation history
- Complete context preservation for ongoing conversations
- Historical data for LLM context feeding
- Seamless conversation continuity across interactions

## Technical Architecture

- **Frontend Triggers**: Facebook/Instagram webhooks
- **Queue Management**: Redis for request processing
- **Primary Database**: PostgreSQL for product knowledge-base
- **Conversation Storage**: MongoDB for chat history
- **AI Processing**: Azure OpenAI API integration
- **Architecture**: Microservice-based design for scalability

## Integration Points

- **Input**: Social media webhook notifications, customer messages
- **Output**: Qualified leads transferred to Onboarding Agent
- **Monitoring**: Business owner dashboard integration
- **Scalability**: Multi-client support with isolated product databases
