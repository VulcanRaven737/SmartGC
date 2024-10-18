import json
from clang.cindex import CursorKind, Index
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

@dataclass
class VariableReference:
    function_name: str
    variable_name: str
    line_number: int

class ScopeTracker:
    def __init__(self):
        self.references: Dict[Tuple[str, str], VariableReference] = {}
        self.deallocations: List[dict] = []
        self.current_function: str = ""

    def add_reference(self, var_name: str, line_number: int):
        key = (self.current_function, var_name)
        self.references[key] = VariableReference(
            function_name=self.current_function,
            variable_name=var_name,
            line_number=line_number
        )

    def update_reference_line(self, var_name: str, new_line: int):
        key = (self.current_function, var_name)
        if key in self.references:
            ref = self.references[key]
            ref.line_number = new_line

    def get_reference(self, var_name: str) -> VariableReference:
        key = (self.current_function, var_name)
        return self.references.get(key)

def traverse_ast(node, scope_tracker: ScopeTracker, start_line=None, end_line=None):
    if node.kind == CursorKind.FUNCTION_DECL:
        scope_tracker.current_function = node.spelling

    if start_line is None:
        start_line = node.location.line

    if node.kind in (CursorKind.FOR_STMT, CursorKind.WHILE_STMT):
        start_line = node.location.line
        end_line = node.extent.end.line

    if node.kind == CursorKind.DECL_REF_EXPR:
        if node.referenced and node.referenced.kind == CursorKind.VAR_DECL:
            var_name = node.spelling
            scope_tracker.add_reference(var_name, node.location.line)

    for child in node.get_children():
        traverse_ast(child, scope_tracker, start_line, end_line)

    if node.kind in (CursorKind.FOR_STMT, CursorKind.WHILE_STMT):
        for key, ref in scope_tracker.references.items():
            if ref.function_name == scope_tracker.current_function:
                if start_line <= ref.line_number <= end_line:
                    scope_tracker.update_reference_line(ref.variable_name, end_line)

def check_alloc_term(filename: str, line_number: int, var_name: str) -> bool:
    with open(filename, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if "alloc" in line and f"*{var_name}" in line:
                return True
    return False

def main(input_file: str, json_file: str):
    index = Index.create()
    tu = index.parse(input_file, args=['-std=c11'])
    print('Translation unit:', tu.spelling)

    scope_tracker = ScopeTracker()

    for node in tu.cursor.get_children():
        if node.kind == CursorKind.FUNCTION_DECL:
            traverse_ast(node, scope_tracker)

    # Process deallocations
    for (func_name, var_name), ref in scope_tracker.references.items():
        if check_alloc_term(input_file, ref.line_number, var_name):
            scope_tracker.deallocations.append({
                "function_name": func_name,
                "line_number": ref.line_number,
                "variable_name": var_name
            })

    output = {
        "deallocations": scope_tracker.deallocations
    }

    if scope_tracker.deallocations:
        with open(json_file, 'w') as f:
            json.dump(output, f, indent=4)
        print("Data written to references.json")
    else:
        print("No deallocations found.")