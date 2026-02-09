# Test Quality: Examples

Detailed code examples for each test quality factor.

---

## 1. Substantive Assertions (No Rubber Stamps)

```python
# INCORRECT - rubber stamp test (proves nothing)
def test_process_data():
    result = process_data(sample_data)
    assert result is not None  # This would pass even if result was garbage


# INCORRECT - only asserts on mock return value
def test_fetch_user(mock_db):
    mock_db.get.return_value = {"id": 1, "name": "Alice"}
    result = fetch_user(1)
    assert result == {"id": 1, "name": "Alice"}  # Just testing the mock!


# INCORRECT - only verifies types
def test_calculate_totals():
    result = calculate_totals(orders)
    assert isinstance(result, dict)
    assert isinstance(result.get("total"), (int, float))


# CORRECT - substantive assertions that verify behavior
def test_process_data_returns_cleaned_records():
    """Verify process_data removes invalid records and normalizes fields."""
    # Arrange
    sample_data = [
        {"id": 1, "value": "  VALID  ", "status": "active"},
        {"id": 2, "value": "", "status": "active"},  # should be filtered
        {"id": 3, "value": "also valid", "status": "inactive"},  # should be filtered
    ]

    # Act
    result = process_data(sample_data)

    # Assert - specific, meaningful assertions
    with check:
        assert len(result) == 1, "Should filter invalid and inactive records"
    with check:
        assert result[0]["id"] == 1
    with check:
        assert result[0]["value"] == "valid", "Should be trimmed and lowercased"
```

---

## 2. True Functionality Testing

```python
# INCORRECT - testing implementation details
def test_user_service_internal_cache():
    service = UserService()
    service.get_user(1)
    assert 1 in service._cache  # Testing private implementation!
    assert service._cache_hits == 0  # Internal counter


# INCORRECT - would break on refactoring
def test_order_processor():
    processor = OrderProcessor()
    processor.process(order)
    # These assertions depend on internal method call order
    assert processor._validated is True
    assert processor._calculated is True
    assert processor._persisted is True


# CORRECT - testing observable behavior
def test_user_service_caches_results():
    """Second call should not hit the database."""
    # Arrange
    db = FakeDatabase()
    db.users = {1: User(id=1, name="Alice")}
    service = UserService(db)

    # Act
    first_call = service.get_user(1)
    second_call = service.get_user(1)

    # Assert - observable behavior, not internal state
    with check:
        assert first_call == second_call
    with check:
        assert db.query_count == 1, "Should cache, not query twice"


# CORRECT - tests public contract
def test_order_processor_validates_and_saves():
    """Process should validate order and persist to database."""
    # Arrange
    db = FakeDatabase()
    processor = OrderProcessor(db)
    order = Order(items=[Item(sku="ABC", quantity=2)])

    # Act
    result = processor.process(order)

    # Assert - what matters to callers
    with check:
        assert result.success is True
    with check:
        assert result.order_id is not None
    with check:
        assert db.orders[result.order_id] == order
```

---

## 3. Test Organization

```python
# INCORRECT - unrelated tests in same class
class TestUserStuff:
    def test_user_creation(self):
        user = User(name="Alice")
        assert user.name == "Alice"

    def test_email_validation(self):  # Different concern!
        assert is_valid_email("test@example.com")

    def test_database_connection(self):  # Completely unrelated!
        db = Database()
        assert db.is_connected


# CORRECT - cohesive test class
class TestUserCreation:
    """Tests for User creation and initialization."""

    @pytest.fixture
    def valid_user_data(self) -> dict:
        return {"name": "Alice", "email": "alice@example.com"}

    def test_create_user_with_required_fields(self, valid_user_data):
        """User should be created with name and email."""
        user = User(**valid_user_data)
        with check:
            assert user.name == "Alice"
        with check:
            assert user.email == "alice@example.com"

    def test_create_user_generates_uuid(self, valid_user_data):
        """User should get a unique ID on creation."""
        user = User(**valid_user_data)
        assert user.id is not None
        assert len(str(user.id)) == 36  # UUID format

    def test_create_user_without_name_raises_error(self):
        """User creation should require a name."""
        with pytest.raises(ValueError, match="name is required"):
            User(name="", email="test@example.com")
```

---

## 4. Happy Path AND Edge Case Coverage

```python
# INCORRECT - only happy path
def test_divide():
    assert divide(10, 2) == 5
    assert divide(100, 4) == 25
    # No test for divide by zero!
    # No test for negative numbers!
    # No test for floats!


# CORRECT - comprehensive coverage
class TestDivide:
    """Tests for divide function."""

    @pytest.mark.parametrize(
        ("a", "b", "expected"),
        [
            (10, 2, 5),
            (100, 4, 25),
            (7, 2, 3.5),
            (-10, 2, -5),
            (0, 5, 0),
        ],
    )
    def test_divide_valid_inputs(self, a, b, expected):
        """Divide should handle various numeric inputs."""
        assert divide(a, b) == expected

    def test_divide_by_zero_raises_error(self):
        """Divide by zero should raise ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError):
            divide(10, 0)

    def test_divide_with_none_raises_type_error(self):
        """None inputs should raise TypeError."""
        with pytest.raises(TypeError):
            divide(None, 5)
```

---

## 5. Test Data Variety

```python
# INCORRECT - repetitive, unrealistic data with no variety
def test_user_1():
    user = User(name="test", email="test@test.com")
    assert user.is_valid()

def test_user_2():
    user = User(name="test", email="test@test.com")  # Same data!
    assert user.can_login()

def test_user_3():
    user = User(name="test", email="test@test.com")  # Same data again!
    assert user.is_active


# INCORRECT - magic numbers without context
def test_pricing():
    assert calculate_price(100, 0.2, 5) == 96  # What are these numbers?


# INCORRECT - only simple integers, no edge values
def test_summarize():
    df = pl.DataFrame({"value": [1, 2, 3]})  # No nulls, no floats, no extremes
    result = summarize(df)
    assert result["mean"] == 2.0


# CORRECT - varied, realistic, parametrized
@pytest.mark.parametrize(
    ("name", "email", "expected_valid"),
    [
        ("Alice Johnson", "alice.johnson@example.com", True),
        ("Bob Smith", "bob.smith@company.org", True),
        ("", "empty@example.com", False),  # Empty name
        ("Charlie", "", False),  # Empty email
        ("Dana", "not-an-email", False),  # Invalid email format
    ],
)
def test_user_validation(name, email, expected_valid):
    """User validation should check name and email."""
    user = User(name=name, email=email)
    assert user.is_valid() == expected_valid


# CORRECT - clear test data with context
def test_pricing_with_discount():
    """Price should apply quantity discount and coupon."""
    # Arrange
    base_price = 100.00
    quantity_discount_percent = 0.20  # 20% off for bulk
    coupon_discount_dollars = 5.00

    # Act
    final_price = calculate_price(
        base_price,
        quantity_discount_percent,
        coupon_discount_dollars
    )

    # Assert
    # $100 - 20% = $80, then - $5 coupon = $75
    assert final_price == 75.00


# CORRECT - diverse data types and edge values
def test_summarize_with_nulls_and_extremes():
    """Summarize should handle nulls, infinity, and negative zero."""
    # Arrange - data inline with diverse edge cases
    df = pl.DataFrame({
        "value": [None, -0.0, 1e15, None, float("inf")],
        "category": ["sales", None, "support", None, ""],
    })

    # Act
    result = summarize(df)

    # Assert
    with check:
        assert result["null_count"] == 2
```

---

## 6. Fixture Usage

Fixtures are for **dependency instances** (connections, services, clients), not for test data.

```python
# INCORRECT - fixture modifies global state
@pytest.fixture
def setup_global_config():
    import myapp.config as config
    config.DEBUG = True  # Modifies global!
    config.DATABASE_URL = "sqlite://:memory:"
    yield
    # Oops, forgot to reset!


# INCORRECT - fixture defines test data (should be inline)
@pytest.fixture
def single_user():
    return User(name="Test")

def test_something(single_user):  # Reader must jump to fixture to see data
    assert single_user.name == "Test"


# INCORRECT - fixture defines test data (dict/DataFrame/simple values)
@pytest.fixture
def user_data() -> dict:
    return {"name": "Alice", "email": "alice@example.com"}

def test_create_user(user_data):  # Data hidden — define inline instead
    user = User(**user_data)
    assert user.is_valid()


# INCORRECT - complex fixture chain
@pytest.fixture
def base_config():
    return {"debug": True}

@pytest.fixture
def extended_config(base_config):
    return {**base_config, "db": "test"}

@pytest.fixture
def service(extended_config):
    return Service(extended_config)

@pytest.fixture
def prepared_service(service):
    service.initialize()
    return service

def test_service(prepared_service):  # 4 fixtures deep!
    ...


# CORRECT - fixture for a dependency instance with cleanup
@pytest.fixture
def db_connection():
    """Create test database connection with automatic cleanup."""
    conn = create_test_database()
    yield conn
    conn.close()
    drop_test_database()


# CORRECT - fixture for a reusable dependency instance
@pytest.fixture
def processor() -> DataProcessor:
    """Create a DataProcessor instance for testing."""
    return DataProcessor(max_size=1000, validate=True)


# CORRECT - test data defined inline, fixture only for the dependency
def test_load_data_success(processor: DataProcessor) -> None:
    """Test successful data loading with valid input."""
    # Arrange - data inline so reader sees exactly what's loaded
    sample_data = [
        {"id": 1, "value": 10.5, "name": "Alice"},
        {"id": 2, "value": 20.0, "name": "Bob"},
    ]

    # Act
    processor.load_data(sample_data)

    # Assert
    with check:
        assert processor.record_count == 2


# CORRECT - simple data defined inline
def test_user_full_name():
    """User full_name should combine first and last name."""
    # Simple data - no fixture needed
    user = User(first_name="Alice", last_name="Johnson")
    assert user.full_name == "Alice Johnson"
```

---

## 7. Mock Discipline

```python
# INCORRECT - mocking the unit under test
def test_calculator(mocker):
    calc = Calculator()
    mocker.patch.object(calc, 'add', return_value=5)  # Mocking what we're testing!
    assert calc.add(2, 3) == 5  # This tests nothing


# INCORRECT - excessive mocking
def test_process_order(mocker):
    mock_db = mocker.Mock()
    mock_email = mocker.Mock()
    mock_payment = mocker.Mock()
    mock_inventory = mocker.Mock()
    mock_shipping = mocker.Mock()
    mock_analytics = mocker.Mock()  # 6 mocks = design smell

    processor = OrderProcessor(
        mock_db, mock_email, mock_payment,
        mock_inventory, mock_shipping, mock_analytics
    )
    processor.process(order)
    # Tons of mock assertions...


# INCORRECT - mocking when real object works
def test_string_processing(mocker):
    mock_str = mocker.Mock()
    mock_str.upper.return_value = "HELLO"
    result = process_text(mock_str)  # Why mock a string?!
    assert result == "HELLO"


# CORRECT - mock only external dependencies
def test_send_notification():
    """Notification should be sent via email service."""
    # Arrange
    fake_email_service = FakeEmailService()
    notifier = Notifier(email_service=fake_email_service)

    # Act
    notifier.notify(user_id=1, message="Hello")

    # Assert
    assert len(fake_email_service.sent_emails) == 1
    assert fake_email_service.sent_emails[0].message == "Hello"


# CORRECT - use real objects when possible
def test_json_serialization():
    """Order should serialize to valid JSON."""
    # No mocks needed - use real Order and real json
    order = Order(id=1, customer="alice@example.com", total=99.99)

    json_str = order.to_json()
    parsed = json.loads(json_str)

    with check:
        assert parsed["id"] == 1
    with check:
        assert parsed["customer"] == "alice@example.com"
    with check:
        assert parsed["total"] == 99.99
```

---

## 8. Tests Run Successfully

```python
# INCORRECT - syntax error
def test_something()  # Missing colon!
    assert True


# INCORRECT - import error
from nonexistent_module import Thing  # Will fail immediately

def test_thing():
    assert Thing().value == 1


# INCORRECT - unexplained skip
@pytest.mark.skip  # Why? When can this be unskipped?
def test_important_feature():
    assert feature_works()


# INCORRECT - test that fails
def test_broken():
    result = calculate_total([1, 2, 3])
    assert result == 5  # Actually returns 6!


# CORRECT - clear skip reason with ticket reference
@pytest.mark.skip(reason="Requires external API key - see #123 for CI setup")
def test_external_api_integration():
    ...


# CORRECT - xfail with clear explanation
@pytest.mark.xfail(reason="Bug in upstream library - tracked in #456")
def test_known_issue():
    ...


# CORRECT - tests that actually pass
def test_calculate_total():
    """Calculate total should sum all values."""
    result = calculate_total([1, 2, 3])
    assert result == 6
```
