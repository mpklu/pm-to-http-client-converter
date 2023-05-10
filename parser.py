import json

class Assertion:
    def __init__(self, key, functions):
        self.key = key
        self.functions = functions

class Test:
    def __init__(self, description):
        self.description = description
        self.assertions = []

def parse_postman_test_script(script_path):
    with open(script_path, 'r') as f:
        script = f.read()
    
    assertions = []
    tests = []
    
    # Extract assertions
    for line in script.split('\n'):
        if 'pm.expect(' in line:
            key = line.split('(')[1].split(',')[0].strip()
            functions = []
            for function in line.split('to.')[1].split('('):
                if 'null' in function:
                    function_name = function.split(')')[0].strip()
                    functions.append(function_name)
            assertion = Assertion(key, functions)
            assertions.append(assertion)
    
    # Extract tests
    test_description = ''
    for line in script.split('\n'):
        if 'pm.test(' in line:
            test_description = line.split('(')[1].split(')')[0].strip('"')
            test = Test(test_description)
            tests.append(test)
        elif '});' in line:
            test.assertions = assertions.copy()
            assertions.clear()
    
    return tests

tests = parse_postman_test_script('postman.js')
for test in tests:
    print(f'Test: {test.description}')
    for assertion in test.assertions:
        print(f'Assertion: {assertion.key} should satisfy {assertion.functions}')
