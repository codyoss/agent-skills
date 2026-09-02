# Async & Concurrency Patterns in Rust

## 1. Actor Pattern with Tokio Channels

Instead of sharing complex state with `Arc<Mutex<State>>`, prefer message passing:

```rust
use tokio::sync::{mpsc, oneshot};

pub enum Command {
    StartStream { response_tx: oneshot::Sender<bool> },
    StopStream,
    GetStats { response_tx: oneshot::Sender<StreamStats> },
}

pub struct StreamCoordinator {
    cmd_tx: mpsc::Sender<Command>,
}

impl StreamCoordinator {
    pub fn spawn() -> Self {
        let (cmd_tx, mut cmd_rx) = mpsc::channel::<Command>(32);

        tokio::spawn(async move {
            let mut is_running = false;
            while let Some(cmd) = cmd_rx.recv().await {
                match cmd {
                    Command::StartStream { response_tx } => {
                        is_running = true;
                        let _ = response_tx.send(true);
                    }
                    Command::StopStream => {
                        is_running = false;
                    }
                    Command::GetStats { response_tx } => {
                        let _ = response_tx.send(StreamStats { is_running });
                    }
                }
            }
        });

        Self { cmd_tx }
    }
}
```

## 2. Cancellation Tokens

Use `tokio_util::sync::CancellationToken` for graceful shutdown:

```rust
use tokio_util::sync::CancellationToken;

pub async fn run_worker(token: CancellationToken) {
    loop {
        tokio::select! {
            _ = token.cancelled() => {
                // Graceful cleanup
                break;
            }
            _ = tokio::time::sleep(tokio::time::Duration::from_millis(100)) => {
                // Perform periodic work
            }
        }
    }
}
```

## 3. Mutex Guards Across Await Points

- **Rule**: Never hold a `std::sync::MutexGuard` across an `.await` boundary. It makes the future `!Send` and risks deadlocks.
- If lock contention is low and short, use standard mutex but drop before awaiting.
- If a lock must span `.await`, use `tokio::sync::Mutex`.
