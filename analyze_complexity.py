import os
import ast
import mccabe

# List of files/directories to exclude
EXCLUDE = ['__pycache__', '__init__.py', 'venv', 'LICENSE']

def is_excluded(file_path):
    for pattern in EXCLUDE:
        if pattern in file_path:
            return True
    return False

def get_complexity(code):
    tree = ast.parse(code)
    visitor = mccabe.PathGraphingAstVisitor()
    visitor.preorder(tree, visitor)
    return visitor.graphs

def analyze_file(file_path):
    with open(file_path, 'r') as file:
        code = file.read()
    try:
        complexity = get_complexity(code)
        for function in complexity:
            yield file_path, function, complexity[function].complexity()
    except SyntaxError:
        print(f"Syntax error in file: {file_path}")

def analyze_project(root_dir):
    results = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE]  # Exclude directories
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.py') and not is_excluded(file_path):  # Exclude specific files
                results.extend(analyze_file(file_path))
    return results

def main():
    project_root = '.' 
    results = analyze_project(project_root)
    
    # Sort results by complexity
    sorted_results = sorted(results, key=lambda x: x[2], reverse=True)
    
    # Print results
    print("File Path | Function Name | Complexity")
    print("-" * 50)
    for file_path, function_name, complexity in sorted_results:
        print(f"{file_path} | {function_name} | {complexity}")

    # Calculate average complexity
    avg_complexity = sum(r[2] for r in results) / len(results) if results else 0
    print(f"\nAverage Complexity: {avg_complexity:.2f}")

if __name__ == "__main__":
    main()
