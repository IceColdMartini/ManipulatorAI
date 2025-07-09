"""
API request and response models for ManipulatorAI.

This module defines all the Pydantic models used for API endpoints,
including webhook payloads, request validation, and response formatting.

Business Context:
- Webhook models handle Facebook/Instagram event processing
- Message processing models for AI pipeline integration
- Business logic models for branch decision making
- Error handling and validation models
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# WEBHOOK MODELS
# =============================================================================


class WebhookVerification(BaseModel):
    """
    Model for webhook verification process.

    Used during the initial webhook setup with Facebook/Instagram.
    """

    hub_mode: str = Field(alias="hub.mode", description="Webhook verification mode")
    hub_challenge: str = Field(alias="hub.challenge", description="Verification challenge")
    hub_verify_token: str = Field(alias="hub.verify_token", description="Verification token")

    class Config:
        populate_by_name = True


class WebhookUser(BaseModel):
    """User information from webhook events."""

    id: str = Field(description="Platform user ID")
    name: str | None = Field(default=None, description="User display name")
    username: str | None = Field(default=None, description="User handle/username")


class WebhookMessage(BaseModel):
    """Message data from webhook events."""

    mid: str = Field(description="Message ID")
    text: str | None = Field(default=None, description="Message text content")
    timestamp: int = Field(description="Message timestamp (Unix)")

    # Attachments (images, videos, etc.)
    attachments: list[dict[str, Any]] | None = Field(
        default=None, description="Message attachments"
    )

    # Quick replies and postbacks
    quick_reply: dict[str, str] | None = Field(default=None, description="Quick reply payload")

    postback: dict[str, str] | None = Field(default=None, description="Postback payload")


class WebhookMessaging(BaseModel):
    """Messaging event from webhook."""

    sender: WebhookUser = Field(description="Message sender")
    recipient: WebhookUser = Field(description="Message recipient")
    timestamp: int = Field(description="Event timestamp")
    message: WebhookMessage | None = Field(default=None, description="Message data")
    postback: dict[str, Any] | None = Field(default=None, description="Postback data")
    read: dict[str, Any] | None = Field(default=None, description="Read receipt")
    delivery: dict[str, Any] | None = Field(default=None, description="Delivery receipt")


class WebhookEntry(BaseModel):
    """Webhook entry containing multiple messaging events."""

    id: str = Field(description="Page/account ID")
    time: int = Field(description="Entry timestamp")
    messaging: list[WebhookMessaging] = Field(description="Messaging events")


class WebhookPayload(BaseModel):
    """
    Complete webhook payload from Facebook/Instagram.

    This is the root model for all incoming webhook events.
    """

    object: str = Field(description="Webhook object type (page/instagram)")
    entry: list[WebhookEntry] = Field(description="Webhook entries")


# =============================================================================
# BUSINESS LOGIC MODELS
# =============================================================================


class BranchDecision(BaseModel):
    """
    Model for two-branch control flow decision.

    Determines whether to use Manipulator or Convincer branch.
    """

    branch_type: str = Field(description="Branch type: 'manipulator' or 'convincer'")
    confidence: float = Field(ge=0.0, le=1.0, description="Decision confidence score")
    reasoning: str = Field(description="Why this branch was chosen")
    target_product_id: int | None = Field(
        default=None, description="Product ID for Manipulator branch"
    )


class KeywordExtractionRequest(BaseModel):
    """
    Request model for keyRetriever subsystem.

    Used to extract keywords from customer messages for product matching.
    """

    message_content: str = Field(min_length=1, description="Customer message to analyze")
    conversation_context: list[str] | None = Field(
        default=None, description="Previous messages for context"
    )
    customer_id: str = Field(description="Customer ID for context")
    platform: str = Field(description="Platform source")


class KeywordExtractionResponse(BaseModel):
    """
    Response model from keyRetriever subsystem.
    """

    keywords: list[str] = Field(description="Extracted keywords")
    confidence_scores: dict[str, float] = Field(description="Confidence per keyword")
    processing_time_ms: float = Field(description="Processing duration")
    context_used: bool = Field(description="Whether conversation context was used")


class ProductMatchingRequest(BaseModel):
    """
    Request model for tagMatcher subsystem.

    Finds products that correlate with extracted keywords.
    """

    keywords: list[str] = Field(description="Keywords to match against products")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Correlation threshold")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum products to return")
    exclude_product_ids: list[int] | None = Field(
        default=None, description="Product IDs to exclude from results"
    )


class ProductMatch(BaseModel):
    """Individual product match result."""

    product_id: int = Field(description="Matched product ID")
    correlation_score: float = Field(ge=0.0, le=1.0, description="Correlation strength")
    matching_tags: list[str] = Field(description="Tags that matched")
    product_name: str = Field(description="Product name")
    product_genre: str | None = Field(description="Product genre")


class ProductMatchingResponse(BaseModel):
    """
    Response model from tagMatcher subsystem.
    """

    matches: list[ProductMatch] = Field(description="Matched products")
    total_candidates: int = Field(description="Total products evaluated")
    processing_time_ms: float = Field(description="Processing duration")
    threshold_used: float = Field(description="Correlation threshold applied")


class ConversationGenerationRequest(BaseModel):
    """
    Request model for AI conversation generation.

    Used to generate contextual responses to customer messages.
    """

    customer_message: str = Field(description="Latest customer message")
    conversation_history: list[dict[str, str]] = Field(description="Previous conversation")
    matched_products: list[ProductMatch] = Field(description="Products to potentially mention")
    customer_context: dict[str, Any] = Field(description="Customer information and preferences")
    conversation_goal: str = Field(description="Current conversation objective")

    # AI generation parameters
    temperature: float | None = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=150, ge=10, le=500)
    include_product_recommendations: bool = Field(default=True)


class ConversationGenerationResponse(BaseModel):
    """
    Response model from AI conversation generation.
    """

    response_text: str = Field(description="Generated response text")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Response quality confidence")
    products_mentioned: list[int] = Field(description="Product IDs mentioned in response")
    conversation_state: str = Field(description="Suggested next conversation state")

    # AI metrics
    tokens_used: int = Field(description="Tokens consumed")
    generation_time_ms: float = Field(description="Generation duration")
    model_used: str = Field(description="AI model identifier")


# =============================================================================
# ERROR AND VALIDATION MODELS
# =============================================================================


class ErrorDetail(BaseModel):
    """Individual error detail."""

    field: str | None = Field(default=None, description="Field that caused the error")
    message: str = Field(description="Error message")
    code: str | None = Field(default=None, description="Error code")


class ErrorResponse(BaseModel):
    """
    Standardized error response model.

    Used for all API error responses to ensure consistency.
    """

    error: str = Field(description="Error type")
    message: str = Field(description="Human-readable error message")
    details: list[ErrorDetail] | None = Field(
        default=None, description="Detailed error information"
    )
    correlation_id: str | None = Field(default=None, description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    path: str | None = Field(default=None, description="API endpoint path")


class ValidationErrorResponse(ErrorResponse):
    """
    Specialized error response for validation failures.
    """

    error: str = Field(default="validation_error", description="Error type")
    invalid_fields: list[str] = Field(description="List of fields that failed validation")


# =============================================================================
# HEALTH CHECK AND MONITORING MODELS
# =============================================================================


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ComponentHealth(BaseModel):
    """Health status of individual system component."""

    status: HealthStatus = Field(description="Component health status")
    last_checked: datetime = Field(description="Last health check time")
    response_time_ms: float | None = Field(default=None, description="Component response time")
    error_message: str | None = Field(default=None, description="Error details if unhealthy")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional component info")


class HealthCheckResponse(BaseModel):
    """
    Comprehensive health check response.

    Used by monitoring systems to assess service health.
    """

    status: HealthStatus = Field(description="Overall system health")
    service: str = Field(description="Service name")
    version: str = Field(description="Service version")
    environment: str = Field(description="Deployment environment")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")

    # Component health details
    components: dict[str, ComponentHealth] = Field(description="Individual component health")

    # System metrics
    uptime_seconds: float | None = Field(default=None, description="Service uptime")
    memory_usage_mb: float | None = Field(default=None, description="Memory usage")
    cpu_usage_percent: float | None = Field(default=None, description="CPU usage")


class MetricsResponse(BaseModel):
    """
    System metrics and performance data.
    """

    requests_total: int = Field(description="Total requests processed")
    requests_per_minute: float = Field(description="Current request rate")
    avg_response_time_ms: float = Field(description="Average response time")
    error_rate_percent: float = Field(description="Error rate percentage")

    # AI-specific metrics
    ai_requests_total: int = Field(description="Total AI requests")
    avg_ai_response_time_ms: float = Field(description="Average AI response time")
    ai_tokens_used: int = Field(description="Total AI tokens consumed")

    # Database metrics
    db_connections_active: int = Field(description="Active database connections")
    db_query_avg_time_ms: float = Field(description="Average database query time")

    # Conversation metrics
    conversations_active: int = Field(description="Currently active conversations")
    conversations_qualified_today: int = Field(description="Leads qualified today")


# =============================================================================
# PAGINATION AND LISTING MODELS
# =============================================================================


class PaginationParams(BaseModel):
    """
    Standard pagination parameters for list endpoints.
    """

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str | None = Field(default=None, description="Field to sort by")
    sort_order: str | None = Field(
        default="desc", pattern="^(asc|desc)$", description="Sort direction"
    )


class ListResponse(BaseModel):
    """
    Generic list response with pagination metadata.
    """

    items: list[Any] = Field(description="List items")
    total: int = Field(description="Total items available")
    page: int = Field(description="Current page number")
    size: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there are more pages")
    has_prev: bool = Field(description="Whether there are previous pages")


# Type aliases for better code readability
WebhookEventID = str
MessageContent = str
CorrelationScore = float
ProcessingTime = float
