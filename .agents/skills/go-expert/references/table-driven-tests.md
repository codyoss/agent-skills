# **Table-Driven Tests Pattern**

In Go, we use table-driven tests to cover various scenarios (happy path, edge cases, errors) without repeating test logic.

## **The Template**

When generating tests, strictly adhere to this structure:

```go
func TestFunctionName(t *testing.T) {  
    // 1. Define the test case struct  
    type testCase struct {  
        name      string  
        input     string // input parameters  
        want      string // expected result  
        wantErr   bool   // do we expect an error?  
        // mockFunc func() // optional: for mocking dependencies  
    }

    // 2. Define the table (slice of test cases)  
    tests := []testCase{  
        {  
            name:    "Happy Path",  
            input:   "valid input",  
            want:    "expected output",  
            wantErr: false,  
        },  
        {  
            name:    "Edge Case: Empty Input",  
            input:   "",  
            want:    "",  
            wantErr: true,  
        },  
    }

    // 3. Iterate over the table  
    for _, tc := range tests {  
        t.Run(tc.name, func(t *testing.T) {  
            // Setup / Mocking (if any)

            // Execution  
            got, err := FunctionName(tc.input)

            // Verification: Error  
            if (err != nil) != tc.wantErr {  
                t.Errorf("FunctionName() error = %v, wantErr %v", err, tc.wantErr)  
                return  
            }

            // Verification: Value  
            // Use cmp.Diff for complex structs, or simple != for basics  
            if got != tc.want {  
                t.Errorf("FunctionName() = %v, want %v", got, tc.want)  
            }  
        })  
    }  
}
```
## **Rules for Tests**

1. **Subtests**: Always use t.Run.  
2. **Parallelism**: If the code is thread-safe, add t.Parallel() inside the loop (and tc := tc capture if using Go versions < 1.22).  
3. **Naming**: Test functions must start with Test.  
4. **Helper Functions**: If setup is complex, create a func setupTest(`t *testing.T`) helper.