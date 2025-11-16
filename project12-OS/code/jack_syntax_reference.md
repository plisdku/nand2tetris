# Jack Language Syntax Reference

## Class Declaration
```
class ClassName {
    // class body
}
```

## Variable Declarations
- `static type varName;` - class variables
- `field type varName;` - instance variables  
- `var type varName;` - local variables

## Method Types
- `function returnType methodName(params)` - static methods
- `method returnType methodName(params)` - instance methods
- `constructor ClassName new(params)` - constructors

## Data Types
- `int` - integers
- `char` - characters
- `boolean` - true/false
- `Array` - arrays
- `String` - strings
- `ClassName` - object references

## Statements
- `let varName = expression;` - assignment
- `if (condition) { statements }` - conditionals
- `if (condition) { statements } else { statements }` - if-else
- `while (condition) { statements }` - loops
- `do methodCall;` - method calls (void return)
- `return expression;` or `return;` - return statements

## Expressions
- Arithmetic: `+`, `-`, `*`, `/`
- Comparison: `<`, `>`, `=`
  - Note: `<=` implemented as `~(x > y)`, `>=` implemented as `~(x < y)`
- Logical: `&` (and), `|` (or), `~` (not)
- Array access: `arrayName[index]`
- Method calls: `ClassName.method()` or `object.method()`

## Special Values
- `this` - current object reference
- `null` - null reference
- Numbers: positive/negative integers
- Characters: single quotes (implied from context)

## Comments
- `//` - single line comments
- `/* */` - multi-line comments (inferred)

## Memory Management
- `Array.new(size)` - allocate array
- `object.dispose()` - deallocate object
- Direct memory access via `Memory.peek()/poke()`
