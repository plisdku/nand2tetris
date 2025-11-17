# Copilot Instructions for Jack Language Development

## Context
This workspace contains Jack language files (.jack) for implementing an operating system as part of the Nand2Tetris course.

## Important References
- **Syntax Reference**: Always refer to `jack_syntax_reference.md` for proper Jack language syntax when working with .jack files
- Jack is a simple object-oriented language with specific syntax rules and limitations

## Key Reminders
- Jack only has basic comparison operators (`<`, `>`, `=`) - use logical negation for `<=` and `>=`
 - Never edit files inside `*Test` directories; make changes in the `code/` directory only.
 - This environment cannot compile or run `.jack` files locally. The only available testing options are uploading files to the course/web app or preparing a submission and running tests there.
 - Subroutine call rules: if a subroutine is declared `function`, call it as `ClassName.subroutine()`; if declared `method`, call it as `do subroutine()` inside methods or `var.subroutine()` on objects. Keep declaration and call style consistent to avoid "called as a method" errors.

- Unit-test note: the web IDE provides fallback, correct implementations for other OS modules. For a unit test upload include only `Main.jack` and the single module file under test (e.g. `String.jack`). Do not copy the whole OS into the unit test.
- Succinctness: keep all diagnostic notes and generated `.md` files very short and to the point; prefer one-line notes and minimal examples.

- Edit rule: Do not modify workspace files unless the repository owner explicitly asks for the change.
 - Jack note: Jack string literals do not interpret escape sequences like `\n`. Call `do Output.println()` explicitly for newlines.

- Var-declarations: all `var` declarations must appear at the top of a subroutine (immediately after the `function`/`method`/`constructor` declaration), not interleaved with executable statements.
