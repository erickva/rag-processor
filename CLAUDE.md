### 🔄 Project Awareness & Context

- Document everything we discuss in this chat on `CHATDOC.md`. So that I can go back and check at any point in time what we have done. Start each line with the date and time. Based on this computer time.
- Always read `PLANNING.md` at the start of a new conversation to understand the project's architecture, goals, style, and constraints.
- Check `TASK.md` before starting a new task. If the task isn't listed, add it with a brief description and today's date.
- Use consistent naming conventions, file structure, and architecture patterns as described in `PLANNING.md`.

### 🧱 Code Structure & Modularity

- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
- **Use clear, consistent imports** (prefer relative imports within packages).

### 🧪 Testing & Reliability

- **Always create Pytest unit tests for new features** (functions, classes, routes, etc).
- **After updating any logic**, check whether existing unit tests need to be updated. If so, do it.
- **Tests should live in a `/tests` folder** mirroring the main app structure.
  - Include at least:
    - 1 test for expected use
    - 1 edge case
    - 1 failure case
- Always test the individual functions for agent tools.

### ✅ Task Completion

- **Mark completed tasks in `TASK.md`** immediately after finishing them.
- Add new sub-tasks or TODOs discovered during development to `TASK.md` under a "Discovered During Work" section.
- **Before you move to the next item in the todo list, make sure you've written tests according to our guidelines in memory.** After tests and documentation of the work is complete you can then move to the next item on the list.

### 📎 Style & Conventions

- **Use Python** as the primary language.
- **Follow PEP8**, use type hints, and format with `black`.
- **Use `pydantic` for data validation**.
- Write **docstrings for every function** using the Google style:
  ```python
  def example():
      """
      Brief summary.

      Args:
          param1 (type): Description.

      Returns:
          type: Description.
      """
  ```

### 📚 Documentation & Explainability

- **Update `README.md`** when new features are added, dependencies change, or setup steps are modified.
- **Comment code exhaustivily** and assume the person interacting with you has either no coding experience or has experience in other languages framework what what is being used. Ensure everything is understandable to a junior-level developer.- When writing complex logic, **add an inline `# Reason:` comment** explaining the why, not just the what.

### 🧠 AI Behavior Rules

- **Never assume missing context. Ask questions if uncertain.**
- **Always confirm file paths & module names** exist before using
- **Never delete or overwrite existing code** unless explicitly instructed to or if part of a task from `TASK.md`.

### 💻 Coding Best Practices

- No magic numbers, we have a constant file for it @config/constants.py Please use it.
- **Use of constants.py**: All magic numbers, timeouts, retry counts, HTTP status codes, and configurable values must be defined in config/constants.py. Never hardcode numeric values directly in code. Import constants using from config.constants import CONSTANT_NAME. Group related constants with comments and use descriptive names with prefixes (e.g., WHATSAPP_CLIENT_TIMEOUT, HTTP_OK, CHATWOOT_CIRCUIT_FAILURE_THRESHOLD). When adding new features, first check if relevant constants already exist, then add new ones following the established naming pattern. Constants should be UPPER_CASE with underscores.

### 🔌 Circuit Breaker Implementation

- Circuit Breaker: When implementing circuit breaker pattern, always use the existing utils/circuit_breaker.py module which provides CircuitBreaker and CircuitBreakerManager classes with three states (CLOSED, OPEN, HALF_OPEN). For any external API call, use HTTPClientManager.request_with_circuit_breaker() method instead of direct HTTP calls. Configure service-specific thresholds in config/constants.py using pattern SERVICE_CIRCUIT_FAILURE_THRESHOLD and SERVICE_CIRCUIT_RECOVERY_TIMEOUT. Always reset circuit breaker state in test fixtures using circuit_breaker_manager.reset_circuit_breaker(service_name). Circuit breaker should be integrated at the HTTP client level, not in individual service methods.
- Google APIs: Use utils/google_client.py GoogleAPIClientManager for all Google API calls with built-in circuit breaker support. Never make direct Google API execute() calls.
- RAG/Embeddings: Use utils/rag_client.py RAGClientManager for all embedding generation and vector searches with circuit breaker protection.

### 🚨 Logging & Error Handling

- Proper Logging: Always use the injected ErrorHandler instance for logging instead of direct logger calls. Use self.error_handler.log_error() with appropriate ErrorLevel (ERROR, WARNING, INFO, DEBUG) and always include context dictionary with operation name, relevant parameters, and error_type. Never use raw logger.error() or print() statements. For background tasks, use the @safe_background_task decorator which handles logging automatically. All error logs must include structured context for monitoring and debugging. Use ErrorLevel.WARNING for recoverable issues, ErrorLevel.ERROR for failures requiring attention.

### 🛡️ Error Handling Standardization

- Error Handling Standardization: All services must use the injected ErrorHandler instance from utils/error_handler.py. For HTTP endpoints, use @handle_api_errors decorator to automatically convert exceptions to proper HTTP responses. For service methods, use try/except blocks with self.error_handler.log_error() and return None or False on failure (never raise unless it's an HTTP endpoint). Always include operation context in error logs. Use custom exception types (WhatsAppError, TransportError) for service-specific errors. Background tasks must use @safe_background_task decorator. Never expose raw error messages to users - use sanitized error responses.
