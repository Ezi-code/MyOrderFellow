# Project AI Guidelines

These guidelines are intended for AI assistants and copilots to ensure code quality, consistency, and adherence to best practices within the `my_order_fellow` project.

## Core Principles

1.  **Pythonic Code**: Follow PEP 8 standards. Code should be concise, readable, and idiomatic.
2.  **Django Best Practices**: Leverage the framework's features rather than reinventing the wheel.
3.  **Documentation**: Code must be self-documenting via type hints and explicit docstrings.

## Coding Standards

### 1. Documentation & Docstrings
-   **Requirement**: All modules, classes, and public methods must include docstrings.
-   **Format**: Use the **Google Python Style Guide** format for docstrings.
-   **Content**:
    -   **Description**: A clear summary of what the code does.
    -   **Args**: List each parameter with its type and description.
    -   **Returns**: Describe the return value and its type.
    -   **Raises**: List any exceptions that are explicitly raised.

### 2. Type Hinting
-   Use Python's standard type hints (Python 3.10+ syntax preferred).
-   Annotate all function arguments and return types.
-   Use `typing.Optional`, `typing.List`, etc., where necessary, or built-in types if on a compatible version.

### 3. Django Specifics
-   **Models**:
    -   Inherit from `base.models.TimeStampedModel` for any model requiring `created_at` and `updated_at` fields.
    -   Keep business logic in Models or Managers ("Fat Models, Thin Views").
    -   Always define a `__str__` method.
-   **Database**:
    -   Use `select_related` (for ForeignKey) and `prefetch_related` (for ManyToMany) to prevent N+1 query issues.
    -   Prefer Django's ORM methods over raw SQL.
-   **Views**:
    -   Use Class-Based Views (CBVs) for standard CRUD to maintain consistency.
    -   Ensure proper error handling and status codes.

## Example Implementation

```python
from django.db import models
from typing import List

class Product(models.Model):
    """
    Represents a product available in the store.

    Attributes:
        name (str): The name of the product.
        price (Decimal): The price of the product.
    """
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def calculate_discount(self, percentage: float) -> float:
        """
        Calculates the discount amount based on a percentage.

        Args:
            percentage (float): The discount percentage (0.0 to 1.0).

        Returns:
            float: The calculated discount amount.
        """
        return float(self.price) * percentage
```
