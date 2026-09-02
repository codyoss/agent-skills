# Adversarial Test Patterns & Templates

## 1. Concurrent Burst & Cancellation Harness (Rust / Tokio)

```rust
#[tokio::test(flavor = "multi_thread", worker_threads = 4)]
async fn test_adversarial_concurrent_hammer_and_cancel() {
    let coordinator = Arc::new(Coordinator::new());
    let mut handles = Vec::new();

    for i in 0..100 {
        let coord = Arc::clone(&coordinator);
        handles.push(tokio::spawn(async move {
            if i % 3 == 0 {
                // Rapid start/cancel race
                let token = CancellationToken::new();
                let fut = coord.process_with_token(token.clone());
                token.cancel();
                let _ = fut.await;
            } else {
                let _ = coord.process_payload(format!("payload-{}", i)).await;
            }
        }));
    }

    for handle in handles {
        let res = handle.await;
        assert!(res.is_ok(), "Task panicked during stress run");
    }

    assert!(coordinator.is_healthy().await, "Coordinator ended in corrupted state");
}
```

## 2. Race Condition Runner (Go)

```go
func TestAdversarialConcurrentExecution(t *testing.T) {
    srv := NewService()
    const workers = 50
    const iterations = 100

    var wg sync.WaitGroup
    wg.Add(workers)

    for i := 0; i < workers; i++ {
        go func(workerID int) {
            defer wg.Done()
            for j := 0; j < iterations; j++ {
                if j%2 == 0 {
                    _ = srv.Mutate(fmt.Sprintf("key-%d", j))
                } else {
                    _ = srv.Read(fmt.Sprintf("key-%d", j))
                }
            }
        }(i)
    }

    wg.Wait()
    if err := srv.ValidateIntegrity(); err != nil {
        t.Fatalf("State corrupted after concurrent access: %v", err)
    }
}
```

## 3. Mock Server Fault Injection (WireMock / HTTP)

- Simulate network disconnects (`wiremock::ResponseTemplate::new(500)` or dropped socket).
- Verify timeouts, exponential backoff retries, and clean error bubble-up.
