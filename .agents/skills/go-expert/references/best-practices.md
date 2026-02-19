# **Go Best Practices & Style Guide**

## **Naming**

* **Short Locals**: Use `i` for loop index, `r` for reader, `w` for writer. Avoid `index`, `readerObject`.  
* **Descriptive Globals**: Exported functions/vars need descriptive names.  
* **Getters**: Use `Owner()`, NOT `GetOwner()`.  
* **Interfaces**: One method interfaces end in `-er` (e.g., `Reader`, `Writer`).

## **Structure**

* **Package Names**: Short, lowercase, singular (e.g., `transport`, not `transports` or `http_transport`).  
* **Constructors**: `New(...)` or `NewType(...)`.

## **Error Handling**

* **Indent Error Flow**: Handle errors first to keep the "happy path" unindented.  

```go
  // Bad  
  if err == nil {  
      // do work  
  } return err

  // Good  
  if err != nil {  
      return err  
  }  
  // do work
```

## **Interfaces**

* **Accept Interfaces, Return Structs**: Functions should accept the smallest interface required but return concrete types.  
* **Definition**: Define interfaces where they are *used* (consumer), not where they are implemented (producer).