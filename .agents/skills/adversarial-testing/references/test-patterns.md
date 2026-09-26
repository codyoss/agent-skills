# Adversarial Test Patterns & Templates

Adapt names (`Coordinator`, `Service`, `parse`) to the code under test. Every template has a hard deadline so a deadlock fails the test instead of hanging CI.

## 1. Concurrent Burst & Cancellation Harness (Rust / Tokio)

```rust
use std::{sync::Arc, time::Duration};
use tokio::time::timeout;
use tokio_util::sync::CancellationToken;

#[tokio::test(flavor = "multi_thread", worker_threads = 4)]
async fn adversarial_concurrent_hammer_and_cancel() {
    let coordinator = Arc::new(Coordinator::new());

    let run = async {
        let mut handles = Vec::new();
        for i in 0..100 {
            let coord = Arc::clone(&coordinator);
            handles.push(tokio::spawn(async move {
                match i % 3 {
                    // Cancel before the first poll.
                    0 => {
                        let token = CancellationToken::new();
                        token.cancel();
                        let _ = coord.process_with_token(token).await;
                    }
                    // Cancel mid-flight, after the operation has started.
                    1 => {
                        let token = CancellationToken::new();
                        let task = tokio::spawn({
                            let coord = Arc::clone(&coord);
                            let token = token.clone();
                            async move { coord.process_with_token(token).await }
                        });
                        tokio::time::sleep(Duration::from_micros((i * 37 % 500) as u64)).await;
                        token.cancel();
                        let _ = task.await;
                    }
                    _ => {
                        let _ = coord.process_payload(format!("payload-{i}")).await;
                    }
                }
            }));
        }
        for handle in handles {
            handle.await.expect("task panicked during stress run");
        }
    };

    timeout(Duration::from_secs(30), run)
        .await
        .expect("stress run deadlocked (exceeded 30s)");

    assert!(coordinator.is_healthy().await, "coordinator ended in corrupted state");
}
```

## 2. Race Condition Runner with Leak Check (Go)

Run with `go test -race -count=20 -run Adversarial ./...`.

```go
import (
    "context"
    "fmt"
    "sync"
    "testing"
    "time"

    "go.uber.org/goleak"
)

func TestAdversarialConcurrentExecution(t *testing.T) {
    defer goleak.VerifyNone(t) // fails if any goroutine outlives the test

    srv := NewService()
    defer srv.Close()

    const workers = 50
    const iterations = 100

    var wg sync.WaitGroup
    wg.Add(workers)
    for i := 0; i < workers; i++ {
        go func(workerID int) {
            defer wg.Done()
            for j := 0; j < iterations; j++ {
                key := fmt.Sprintf("key-%d", j%10) // few keys => high contention
                if (workerID+j)%2 == 0 {
                    _ = srv.Mutate(key)
                } else {
                    _ = srv.Read(key)
                }
            }
        }(i)
    }

    done := make(chan struct{})
    go func() { wg.Wait(); close(done) }()
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    select {
    case <-done:
    case <-ctx.Done():
        t.Fatal("deadlock: workers did not finish within 30s")
    }

    if err := srv.ValidateIntegrity(); err != nil {
        t.Fatalf("state corrupted after concurrent access: %v", err)
    }
}
```

## 3. Fuzz Target (Go native fuzzing)

Run with `go test -fuzz=FuzzParse -fuzztime=60s`. Failing inputs are saved under `testdata/fuzz/FuzzParse/` and replay as regular tests.

```go
func FuzzParse(f *testing.F) {
    f.Add([]byte(`{"id":1,"name":"a"}`)) // seed corpus: valid input
    f.Add([]byte(`{"id":`))              // truncated
    f.Add([]byte{0xff, 0xfe, 0x00})      // invalid UTF-8

    f.Fuzz(func(t *testing.T, data []byte) {
        v, err := Parse(data) // must never panic
        if err != nil {
            return
        }
        // Round-trip property: anything we accept, we can re-encode and re-parse identically.
        out, err := Encode(v)
        if err != nil {
            t.Fatalf("accepted input but failed to re-encode: %v", err)
        }
        v2, err := Parse(out)
        if err != nil || !reflect.DeepEqual(v, v2) {
            t.Fatalf("round-trip mismatch: %v vs %v (err=%v)", v, v2, err)
        }
    })
}
```

## 4. Property-Based Test (Python / Hypothesis)

```python
from hypothesis import given, strategies as st

@given(st.binary(max_size=4096))
def test_parse_never_raises_untyped(data):
    try:
        parse(data)
    except ParseError:
        pass  # typed, expected failure is fine; anything else fails the test

@given(st.dictionaries(st.text(), st.integers()))
def test_round_trip(obj):
    assert decode(encode(obj)) == obj
```

## 5. Mock Server Fault Injection (Go `httptest`)

```go
func TestAdversarialUpstreamFailures(t *testing.T) {
    var calls atomic.Int32
    upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        switch calls.Add(1) {
        case 1:
            w.WriteHeader(http.StatusInternalServerError)
        case 2:
            w.Header().Set("Retry-After", "1")
            w.WriteHeader(http.StatusTooManyRequests)
        case 3:
            // Drop the connection mid-response.
            hj, _ := w.(http.Hijacker)
            conn, _, _ := hj.Hijack()
            conn.Close()
        default:
            w.Write([]byte(`{"ok":true}`))
        }
    }))
    defer upstream.Close()

    client := NewClient(upstream.URL, WithMaxRetries(5))
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    if _, err := client.Fetch(ctx); err != nil {
        t.Fatalf("client should recover after transient failures: %v", err)
    }
    if got := calls.Load(); got != 4 {
        t.Fatalf("expected 4 attempts (3 failures + success), got %d", got)
    }
}
```

In Rust, the `wiremock` crate provides the same shape: `Mock::given(method("GET")).respond_with(ResponseTemplate::new(500)).up_to_n_times(1)`. Verify timeouts, exponential backoff, and that errors bubble up as typed errors rather than panics.
