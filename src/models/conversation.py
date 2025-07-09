"""
Conversation data models for MongoDB using Pydantic.

This module defines conversation-related models stored in MongoDB.
Conversations track the complete interaction history between ManipulatorAI
and customers across social media platforms.

Business Context:
- Conversations have states: active, qualified, abandoned
- Messages include context for AI response generation
- Lead qualification status determines handoff to Onboarding Agent
- Platform-specific metadata for webhook integration
- Correlation tracking for customer journey analytics
"""

from datetime import datetime
from enum import Enum
from typing import Any

from bson import ObjectId
from pydantic import BaseModel, Field


class ConversationState(str, Enum):
    """
    Conversation lifecycle states.

    These states drive the business logic for conversation management
    and determine when to hand off to the Onboarding Agent.
    """

    ACTIVE = "active"  # Ongoing conversation
    QUALIFIED = "qualified"  # Lead qualified, ready for handoff
    ABANDONED = "abandoned"  # Customer stopped responding
    COMPLETED = "completed"  # Successfully handed off
    FAILED = "failed"  # Conversation failed/error occurred


class Platform(str, Enum):
    """Supported social media platforms."""

    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"  # Future platform support
    TELEGRAM = "telegram"  # Future platform support


class MessageRole(str, Enum):
    """Message sender role in conversation."""

    CUSTOMER = "customer"  # Message from customer
    ASSISTANT = "assistant"  # Message from ManipulatorAI
    SYSTEM = "system"  # System/platform messages


class MessageType(str, Enum):
    """Type of message content."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    STICKER = "sticker"
    REACTION = "reaction"


class Message(BaseModel):
    """
    Individual message within a conversation.

    Stores complete message history for context-aware AI responses
    and conversation analytics.
    """

    id: str = Field(description="Unique message ID from platform")
    role: MessageRole = Field(description="Who sent the message")
    content: str = Field(description="Message text content")
    message_type: MessageType = Field(default=MessageType.TEXT, description="Type of message")
    timestamp: datetime = Field(description="When message was sent")

    # Platform-specific metadata
    platform_data: dict[str, Any] = Field(
        default_factory=dict, description="Platform-specific message metadata"
    )

    # AI processing metadata
    processed_at: datetime | None = Field(
        default=None, description="When AI processed this message"
    )

    processing_duration_ms: float | None = Field(
        default=None, description="Time taken to process message"
    )

    # Business context extraction results
    extracted_keywords: list[str] = Field(
        default_factory=list, description="Keywords extracted by keyRetriever subsystem"
    )

    matched_products: list[int] = Field(
        default_factory=list, description="Product IDs matched by tagMatcher subsystem"
    )

    correlation_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Best correlation score from tagMatcher"
    )


class LeadQualification(BaseModel):
    """
    Lead qualification assessment data.

    Tracks the AI's assessment of lead quality and readiness
    for handoff to the Onboarding Agent.
    """

    is_qualified: bool = Field(description="Whether lead is qualified")
    confidence_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="AI confidence in qualification assessment"
    )

    qualification_reasons: list[str] = Field(
        default_factory=list, description="Reasons for qualification decision"
    )

    interested_products: list[int] = Field(
        default_factory=list, description="Product IDs customer showed interest in"
    )

    budget_indicators: list[str] = Field(
        default_factory=list, description="Customer statements indicating budget/buying intent"
    )

    urgency_level: str | None = Field(
        default=None, description="Assessed urgency level (low/medium/high)"
    )

    next_actions: list[str] = Field(
        default_factory=list, description="Recommended next actions for Onboarding Agent"
    )

    assessed_at: datetime = Field(
        default_factory=datetime.utcnow, description="When qualification was assessed"
    )


class ConversationBase(BaseModel):
    """
    Base conversation model with shared fields.
    """

    # Customer identification
    customer_id: str = Field(description="Unique customer ID from platform")
    customer_name: str | None = Field(default=None, description="Customer display name")
    customer_username: str | None = Field(default=None, description="Customer username/handle")

    # Platform information
    platform: Platform = Field(description="Social media platform")
    platform_conversation_id: str = Field(description="Platform-specific conversation ID")

    # Conversation state
    state: ConversationState = Field(
        default=ConversationState.ACTIVE, description="Current conversation state"
    )

    # Business context
    branch_type: str | None = Field(
        default=None, description="Which business logic branch (manipulator/convincer)"
    )

    target_product_id: int | None = Field(
        default=None, description="Direct product ID for Manipulator branch"
    )

    # Timestamps
    started_at: datetime = Field(
        default_factory=datetime.utcnow, description="Conversation start time"
    )
    last_message_at: datetime | None = Field(default=None, description="Last message timestamp")
    qualified_at: datetime | None = Field(default=None, description="When lead was qualified")
    completed_at: datetime | None = Field(default=None, description="When conversation completed")

    # Correlation tracking
    correlation_id: str | None = Field(default=None, description="Request correlation ID")

    # Metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional conversation metadata"
    )


class Conversation(ConversationBase):
    """
    Complete conversation model for MongoDB storage.

    This is the main document stored in MongoDB containing the full
    conversation history and all related metadata.
    """

    # MongoDB ObjectId
    id: str | None = Field(default=None, alias="_id", description="MongoDB document ID")

    # Message history
    messages: list[Message] = Field(default_factory=list, description="Complete message history")

    # Lead qualification
    lead_qualification: LeadQualification | None = Field(
        default=None, description="Lead qualification assessment"
    )

    # Performance metrics
    total_messages: int = Field(default=0, description="Total number of messages")
    ai_response_count: int = Field(default=0, description="Number of AI responses sent")
    avg_response_time_ms: float | None = Field(default=None, description="Average AI response time")

    # Conversation outcome
    outcome: str | None = Field(default=None, description="Final conversation outcome")
    handoff_data: dict[str, Any] | None = Field(
        default=None, description="Data package for Onboarding Agent handoff"
    )

    class Config:
        """Pydantic configuration for MongoDB integration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class ConversationCreate(ConversationBase):
    """
    Model for creating new conversations.

    Used when starting a new conversation from webhook events.
    """

    pass


class ConversationUpdate(BaseModel):
    """
    Model for updating conversation fields.

    Supports partial updates to conversation state and metadata.
    """

    state: ConversationState | None = Field(default=None)
    customer_name: str | None = Field(default=None)
    customer_username: str | None = Field(default=None)
    target_product_id: int | None = Field(default=None)
    last_message_at: datetime | None = Field(default=None)
    qualified_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    outcome: str | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)


class ConversationPublic(BaseModel):
    """
    Public conversation model for API responses.

    Excludes sensitive internal data while providing conversation overview.
    """

    id: str = Field(description="Conversation ID")
    customer_id: str = Field(description="Customer ID")
    customer_name: str | None = Field(description="Customer name")
    platform: Platform = Field(description="Platform")
    state: ConversationState = Field(description="Current state")
    branch_type: str | None = Field(description="Business logic branch")
    target_product_id: int | None = Field(description="Target product ID")
    started_at: datetime = Field(description="Start time")
    last_message_at: datetime | None = Field(description="Last message time")
    total_messages: int = Field(description="Message count")
    is_qualified: bool = Field(description="Whether lead is qualified")


class ConversationsPublic(BaseModel):
    """
    Model for paginated conversation list responses.
    """

    conversations: list[ConversationPublic] = Field(description="List of conversations")
    total: int = Field(description="Total conversation count")
    page: int = Field(description="Current page")
    size: int = Field(description="Page size")
    pages: int = Field(description="Total pages")


class MessageCreate(BaseModel):
    """
    Model for adding new messages to conversations.
    """

    role: MessageRole = Field(description="Message sender")
    content: str = Field(min_length=1, description="Message content")
    message_type: MessageType = Field(default=MessageType.TEXT)
    platform_data: dict[str, Any] = Field(default_factory=dict)


class ConversationStats(BaseModel):
    """
    Conversation analytics and statistics model.
    """

    total_conversations: int = Field(description="Total number of conversations")
    active_conversations: int = Field(description="Currently active conversations")
    qualified_leads: int = Field(description="Qualified leads count")
    completion_rate: float = Field(description="Conversation completion rate")
    avg_messages_per_conversation: float = Field(description="Average messages per conversation")
    avg_qualification_time_hours: float | None = Field(description="Average time to qualification")
    platform_breakdown: dict[str, int] = Field(description="Conversations by platform")
    daily_stats: list[dict[str, Any]] = Field(description="Daily conversation statistics")


# Type aliases for better code readability
ConversationID = str
CustomerID = str
MessageID = str
