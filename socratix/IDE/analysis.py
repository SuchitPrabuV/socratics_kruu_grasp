import ast

def analyze_structure(code_string):
    """
    Analyzes the Python code for structural elements using AST.
    Returns a dictionary of found concepts and potential missing logic.
    """
    results = {
        'status': 'valid_syntax',
        'concepts_found': [],
        'structure_map': {}
    }

    try:
        tree = ast.parse(code_string)
    except SyntaxError as e:
        return {
            'status': 'syntax_error',
            'error': str(e),
            'line': e.lineno
        }

    # Helper to traverse and tag concepts
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            results['concepts_found'].append('function_definition')
            results['structure_map']['function_name'] = node.name
        elif isinstance(node, ast.For):
            results['concepts_found'].append('for_loop')
        elif isinstance(node, ast.While):
            results['concepts_found'].append('while_loop')
        elif isinstance(node, ast.If):
            results['concepts_found'].append('conditional')
        elif isinstance(node, ast.Return):
            results['concepts_found'].append('return_statement')
        elif isinstance(node, ast.Call):
            if hasattr(node.func, 'id') and node.func.id == 'print':
                results['concepts_found'].append('print_statement')

    return results
