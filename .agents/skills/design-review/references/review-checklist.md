# Design Review Checklist

Use this checklist during Pass 2 (line-by-line challenge) to ensure every concern area is covered. Not every item applies to every document — skip items that are clearly not relevant.

---

## System Overview / Principles

- [ ] Are the stated principles actually enforced by the architecture? Or are they aspirational?
- [ ] Are there principles that contradict each other (e.g., "streaming" but also "jq filtering" requires buffering)?
- [ ] Is input format precisely defined? (JSON only? YAML? Both? Who parses what?)
- [ ] Is output format precisely defined? (Always JSON? newline-terminated? pretty-printed?)

## Architecture & Components

- [ ] Is every component's **responsibility boundary** clearly stated?
- [ ] Are there components that do too much (God component)?
- [ ] Are there responsibilities mentioned in prose that don't have a home in any component?
- [ ] Is the data flow between components defined? (What does component A pass to component B?)
- [ ] Does any component have a circular dependency on another?
- [ ] Are third-party library calls attributed to a specific component, not floating in the doc?

## Execution Flow

- [ ] Is there an ordering constraint that the flow ignores? (e.g., needing initialized data before a framework runs)
- [ ] Is every step ordered and numbered, not described as parallel prose?
- [ ] Are error paths defined at each step? (What happens if step 3 fails?)
- [ ] Is the "happy path" vs. "error path" output clearly differentiated? (stdout vs. stderr, exit codes)
- [ ] Are there implicit assumptions about the environment? (env vars set, files present, network available)

## Data Structures

- [ ] Are all types fully defined? No abstract references to "a Schema type" — name the actual type.
- [ ] When referencing a third-party type, is the import path stated?
- [ ] Are all fields accounted for? (e.g., if grouping is by tags, does the struct have a `Tags` field?)
- [ ] For collections, is the key and value type stated? (`map[int]*Schema` not just "a map of responses")
- [ ] Are nullable/optional fields distinguished from required ones?
- [ ] Is there a config/settings struct if the system has user-configurable behavior?

## Configuration & Environment

- [ ] Is the config file format (YAML, TOML, JSON) specified?
- [ ] Is a concrete example of the config file provided?
- [ ] Are all env vars named explicitly?
- [ ] Is there a priority order for config sources? (flag > env var > config file > default)
- [ ] Is the config file path documented and discoverable without reading source?

## API / Interface Contracts

- [ ] Are function/method signatures defined for non-trivial components?
- [ ] Is the input validation contract defined? (What is rejected? What error is returned?)
- [ ] Is the error return format defined? (string? typed error? JSON struct?)
- [ ] For HTTP-adjacent tools: are Content-Type, Accept, and auth headers specified?
- [ ] Are edge cases documented? (empty input, missing optional fields, oversized payloads)

## Package / Module Structure

- [ ] Is each package's exported surface described? (Not just a label — what does it expose?)
- [ ] Are there packages that overlap in responsibility?
- [ ] Is there a package missing for a clearly stated concern (e.g., output formatting)?
- [ ] Does the structure enforce the dependency direction? (No cycles, internals not imported by cmd)

## Implementation Details

- [ ] Are implementation sections specific enough to produce code from? ("iterate and replace" is not; "use `strings.ReplaceAll` with `url.PathEscape`" is)
- [ ] Are any "simple" steps that are actually non-trivial called out? (e.g., stdin detection, multipart streaming)
- [ ] Is priority order defined for any "pick one of these inputs" scenarios?
- [ ] Are concurrency concerns addressed where applicable? (goroutines, pipe readers/writers)

## Scope & Deferral

- [ ] Are deferred features explicitly marked as "V2" or "out of scope for V1"?
- [ ] Is there scope creep — features mentioned in passing that would be significant to implement?
- [ ] Are there features that, if removed, would simplify implementation considerably with minimal user impact?
