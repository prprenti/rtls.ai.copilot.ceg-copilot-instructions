---
applyTo: "**/*.sv,**/*.svh,**/{uvm_checker,uvm_coverage,sideband_sequence,test_generator_template}.prompt.md"
---


# DVT tools for SV code

We use DVT to compile and analyze our SystemVerilog code.
**IMPORTANT:** Whenever possible you must use DVT tools to ensure code quality and consistency. Do not grep through the code base manually unless absolutely necessary.

`dvt_get_symbol_definitions`         -> Retrieves the full source code definitions of symbols (e.g., classes, modules, interfaces).
`dvt_get_symbol_locations`           -> Finds where symbols are defined in the project (file path and line range).
`dvt_get_symbol_references`          -> Finds all usages of a symbol across the project.
`dvt_get_identifier_references`      -> Finds all usages of a specific identifier (e.g., variable, function parameter) across the project.
`dvt_get_symbol_dependencies`        -> Retrieves source code definitions of all symbols that a given symbol depends on.
`dvt_get_compiled_files_tree`        -> Shows all compiled files in the project as a hierarchical tree.
`dvt_get_design_top`                 -> Retrieves the top-level design element(s) in the project.
`dvt_get_design_subinstances`        -> Lists all sub-instances of a specified design element.
`dvt_get_verification_top`           -> Gets the top-level UVM component.
`dvt_get_verification_subcomponents` -> Lists all subcomponents of a specified UVM component.
`dvt_get_file_identifiers`           -> Lists all identifiers in a file, grouped by line.
`dvt_get_problems`                   -> Retrieves compilation problems (errors/warnings) for a given file.
