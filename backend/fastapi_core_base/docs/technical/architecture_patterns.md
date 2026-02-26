# Architecture Patterns in `src/shared`

The `src/shared` directory utilizes two primary design patterns to organize code, minimize coupling, and maintain a clean separation of concerns. Choosing the correct pattern depends on whether the component is stateful and business-critical or stateless and universally required.

---

## 1. The Module / Facade Pattern (`__init__.py` Exports)

### What it is
The Module Pattern relies on exporting a functional interface or a global singleton through a module's `__init__.py` file. Instead of forcing consuming code to instantiate a formal "Service" class, the module acts as a "public storefront" (Facade) that hides the underlying complexity.

### When to use it
Use this pattern for **stateless utilities**, **cross-cutting concerns**, and components that are needed *everywhere* in the codebase.

- **Examples:** Logging, Configuration, Exceptions, Middlewares, low-level HTTP/SMTP dispatchers.
- **Why it's better here:** 
  - **Low Boilerplate:** It prevents requiring 100 files to import and instantiate a `LoggingService` class.
  - **Low Coupling:** Changes to the underlying implementation (e.g., swapping out the logging engine) only occur behind the `__init__.py` interface, requiring zero refactoring in consuming code.
  - **Purity:** Functions like `send_email(payload)` or `get_logger(name)` are pure, lightweight, and do not hold state.

### Example: Logging
Instead of every file importing a service:
```python
# BAD: Tight coupling to an explicit service class
from src.shared.services.logging_service import LoggingService
logger = LoggingService.get_logger(__name__)
```
We use the Module Facade:
```python
# GOOD: Abstracted via the module interface
from src.shared.logging import get_logger
logger = get_logger(__name__)
```

---

## 2. The Service Orchestrator Pattern (Service Classes)

### What it is
The Service Orchestrator Pattern involves wrapping interactions inside a dedicated, instantiate-able `Class` object (`SomeService`). These classes act as traffic cops—they intercept requests, apply business logic, handle state, and delegate work to lower-level components.

### When to use it
Use this pattern for **heavy, stateful, or business-critical resources** that require complex routing, lifecycle management, or dependency injection.

- **Examples:** `DatabaseService`, `NotifierService`, `UserService`, `RedisService`.
- **Why it's better here:**
  - **State Management:** Database operations, connection pools, and caching mechanisms are inherently stateful and must be managed across an application lifecycle.
  - **Orchestration:** A `NotifierService` doesn't just "fire a request"—it receives a complex `AlertPayload`, determines which channels are active (Email, Slack), selects the right low-level provider modules, and tracks the results.
  - **Dependency Injection (DI):** In frameworks like FastAPI, services are usually injected into API routes. Mocking a `DatabaseService` class is much cleaner and safer during unit testing than overriding loose global functions.

### Example: Notifier Orchestration
The orchestration class handles the complex routing logic while delegating the actual work to pure module functions.
```python
# src/shared/services/notifier_service.py

from src.shared.notifier.providers.email_provider import send_email
from src.shared.notifier.providers.slack_provider import send_slack

class NotifierService:
    @staticmethod
    async def send(payload: AlertPayload) -> bool:
        # Route logic and orchestration
        if AlertChannel.EMAIL in payload.channels:
            send_email(payload.email)  # Delegates to the pure Module/Facade API
        
        if AlertChannel.SLACK in payload.channels:
            await send_slack(payload.slack) # Delegates to the pure Module/Facade API
            
        return True
```

---

## Summary
- **Stateless & Pervasive = Module Facade** (Expose functions/singletons directly via `__init__.py`)
- **Stateful & Complex Routing = Service Orchestrator** (Build an explicit `Class` to manage dependencies and logic)
