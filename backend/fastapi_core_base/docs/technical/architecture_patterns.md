# Architecture Patterns (2026 Refinement)

The `src/shared` directory utilizes thirteen primary design patterns to organize code, minimize coupling, and maintain a clean separation of concerns. Choosing the correct pattern depends on whether the component is stateful, business-critical, or requires a simplified developer experience.

---

## 1. The Module / Facade Pattern ("The Steering Wheel")

**1. What it is:** Exposes functionality as simple, stateless functions via `__init__.py`. This pattern acts as a functional interface that hides underlying complexity from the consumer.

**2. When to use it:** Use this when you need logic that is universally required across the codebase and does not depend on user state or complex initialization. It is ideal for minimizing boilerplate and coupling.

**3. Best for / use case:**
- **Logging:** Shared loggers used in every module.
- **Formatting:** String manipulation, date formatting, or unit conversion.
- **Constants:** Shared system-wide values.
- **Global Config:** Accessing environment variables or core settings.

**4. Example:** Imagine a car's steering wheel: the driver only cares about turning it left or right (the interface). They don't need to know how the steering rack or hydraulics are moving underneath.

**5. Implementation Sample:**
```python
# src/shared/logging/__init__.py
import logging
import sys

def get_logger(name: str):
    """The simple interface the team uses"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(handler)
    return logger

# Usage in any file:
# from src.shared.logging import get_logger
# logger = get_logger(__name__)
```

---

## 2. The Service Orchestrator Pattern ("The Engine")

**1. What it is:** Wraps logic inside a Class to manage components that have a lifecycle, internal state, or complex routing requirements.

**2. When to use it:** Use this for "heavy" resources that require opening and closing connections, or when a task involves multiple steps that need to be "orchestrated" safely (e.g., checking a database before sending a notification).

**3. Best for / use case:**
- **Database Pools:** Managing SQLAlchemy or AsyncPG connections.
- **Redis/Caching:** Handling TTLs and connection resilience.
- **Notification Routers:** Determining if a message goes to Slack, Email, or both.
- **BigQuery:** Complex analytical data streaming.

**4. Example:** The engine of a car: It has a complex lifecycle (start, idle, run, stop) and manages internal state (temperature, fuel levels). You interact with it through formal controls, but it handles the "heavy lifting" internally.

**5. Implementation Sample:**
```python
class StorageService:
    def __init__(self, bucket_name: str, credentials):
        self.bucket_name = bucket_name
        self.client = StorageClient(credentials) # Stateful client holds connections

    async def upload_file(self, file_bytes: bytes, destination: str):
        # Complex multi-step logic
        bucket = self.client.get_bucket(self.bucket_name)
        blob = bucket.blob(destination)
        blob.upload_from_string(file_bytes)
        return True
```

---

## 3. The Hybrid Pattern ("The Tesla Experience")

**1. What it is:** The most advanced pattern. It encapsulates powerful internal logic within a Service Class (the Orchestrator) but exposes a simple, functional Facade (the Steering Wheel) for team members to use 90% of the time.

**2. When to use it:** Use this for core infrastructure (Storage, Auth, DB Ops) where you want total power for the primary architect but total simplicity for the rest of the developers. It provides the best of both worlds.

**3. Best for / use case:**
- **GCS Storage:** Complex streaming uploads hidden behind a simple `upload_asset()` helper.
- **Authentication:** Token validation logic hidden behind a `get_current_user()` function.
- **Emailing:** Template rendering and SMTP logic hidden behind `send_welcome_email()`.

**4. Example:** A Tesla: Under the hood, it's a complex, stateful computer managing batteries and motors. But for the driver, it's a simple, high-tech experience where most actions are automated or accessible through a single tap.

**5. Implementation Sample:**
```python
# 1. The Orchestrator (Internal logic in storage_manager.py)
class _GCSManager:
    def __init__(self):
        self.default_bucket = "my-app-assets"
    
    def stream_upload(self, data, path):
        # Heavy lifting: chunking, retries, header setting
        pass

# 2. The Facade (Public API in src/shared/gcs/__init__.py)
_manager = _GCSManager() # Singleton instance created once

def upload_asset(file_data, name):
    """The easy-to-use function the team sees 90% of the time"""
    return _manager.stream_upload(file_data, f"assets/{name}")

def get_service():
    """For FastAPI Dependency Injection - gives access to the full Class if needed"""
    return _manager
```

---

## 4. The Repository Pattern ("The Vault")

**1. What it is:** A layer that abstracts the specifics of data storage (SQL, NoSQL, APIs) and provides a clean, domain-oriented interface for retrieving and persisting data.

**2. When to use it:** Use this to decouple your business logic from database-specific queries. This makes the code easier to test and allows you to swap database engines without rewriting domain logic.

**3. Best for / use case:**
- **User Persistence:** `UserRepository.find_by_email("user@example.com")`.
- **Order Management:** `OrderRepository.save(new_order)`.
- **Catalogs:** Complex filtering logic for products or transactions.

**4. Example:** A bank vault: You don't need to know which shelf or box "The Smith Account" is in. You simply ask the banker for the account by name, and they handle the logistics of finding the right ledger and key.

**5. Implementation Sample:**
```python
from sqlalchemy.orm import Session
from src.shared.db.models import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User:
        """Domain-friendly interface for fetching data"""
        return self.db.query(User).filter(User.id == user_id).first()

    def save(self, user: User):
        self.db.add(user)
        self.db.commit()
```

---

## 5. The Factory Pattern ("The Assembly Line")

**1. What it is:** A creation pattern that provides a centralized interface for instantiating objects, allowing the system to decide which specific class to create at runtime based on configuration or input.

**2. When to use it:** Use this when you have multiple providers for the same functionality (e.g., Stripe vs. PayPal) and want to switch between them without the calling code knowing the difference.

**3. Best for / use case:**
- **Payment Processors:** `PaymentFactory.get_processor("stripe")`.
- **Document Exporters:** Creating a PDF, CSV, or JSON exporter based on file extension.
- **Social Auth:** Handling Google, GitHub, or LinkedIn login flows dynamically.

**4. Example:** A pizza assembly line: You order a "Pepperoni Pizza" (the request). The factory knows exactly which dough, sauce, and toppings are needed to build that specific pizza.

**5. Implementation Sample:**
```python
class PaymentFactory:
    @staticmethod
    def get_processor(provider: str):
        if provider == "stripe":
            return StripeProcessor()
        elif provider == "paypal":
            return PayPalProcessor()
        raise ValueError(f"Unsupported provider: {provider}")

# Usage:
# processor = PaymentFactory.get_processor(config.PAYMENT_PROVIDER)
# processor.charge(amount)
```

---

## 6. The Observer / Event Pattern ("The Nervous System")

**1. What it is:** A behavioral pattern where a central "Subject" or "Event Bus" triggers multiple independent side-effects whenever a specific event occurs.

**2. When to use it:** Use this when one primary action (e.g., "User Registered") needs to trigger several unrelated tasks without the primary action's code becoming bloated.

**3. Best for / use case:**
- **Post-Registration:** Triggering analytics, emails, and setup scripts.
- **Audit Logs:** Automatically tracking changes to sensitive data.
- **Real-time Notifications:** Pushing updates to WebSockets when data changes.

**4. Example:** The human nervous system: When you touch a hot stove, your nerves send a signal (the Event). Your brain automatically triggers several reactions: pulling your hand away, yelling, and releasing adrenaline.

**5. Implementation Sample:**
```python
class EventBus:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type: str, callback):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type: str, data: dict):
        for callback in self.subscribers.get(event_type, []):
            callback(data)

# Usage:
# bus.publish("user_registered", {"email": "new@user.com"})
```

---

## 7. The Strategy Pattern ("The Tool Belt")

**1. What it is:** A behavioral pattern that defines a set of interchangeable algorithms and encapsulates each one, making them switchable based on the context.

**2. When to use it:** Use this when you have multiple ways to perform a calculation or business rule and want to swap them easily without creating massive `if/else` ladders.

**3. Best for / use case:**
- **Pricing Engines:** Regional rules or seasonal discounts.
- **Discount Logic:** "Buy one get one" vs "Flat 20% off".
- **Validation Rules:** Different requirements for Business vs Personal accounts.

**4. Example:** Imagine a versatile tool belt: you have one handle (the interface), but you can swap out the head for a screwdriver, a wrench, or a hammer depending on the fastener you encounter.

**5. Implementation Sample:**
```python
class PricingStrategy:
    def calculate(self, amount): pass

class HolidayDiscount(PricingStrategy):
    def calculate(self, amount): return amount * 0.8

class StrategyManager:
    def __init__(self, strategy: PricingStrategy):
        self.strategy = strategy

# Usage:
# price = StrategyManager(HolidayDiscount()).strategy.calculate(100)
```

---

## 8. The Adapter Pattern ("The Universal Plug")

**1. What it is:** A structural pattern that allows objects with incompatible interfaces to collaborate. It acts as a wrapper that translates one interface into another.

**2. When to use it:** Use this when you need to integrate a 3rd party library or legacy system whose API doesn't match your system's required interface.

**3. Best for / use case:**
- **Payment Gateways:** Standardizing Stripe, PayPal, and Adyen SDKs.
- **Sms Providers:** Wrapping Twilio vs AWS SNS with a single `send()` method.
- **Logging:** Adapting a custom internal log format to work with DataDog or CloudWatch.

**4. Example:** A travel power adapter: Your US hairdryer has two flat pins (the client interface), but the wall socket in Rome has two round holes. The adapter sits between them so they can work together.

**5. Implementation Sample:**
```python
class TwilioAdapter:
    def __init__(self, twilio_client):
        self.client = twilio_client

    def send_sms(self, to, message):
        """Translates our 'send_sms' to Twilio's 'messages.create'"""
        self.client.messages.create(body=message, to=to, from_="MySystem")
```

---

## 9. The Unit of Work Pattern ("The Transaction Guard")

**1. What it is:** Maintains a set of objects affected by a business transaction. It coordinates the writing out of changes and resolves concurrency problems as a single atomic operation.

**2. When to use it:** Use this when a single user request affects multiple Repositories or Services and you must ensure they all succeed or fail together (Atomicity).

**3. Best for / use case:**
- **Orders & Inventory:** Deducting stock ONLY if the payment record is successfully created.
- **Complex Setups:** Creating a User, their Wallet, and their Profile in one batch.
- **Financial Transactions:** Ensuring money is deducted from A and added to B simultaneously.

**4. Example:** A personal assistant: You give them ten different documents to file across five different departments. They hold all the papers until the very end, and ONLY if all departments are open and ready do they file all ten.

**5. Implementation Sample:**
```python
class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.users = UserRepository(self.session)
        return self

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
```

---

## 10. The CQRS Pattern ("The Divide & Conquer")

**1. What it is:** Command Query Responsibility Segregation (CQRS) separates the data modification paths (Commands) from the data retrieval paths (Queries) to optimize for performance and scalability.

**2. When to use it:** Use this in high-traffic applications where the scale of reads significantly outweighs writes, or where the "Read Models" need to look fundamentally different from the "Write Models".

**3. Best for / use case:**
- **Dashboards:** Reading from a fast, flattened analytical table while writing to a normalized transactional table.
- **Reporting:** Using BigQuery for reads and PostgreSQL for writes.
- **Search:** Writing to a database but reading from an Elasticsearch index.

**4. Example:** A busy restaurant: One person is dedicated to taking orders (the Command), while another person purely delivers the finished plates to tables (the Query). They don't cross paths, making the service much faster.

**5. Implementation Sample:**
```python
# Write Service (Command)
class UserCommandService:
    def update_profile(self, user_id, data):
        db.update(user_id, data)

# Read Service (Query)
class UserQueryService:
    def get_public_profile(self, user_id):
        return fast_cache.get(f"public:{user_id}")
```

---

## 11. The Middleware Pattern ("The Gatekeeper")

**1. What it is:** Intersects the request-response cycle. It is logic that runs before the core logic handles the request and/or after the response is generated.

**2. When to use it:** Use this for cross-cutting concerns that should apply to all (or most) routes, such as security checks, logging, or performance measuring.

**3. Best for / use case:**
- **Authentication:** Checking if a JWT is valid before letting the request reach an API endpoint.
- **CORS:** Adding the correct headers to every response.
- **Request Logging:** Timing how long every API call takes.

**4. Example:** A security guard at a club: Every guest must pass them before entering (the request). They check IDs and dress codes. Once a guest leaves, they might also hand out a flyer (the response).

**5. Implementation Sample:**
```python
from fastapi import Request

async def logging_middleware(request: Request, call_next):
    # Pre-processing: Start timer
    response = await call_next(request)
    # Post-processing: Log duration
    return response
```

---

## 12. The Dependency Injection Pattern ("The Supplier")

**1. What it is:** A design pattern where a component receives its dependencies (services, repos, or config) from an external source rather than creating them internally.

**2. When to use it:** Use this to make your code more modular, decoupled, and easy to unit test by allowing you to "inject" mock dependencies during testing.

**3. Best for / use case:**
- **Service Interactions:** Injecting a `MailService` into a `UserService`.
- **Database Access:** Injecting the `DbSession` into a Repository.
- **App Configuration:** Passing global settings into specific logic modules.

**4. Example:** A professional chef: They don't go to the market mid-recipe to buy onions. Instead, a kitchen porter supplies the chopped onions (injection), so the chef can focus purely on cooking.

**5. Implementation Sample:**
```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.get("/users")
def list_users(db: Session = Depends(get_db)): # Dependency is injected
    return db.query(User).all()
```

---

## 13. The Circuit Breaker Pattern ("The Fuse Box")

**1. What it is:** A stability pattern that detects failures in a remote service and prevents the application from making calls that are likely to fail, giving the remote service time to recover.

**2. When to use it:** Essential in microservices or when calling unstable 3rd party APIs. It prevents "cascading failures" where one slow service bogs down the entire system.

**3. Best for / use case:**
- **External APIs:** Calling a flaky shipping or weather API.
- **Downstream Microservices:** Protecting the core app from a slow auth service.
- **Database Resilience:** Stopping DB calls during a massive spike or migration.

**4. Example:** A home fuse box: When there is a sudden electrical surge, the fuse "trips" and cuts the circuit. This prevents the surge from reaching your expensive electronics.

**5. Implementation Sample:**
```python
import circuitbreaker

@circuitbreaker.circuit
def call_external_api():
    # If this fails N times, the circuit opens 
    # and subsequent calls fail instantly without trying
    return requests.get("https://flaky-api.com")
```

---

## Summary Comparison Table

| Pattern | Logic Type | Consumption Style | Team Experience | Visual Analogy |
| :--- | :--- | :--- | :--- | :--- |
| **Facade** | Stateless Utility | `module.do_thing()` | **Easiest:** No setup. | The Steering Wheel |
| **Orchestrator** | Stateful Service | `srv = Service(); srv.run()` | **Formal:** Best for DI. | The Engine |
| **Hybrid** | Stateful + Easy API | `module.do_thing()` | **Elite:** Simple yet Powerful. | The Tesla Experience |
| **Repository** | Data Abstraction | `repo.get_by_id()` | **Robust:** Clean data layer. | The Vault |
| **Factory** | Dynamic Creation | `Factory.create()` | **Flexible:** Easy to extend. | The Assembly Line |
| **Observer** | Event Driven | `bus.publish()` | **Decoupled:** Reactive side-effects. | The Nervous System |
| **Strategy** | Algorithmic Swap | `strat.calculate()` | **Clean:** No if/else ladders. | The Tool Belt |
| **Adapter** | SDK Wrapper | `adapter.send()` | **Seamless:** Unified 3rd party APIs. | The Universal Plug |
| **Unit of Work** | Atomic Transaction | `uow.commit()` | **Safe:** All-or-nothing updates. | The Transaction Guard |
| **CQRS** | Read/Write Split | `query.get()` | **Performant:** Optimized for scale. | The Divide & Conquer |
| **Middleware** | Request Filter | `app.middleware()` | **Automatic:** Cross-cutting logic. | The Gatekeeper |
| **DI** | Dependency Supply | `Depends(get_db)` | **Testable:** Decoupled components. | The Supplier |
| **Circuit Breaker** | Resilience | `@circuit` | **Bulletproof:** Prevents cascading. | The Fuse Box |
