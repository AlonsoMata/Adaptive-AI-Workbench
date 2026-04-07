Redesign presets as universal response controls and harden workflow generation

- replace domain-specific presets with reusable universal response controls
- add structured controls for tone, length, language, style, format, and strictness
- migrate built-in packs and profiles to generic response-profile ids
- preserve backward compatibility through legacy preset alias mapping
- update execution and prompt construction to use universal controls end-to-end
- replace preset selection in the UI with a clear universal controls panel
- keep candidate review, install, and runtime execution flows working
- harden template/profile loading against BOM-encoded files
- improve candidate generation reliability with a larger output token budget
- detect truncated candidate-pack JSON more accurately during parsing
- add regression coverage for migration, parsing, execution, and UI behavior
