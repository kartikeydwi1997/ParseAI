# sample.py

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "Cannot divide by zero"
    return a / b

class Calculator:
    def __init__(self):
        self.history = []
    
    def compute(self, operation, a, b):
        if operation == "add":
            result = add(a, b)
        elif operation == "subtract":
            result = subtract(a, b)
        elif operation == "multiply":
            result = multiply(a, b)
        elif operation == "divide":
            result = divide(a, b)
        else:
            result = "Invalid operation"
        self.history.append((operation, a, b, result))
        return result

    def get_history(self):
        return self.history

import ast

class CodeParser(ast.NodeVisitor):
    def __init__(self):
        self.functions = {}  # Stores function names and line numbers
        self.classes = {}  # Stores class names and line numbers
        self.dependencies = {}  # Stores function call dependencies
        self.current_function = None  # Track which function is being visited

    def visit_FunctionDef(self, node):
        self.functions[node.name] = node.lineno  # Store function definitions
        self.dependencies[node.name] = []  # Initialize dependency tracking
        self.current_function = node.name  # Track current function
        self.generic_visit(node)
        self.current_function = None  # Reset after function visit

    def visit_ClassDef(self, node):
        self.classes[node.name] = node.lineno
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and self.current_function:
            called_function = node.func.id  # Function being called
            if called_function in self.functions:  # Ensure it's a defined function
                self.dependencies[self.current_function].append(called_function)
        self.generic_visit(node)

def parse_code(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    parser = CodeParser()
    parser.visit(tree)
    return parser.functions, parser.classes, parser.dependencies

# Simulating parsing of the file
parsed_functions, parsed_classes, parsed_dependencies = parse_code("sample.py")
print("Functions:", parsed_functions)
print("Classes:", parsed_classes)
print("Dependencies:", parsed_dependencies)
