"""
Product data models for PostgreSQL using SQLModel.

This module defines the Product model that represents products in the PostgreSQL database.
Products are the core entities that ManipulatorAI matches with customer interests and
recommends during conversations.

Business Context:
- Products have tags for correlation matching (tagMatcher subsystem)
- Products can be directly referenced by ID (Manipulator branch)
- Products support cross-selling through genre categorization
- Products maintain creation/update timestamps for analytics
"""

from datetime import datetime

from pydantic import field_validator
from sqlmodel import JSON, Column, Field, SQLModel


class ProductBase(SQLModel):
    """
    Base Product model with shared fields for API and database models.

    This contains all the business logic fields that are common between
    the database representation and API request/response models.
    """

    name: str = Field(
        min_length=1, max_length=255, description="Product name (required, 1-255 characters)"
    )

    description: str | None = Field(
        default=None, max_length=2000, description="Detailed product description for AI context"
    )

    price: float | None = Field(
        default=None, ge=0.0, description="Product price (must be >= 0 if specified)"
    )

    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        description="Currency code (3-character ISO code)",
    )

    genre: str | None = Field(
        default=None, max_length=100, description="Product genre/category for cross-selling"
    )

    tags: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Tags for correlation matching with customer messages",
    )

    is_active: bool = Field(
        default=True, description="Whether product is available for recommendation"
    )

    external_id: str | None = Field(
        default=None, max_length=255, description="External system product ID for integration"
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code format."""
        if v:
            v = v.upper()
            # Add more sophisticated currency validation if needed
            if len(v) != 3:
                raise ValueError("Currency must be a 3-character ISO code")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate and normalize tags."""
        if v:
            # Remove empty tags and normalize
            v = [tag.strip().lower() for tag in v if tag.strip()]
            # Remove duplicates while preserving order
            seen = set()
            result = []
            for tag in v:
                if tag not in seen:
                    seen.add(tag)
                    result.append(tag)
            v = result
        return v


class Product(ProductBase):
    """
    Product database model for PostgreSQL.

    This is the actual database table representation with primary key,
    timestamps, and database-specific configurations.
    """

    # Define as SQLModel table
    model_config = {"table": True}

    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True, description="Auto-generated product ID")

    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Product creation timestamp"
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    # Database indexes for performance
    __table_args__ = (
        # Index on tags for efficient searching
        # Note: Actual GIN index creation will be handled in migrations
    )


class ProductCreate(ProductBase):
    """
    Model for creating new products via API.

    This model is used for POST requests to create products.
    It excludes auto-generated fields like ID and timestamps.
    """

    pass


class ProductUpdate(SQLModel):
    """
    Model for updating existing products via API.

    All fields are optional to support partial updates.
    """

    name: str | None = Field(
        default=None, min_length=1, max_length=255, description="Product name (1-255 characters)"
    )

    description: str | None = Field(
        default=None, max_length=2000, description="Product description"
    )

    price: float | None = Field(default=None, ge=0.0, description="Product price (must be >= 0)")

    currency: str | None = Field(
        default=None, min_length=3, max_length=3, description="Currency code (3-character ISO)"
    )

    genre: str | None = Field(default=None, max_length=100, description="Product genre/category")

    tags: list[str] | None = Field(default=None, description="Product tags for matching")

    is_active: bool | None = Field(default=None, description="Product availability status")

    external_id: str | None = Field(
        default=None, max_length=255, description="External system product ID"
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        """Validate currency code format."""
        if v:
            v = v.upper()
            if len(v) != 3:
                raise ValueError("Currency must be a 3-character ISO code")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        """Validate and normalize tags."""
        if v is not None:
            # Remove empty tags and normalize
            v = [tag.strip().lower() for tag in v if tag.strip()]
            # Remove duplicates while preserving order
            seen = set()
            result = []
            for tag in v:
                if tag not in seen:
                    seen.add(tag)
                    result.append(tag)
            v = result
        return v


class ProductPublic(ProductBase):
    """
    Public product model for API responses.

    This includes all product information that should be visible
    to external consumers of the API.
    """

    id: int = Field(description="Product ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class ProductsPublic(SQLModel):
    """
    Model for paginated product list responses.

    Used when returning multiple products with pagination metadata.
    """

    products: list[ProductPublic] = Field(description="List of products")
    total: int = Field(description="Total number of products")
    page: int = Field(description="Current page number")
    size: int = Field(description="Number of items per page")
    pages: int = Field(description="Total number of pages")


# Type aliases for better code readability
ProductID = int
ProductTag = str
ProductGenre = str
