/**
 * CodeRev AI — API client
 * Calls the FastAPI backend when available; falls back to stub responses
 * when the server is unreachable (e.g. during frontend-only development).
 */

const BASE = 'http://localhost:8000'

// ─── Stub responses (mirror real backend shape) ───────────────────────────────

const CONTRIBUTOR_STUB = (beams) => ({
  suggestions: [
    {
      rank: 1,
      score: 0.94,
      code: `public boolean isPrime(int n) {\n    if (n < 2) return false;\n    for (int i = 2; i <= Math.sqrt(n); i++) {\n        if (n % i == 0) return false;\n    }\n    return true;\n}`,
      explanation: 'Optimised loop bound: only iterate up to √n instead of n, reducing time complexity from O(n) to O(√n).',
      tags: ['Performance', 'Refactoring'],
    },
    {
      rank: 2,
      score: 0.81,
      code: `public boolean isPrime(int n) {\n    if (n < 2) return false;\n    if (n == 2) return true;\n    if (n % 2 == 0) return false;\n    for (int i = 3; i * i <= n; i += 2) {\n        if (n % i == 0) return false;\n    }\n    return true;\n}`,
      explanation: 'Further optimisation: skip even numbers after 2, halving the number of iterations.',
      tags: ['Performance', 'Best Practice'],
    },
    {
      rank: 3,
      score: 0.71,
      code: `public boolean isPrime(int n) {\n    return n >= 2 && IntStream.rangeClosed(2, (int) Math.sqrt(n))\n        .noneMatch(i -> n % i == 0);\n}`,
      explanation: 'Functional-style rewrite using Java streams for conciseness.',
      tags: ['Refactoring', 'Modern Java'],
    },
    {
      rank: 4,
      score: 0.58,
      code: `public boolean isPrime(int n) {\n    if (n < 2) return false;\n    BigInteger bi = BigInteger.valueOf(n);\n    return bi.isProbablePrime(10);\n}`,
      explanation: 'Delegates to BigInteger.isProbablePrime for a library-based approach.',
      tags: ['Library', 'Concise'],
    },
    {
      rank: 5,
      score: 0.45,
      code: `public boolean isPrime(int n) {\n    if (n < 2) return false;\n    if (n == 2) return true;\n    for (int i = 3; i <= Math.sqrt(n); i += 2) {\n        if (n % i == 0) return false;\n    }\n    return true;\n}`,
      explanation: 'Combines even-number shortcut with √n bound and odd-only iteration.',
      tags: ['Performance', 'Minimal Change'],
    },
    {
      rank: 6,
      score: 0.38,
      code: `public boolean isPrime(int n) {\n    if (n < 2) return false;\n    if (n < 4) return true;\n    if (n % 2 == 0 || n % 3 == 0) return false;\n    for (int i = 5; i * i <= n; i += 6) {\n        if (n % i == 0 || n % (i + 2) == 0) return false;\n    }\n    return true;\n}`,
      explanation: '6k±1 optimisation: checks only numbers of the form 6k±1, reducing iterations by ~⅔.',
      tags: ['Performance', 'Advanced'],
    },
    {
      rank: 7,
      score: 0.31,
      code: `public boolean isPrime(int n) {\n    return n > 1 && !IntStream.rangeClosed(2, (int) Math.sqrt(n))\n        .anyMatch(i -> n % i == 0);\n}`,
      explanation: 'Stream variant using anyMatch (negated) instead of noneMatch for readability.',
      tags: ['Stream API', 'Modern Java'],
    },
    {
      rank: 8,
      score: 0.25,
      code: `public boolean isPrime(int n) {\n    if (n < 2) return false;\n    for (int i = 2; i * i <= n; i++) {\n        if (n % i == 0) return false;\n    }\n    return true;\n}`,
      explanation: 'Loop condition uses i*i instead of Math.sqrt to avoid floating-point computation.',
      tags: ['Performance', 'Refactoring'],
    },
    {
      rank: 9,
      score: 0.18,
      code: `public boolean isPrime(int n) {\n    if (n < 2) return false;\n    return LongStream.rangeClosed(2, (long) Math.sqrt(n))\n        .noneMatch(i -> n % i == 0);\n}`,
      explanation: 'Uses LongStream to avoid integer overflow on large values of n.',
      tags: ['Safety', 'Stream API'],
    },
    {
      rank: 10,
      score: 0.11,
      code: `public boolean isPrime(int n) {\n    if (n < 2) return false;\n    if (n == 2 || n == 3) return true;\n    if (n % 2 == 0 || n % 3 == 0) return false;\n    int limit = (int) Math.sqrt(n);\n    for (int i = 5; i <= limit; i += 6) {\n        if (n % i == 0 || n % (i + 2) == 0) return false;\n    }\n    return true;\n}`,
      explanation: 'Pre-computes √n limit once outside the loop combined with 6k±1 optimisation.',
      tags: ['Performance', 'Advanced', 'Refactoring'],
    },
  ].slice(0, beams),
  processing_time_ms: 0,
})

const REVIEWER_STUB = (comment, beams) => ({
  implementations: [
    {
      rank: 1,
      score: 0.92,
      code: `public void processData(List<Object> data) {\n    if (data == null) return;\n    for (Object item : data) {\n        logger.info(String.valueOf(item));\n    }\n}`,
      explanation: `Implemented reviewer suggestion: "${comment}". Applied null guard, used enhanced for-loop, and replaced System.out.println with logger.`,
      tags: ['Null Safety', 'Enhanced Loop', 'Logging'],
    },
    {
      rank: 2,
      score: 0.78,
      code: `public void processData(List<Object> data) {\n    Objects.requireNonNull(data, "data must not be null");\n    data.forEach(item -> logger.info(String.valueOf(item)));\n}`,
      explanation: `Alternative implementation of: "${comment}". Uses Objects.requireNonNull and forEach lambda.`,
      tags: ['Functional', 'Null Safety'],
    },
    {
      rank: 3,
      score: 0.65,
      code: `public void processData(List<Object> data) {\n    if (data == null || data.isEmpty()) return;\n    for (Object item : data) {\n        if (item != null) logger.debug("Processing: {}", item);\n    }\n}`,
      explanation: 'Defensive implementation with both null and empty checks, plus per-item null guard.',
      tags: ['Defensive', 'Enhanced Loop'],
    },
    {
      rank: 4,
      score: 0.51,
      code: `public void processData(List<Object> data) {\n    Optional.ofNullable(data).ifPresent(\n        list -> list.stream().filter(Objects::nonNull)\n                    .forEach(item -> logger.info("{}", item)));\n}`,
      explanation: 'Stream-based functional implementation using Optional and method references.',
      tags: ['Stream API', 'Functional'],
    },
    {
      rank: 5,
      score: 0.39,
      code: `public <T> void processData(List<T> data) {\n    if (data == null) return;\n    for (T item : data) {\n        logger.info(String.valueOf(item));\n    }\n}`,
      explanation: 'Generic typed version with null guard and enhanced for-loop.',
      tags: ['Generics', 'Enhanced Loop'],
    },
    {
      rank: 6,
      score: 0.31,
      code: `public void processData(List<Object> data) {\n    if (data == null) return;\n    data.stream()\n        .filter(Objects::nonNull)\n        .map(String::valueOf)\n        .forEach(logger::info);\n}`,
      explanation: 'Pure stream pipeline with method references for maximum conciseness.',
      tags: ['Stream API', 'Null Safety', 'Logging'],
    },
    {
      rank: 7,
      score: 0.24,
      code: `public void processData(List<Object> data) {\n    if (data == null) throw new IllegalArgumentException("data must not be null");\n    for (Object item : data) {\n        logger.info("{}", item);\n    }\n}`,
      explanation: 'Throws IllegalArgumentException instead of silently returning on null input.',
      tags: ['Fail-Fast', 'Enhanced Loop', 'Logging'],
    },
    {
      rank: 8,
      score: 0.18,
      code: `public void processData(Collection<Object> data) {\n    if (data == null || data.isEmpty()) return;\n    data.forEach(item -> logger.info("{}", Objects.toString(item, "null")));\n}`,
      explanation: 'Accepts any Collection, uses Objects.toString for null-safe string conversion.',
      tags: ['Generics', 'Null Safety', 'Functional'],
    },
    {
      rank: 9,
      score: 0.12,
      code: `public void processData(List<Object> data) {\n    Objects.requireNonNull(data, "data must not be null");\n    data.stream()\n        .filter(item -> item != null)\n        .forEach(item -> logger.debug("item={}", item));\n}`,
      explanation: 'Combines requireNonNull with stream filter for explicit per-item null filtering.',
      tags: ['Defensive', 'Stream API', 'Logging'],
    },
    {
      rank: 10,
      score: 0.07,
      code: `public void processData(List<Object> data) {\n    if (data == null) return;\n    Iterator<Object> it = data.iterator();\n    while (it.hasNext()) {\n        Object item = it.next();\n        if (item != null) logger.info(String.valueOf(item));\n    }\n}`,
      explanation: 'Iterator pattern with explicit null guard — useful when removal during iteration is needed.',
      tags: ['Iterator', 'Defensive', 'Logging'],
    },
  ].slice(0, beams),
  processing_time_ms: 0,
})

// ─── API functions ─────────────────────────────────────────────────────────────

export async function reviewCode(code, beams) {
  try {
    const res = await fetch(`${BASE}/api/contributor/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, beams }),
      signal: AbortSignal.timeout(10000),
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data.detail || `Server error ${res.status}`)
    }
    return await res.json()
  } catch (err) {
    if (err.name === 'TypeError' || err.name === 'TimeoutError' || err.message?.includes('fetch')) {
      // Backend unreachable — use stub
      await new Promise(r => setTimeout(r, 1200))
      return CONTRIBUTOR_STUB(beams)
    }
    throw err
  }
}

export async function implementComment(code, comment, beams) {
  try {
    const res = await fetch(`${BASE}/api/reviewer/implement`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, comment, beams }),
      signal: AbortSignal.timeout(10000),
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data.detail || `Server error ${res.status}`)
    }
    return await res.json()
  } catch (err) {
    if (err.name === 'TypeError' || err.name === 'TimeoutError' || err.message?.includes('fetch')) {
      // Backend unreachable — use stub
      await new Promise(r => setTimeout(r, 1500))
      return REVIEWER_STUB(comment, beams)
    }
    throw err
  }
}
