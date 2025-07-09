"""
Data models package for ManipulatorAI.

This package contains all data models used throughout the application:
- Product models for PostgreSQL (SQLModel)
- Conversation models for MongoDB (Pydantic)
- API request/response models (Pydantic)
- Business logic models for AI subsystems

The models are designed to be type-safe, well-validated, and support
both database operations and API serialization.
"""

# API models
from .api import (  # Webhook models; Business logic models; Error and validation models; Health and monitoring models; Pagination models; Type aliases
    BranchDecision,
    ComponentHealth,
    ConversationGenerationRequest,
    ConversationGenerationResponse,
    CorrelationScore,
    ErrorDetail,
    ErrorResponse,
    HealthCheckResponse,
    HealthStatus,
    KeywordExtractionRequest,
    KeywordExtractionResponse,
    ListResponse,
    MessageContent,
    MetricsResponse,
    PaginationParams,
    ProcessingTime,
    ProductMatch,
    ProductMatchingRequest,
    ProductMatchingResponse,
    ValidationErrorResponse,
    WebhookEntry,
    WebhookEventID,
    WebhookMessage,
    WebhookMessaging,
    WebhookPayload,
    WebhookUser,
    WebhookVerification,
)

# Conversation models (MongoDB)
from .conversation import (
    Conversation,
    ConversationBase,
    ConversationCreate,
    ConversationID,
    ConversationPublic,
    ConversationsPublic,
    ConversationState,
    ConversationStats,
    ConversationUpdate,
    CustomerID,
    LeadQualification,
    Message,
    MessageCreate,
    MessageID,
    MessageRole,
    MessageType,
    Platform,
)

# Product models (PostgreSQL)
from .product import (
    Product,
    ProductBase,
    ProductCreate,
    ProductGenre,
    ProductID,
    ProductPublic,
    ProductsPublic,
    ProductTag,
    ProductUpdate,
)

# Export all models for convenient importing
__all__ = [
    # Product models
    "Product",
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductPublic",
    "ProductsPublic",
    "ProductID",
    "ProductTag",
    "ProductGenre",
    # Conversation models
    "Conversation",
    "ConversationBase",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationPublic",
    "ConversationsPublic",
    "ConversationState",
    "ConversationStats",
    "Message",
    "MessageCreate",
    "MessageRole",
    "MessageType",
    "LeadQualification",
    "Platform",
    "ConversationID",
    "CustomerID",
    "MessageID",
    # API models
    "WebhookPayload",
    "WebhookEntry",
    "WebhookMessaging",
    "WebhookMessage",
    "WebhookUser",
    "WebhookVerification",
    "BranchDecision",
    "KeywordExtractionRequest",
    "KeywordExtractionResponse",
    "ProductMatchingRequest",
    "ProductMatchingResponse",
    "ProductMatch",
    "ConversationGenerationRequest",
    "ConversationGenerationResponse",
    "ErrorResponse",
    "ErrorDetail",
    "ValidationErrorResponse",
    "HealthCheckResponse",
    "HealthStatus",
    "ComponentHealth",
    "MetricsResponse",
    "PaginationParams",
    "ListResponse",
    "WebhookEventID",
    "MessageContent",
    "CorrelationScore",
    "ProcessingTime",
]
