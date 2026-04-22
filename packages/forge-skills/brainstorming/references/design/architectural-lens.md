# Architectural Lens

Use this as a design lens inside `forge-brainstorming`, not as a separate workflow.

## Use It When

- system boundaries may change
- data ownership is unclear
- auth, payment, migration, or compatibility constraints can reshape the solution
- a public interface or external contract may be added or changed
- a bug or feature request actually reveals a system-shape problem

## What To Clarify

- which unit owns the behavior
- which interface is public versus internal
- what data crosses each boundary
- where backward compatibility matters
- what failure mode should reopen design instead of being patched during build

## Output

The design doc should make boundary decisions explicit enough that `forge-writing-plans` can assign files, proof, and rollback safely.
