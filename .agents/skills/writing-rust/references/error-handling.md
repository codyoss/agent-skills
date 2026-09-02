# Rust Error Handling Patterns

## 1. Domain Errors with `thiserror` (Libraries & Core Logic)

Use `thiserror` for module/crate-level error enums:

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AudioPipelineError {
    #[error("failed to initialize device '{device}': {reason}")]
    DeviceInitFailed {
        device: String,
        reason: String,
    },

    #[error("audio buffer overflow: capacity {capacity}, attempted {attempted}")]
    BufferOverflow {
        capacity: usize,
        attempted: usize,
    },

    #[error("io error encountered during playback")]
    Io(#[from] std::io::Error),

    #[error("unsupported sample rate: {0}")]
    UnsupportedSampleRate(u32),
}
```

## 2. Application Errors with `anyhow` (CLI & Handlers)

Use `anyhow` for top-level binaries and CLI orchestration:

```rust
use anyhow::{Context, Result};

pub fn load_config(path: &std::path::Path) -> Result<AppConfig> {
    let raw = std::fs::read_to_string(path)
        .with_context(|| f!("failed to read config file at {}", path.display()))?;
    
    let config: AppConfig = toml::from_str(&raw)
        .with_context(|| "failed to deserialize TOML config")?;
        
    Ok(config)
}
```

## 3. Best Practices Checklist

- [ ] Derive `Debug` and implement `std::error::Error` (handled automatically by `thiserror::Error`).
- [ ] Implement `From<T>` conversions via `#[from]` only when the underlying error uniquely maps to that variant.
- [ ] Provide clear, lowercase error messages without trailing punctuation.
- [ ] Avoid exposing internal dependencies in public crate error signatures.
