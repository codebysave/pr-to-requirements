# Pull Request in input al sistema

Campione: `experiments/samples/sample-scrapy_scrapy.json` — 9 Pull Request di
`scrapy/scrapy`, in ordine cronologico. Titolo e corpo sono l'unica evidenza che
il sistema riceve.

---

# PR #6869

**Titolo:** Fix: Dangerous Code Execution Function Could Allow External Attacks in scrapy/shell.py

**Body:**

```text
**Context and Purpose:**

This PR automatically remediates a security vulnerability:
- **Description:** Detected the use of eval(). eval() can be dangerous if used to evaluate dynamic content. If this content can be input from outside the program, this may be a code injection vulnerability. Ensure evaluated content is not definable by external sources.
- **Rule ID:** python.lang.security.audit.eval-detected.eval-detected
- **Severity:** HIGH
- **File:** scrapy/shell.py
- **Lines Affected:** 76 - 76

This change is necessary to protect the application from potential security risks associated with this vulnerability.

**Solution Implemented:**

The automated remediation process has applied the necessary changes to the affected code in `scrapy/shell.py` to resolve the identified issue.

Please review the changes to ensure they are correct and integrate as expected.
```

---

# PR #6870

**Titolo:** Fix: Unsafe Code Loading from User Input Could Execute Malicious Programs in scrapy/commands/genspider.py

**Body:**

```text
**Context and Purpose:**

This PR automatically remediates a security vulnerability:
- **Description:** Untrusted user input in `importlib.import_module()` function allows an attacker to load arbitrary code. Avoid dynamic values in `importlib.import_module()` or use a whitelist to prevent running untrusted code.
- **Rule ID:** python.lang.security.audit.non-literal-import.non-literal-import
- **Severity:** MEDIUM
- **File:** scrapy/commands/genspider.py
- **Lines Affected:** 156 - 156

This change is necessary to protect the application from potential security risks associated with this vulnerability.

**Solution Implemented:**

The automated remediation process has applied the necessary changes to the affected code in `scrapy/commands/genspider.py` to resolve the identified issue.

Please review the changes to ensure they are correct and integrate as expected.
```

---

# PR #6875

**Titolo:** Fix typo in cmdline.py comment: 'a argument' -> 'an argument'

**Body:**

```text
Description:
This pull request fixes a minor typo in a comment in scrapy/cmdline.py:
Changes "a argument" to "an argument" for correct English usage.
Also improves the comment's clarity by changing "that is" to "that it is" for better English grammar.
No code logic or functionality is affected by this change.

Checklist:
[x] My change is as small as possible and focused on a single issue (typo fix).
[x] No tests are needed as this is a comment-only change.
[x] I have followed the contribution guidelines.
```

---

# PR #6879

**Titolo:** Fix: Unsafe Code Loading from User Input Could Execute Malicious Programs in scrapy/commands/genspider.py

**Body:**

```text
**Context and Purpose:**

This PR automatically remediates a security vulnerability:
- **Description:** Untrusted user input in `importlib.import_module()` function allows an attacker to load arbitrary code. Avoid dynamic values in `importlib.import_module()` or use a whitelist to prevent running untrusted code.
- **Rule ID:** python.lang.security.audit.non-literal-import.non-literal-import
- **Severity:** MEDIUM
- **File:** scrapy/commands/genspider.py
- **Lines Affected:** 156 - 156

This change is necessary to protect the application from potential security risks associated with this vulnerability.

**Solution Implemented:**

The automated remediation process has applied the necessary changes to the affected code in `scrapy/commands/genspider.py` to resolve the identified issue.

Please review the changes to ensure they are correct and integrate as expected.
```

---

# PR #6880

**Titolo:** Fix: Unsafe Data Processing Method Allows Malicious Code Execution in scrapy/exporters.py

**Body:**

```text
**Context and Purpose:**

This PR automatically remediates a security vulnerability:
- **Description:** Avoid using `pickle`, which is known to lead to code execution vulnerabilities. When unpickling, the serialized data could be manipulated to run arbitrary code. Instead, consider serializing the relevant data as JSON or a similar text-based serialization format.
- **Rule ID:** python.lang.security.deserialization.pickle.avoid-pickle
- **Severity:** MEDIUM
- **File:** scrapy/exporters.py
- **Lines Affected:** 303 - 303

This change is necessary to protect the application from potential security risks associated with this vulnerability.

**Solution Implemented:**

The automated remediation process has applied the necessary changes to the affected code in `scrapy/exporters.py` to resolve the identified issue.

Please review the changes to ensure they are correct and integrate as expected.
```

---

# PR #6881

**Titolo:** Fix: Unsafe XML Processing Library Could Allow Malicious Attacks in scrapy/http/request/rpc.py

**Body:**

```text
**Context and Purpose:**

This PR automatically remediates a security vulnerability:
- **Description:** Detected use of xmlrpc. xmlrpc is not inherently safe from vulnerabilities. Use defusedxml.xmlrpc instead.
- **Rule ID:** python.lang.security.use-defused-xmlrpc.use-defused-xmlrpc
- **Severity:** MEDIUM
- **File:** scrapy/http/request/rpc.py
- **Lines Affected:** 10 - 10

This change is necessary to protect the application from potential security risks associated with this vulnerability.

**Solution Implemented:**

The automated remediation process has applied the necessary changes to the affected code in `scrapy/http/request/rpc.py` to resolve the identified issue.

Please review the changes to ensure they are correct and integrate as expected.
```

---

# PR #6899

**Titolo:** Fix typing of dynamic `request` attribute on `Failure` with a cast subclass

**Body:**

```text
This PR addresses a longstanding `TODO` in the `call_spider_async` method regarding the typing of the dynamically added `request` attribute on `twisted.python.failure.Failure` objects.

Since `Failure` does not originally define the `request` attribute, adding it dynamically causes static type checkers (e.g., mypy) to raise errors.

To resolve this without changing runtime behavior or introducing new `Failure` instances, this PR introduces a lightweight subclass `FailureWithRequest` used solely for static typing purposes via `cast()`. This approach:

- Provides type safety and clarity for static analysis tools  
- Avoids creating new `Failure` instances, preserving error context and traceback  
- Keeps runtime behavior unchanged  
- Offers a balanced solution (middle ground) between ignoring type checks and a full refactor of `Failure` usage

```

---

# PR #6936

**Titolo:** feat(settings): Change default SCHEDULER_PRIORITY_QUEUE (closes #6924)

**Body:**

```text
## Description
Changes default `SCHEDULER_PRIORITY_QUEUE` to `DownloaderAwarePriorityQueue` (closes #6924).

Depends on #6921 (merged) where the new queue was implemented.

## Changes
- Updated `SCHEDULER_PRIORITY_QUEUE` default in `default_settings.py`
- Updated documentation in `docs/topics/settings.rst`

## Verification
- Ran tests with `pytest`
- Confirmed backward compatibility

## Testing
- Ran priority queue tests (`test_pqueues.py`) - 11 passed, 2 skipped
- Verified with `scrapy bench` (manual testing)
```

---

# PR #6947

**Titolo:** Ban more imports that import twisted.internet.reactor.

**Body:**

```text
This partially rolls back the import changes in #6941 but not all of these were correct before that PR.
```

---
