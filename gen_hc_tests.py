# Author: Kun Lu
#
# Created on 2023-05-11 10:00:20

import json
import sys
import re

#
# Postman Test Parser
# 
TEST_SCOPE = 'test'
EMBEDDED_TEST_SCOPE = 'removed'
ITERATION_SCOPE = 'for-each'
CONDITION = "if"
FUNCTION = "func"

# JS semantics
class Scope: 
    def __init__(self, type):
        self.type = type

    def is_test(self):
        return self.type == TEST_SCOPE or self.type == EMBEDDED_TEST_SCOPE
    
    def is_embedded_test(self):
        return self.type == EMBEDDED_TEST_SCOPE

    # forEach( (obj) => {
    #    ...
    # });
    def is_iteration(self):
        return self.type == ITERATION_SCOPE

# http-client does not support multi-level client.test()
# When we encounter an inner-level `pm.test`,
# we change it to a log, and remove the pm.test closure block.
# We use a Stack to keep track of closure block scopes
class Stack:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return len(self.items) == 0

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if self.is_empty():
            return None
        return self.items.pop()

    def peek(self):
        if self.is_empty():
            return None
        return self.items[-1]

    def size(self):
        return len(self.items)

    def has_test(self):
        if self.is_empty():
            return False
        else:
            for scope in self.items:
                if scope.is_test():
                    return True

        return False

    def has_test_do_not_use(self):
        found = False

        # Create a temporary stack to store the popped elements
        temp_stack = Stack()

        # Pop elements from the original stack and search for the item
        while not self.is_empty():
            scope = self.pop()
            temp_stack.push(scope)

            if (not found) and scope.is_test():
                found = True                

        # Pop elements back from the temporary stack to restore the original stack
        while not temp_stack.is_empty():
            self.push(temp_stack.pop())

        return found

    def is_in_test(self):
        if self.is_empty():
            return False
        else:            
            # return self.peek().is_test()
            return self.has_test() # the last item may not necessarily a test

 

class Assertion:
    def __init__(self, key, desc, functions):
        self.key = key
        self.description = desc
        self.functions = functions

    def get_assertion(self, function_name):
        if function_name.startswith("typeof"):
            type = function_name.split('peof ')[1]
            if type == "array":
                return f'Array.isArray({self.key})'
            else: 
                return f'typeof {self.key} === "{type}"'
        else:
            return f'{function_name}({self.key})'
    # ex:
    # client.assert(typeof obj.id === "number", "obj.id should be a number");
    # client.assert(nullOrNumber(obj.mc), "obj.mc should be a number or null");
    def to_http_client_script(self):
        if len(self.functions) > 0:
            assertion = None
            while len(self.functions) > 0:
                func = self.functions.pop()
                if not assertion:
                    assertion = self.get_assertion(func)
                else:
                    assertion += ' || ' + self.get_assertion(func)

            desc = self.description if self.description else ''
            return f'client.assert({assertion}, "{desc}");'
        else:
            return f'client.assert(false, "error: missing assert function for key: {self.key}");'    


class Test:
    def __init__(self, description):
        self.description = description
        self.assertions = []

    # ex: client.test("Each object in the response has the required fields and data types", function() { 
    def to_http_client_script(self):
        return f'client.test("{self.description}", function() {{\n'


def extract_key(line):
    # Regular expression pattern to match both patterns
    # The ([^,)]+) part matches one or more characters that are not a comma (,) or a closing parenthesis ()).
    # The (?:,|\)) part matches either a comma or a closing parenthesis, but it does not capture it.
    # This allows us to handle cases where there is additional content after the closing parenthesis
    # without including that content in the extracted value.
    pattern = r'pm\.expect\(([^,)]+)(?:,|\))'
    match = re.search(pattern, line)
    if match:
        return match.group(1)
    else:
        print("match not found")
        print(line)
        return None

def extract_desc(line):
    match = re.search(r'"([^"]+)"', line)
    if match:
        description = match.group(1)
    else:
        description = None

    return description

# This only finds the first function name
def extract_function_name_do_not_use(closure):
    pattern = r'\(\w+\)\s*=>\s*{(?:\s*return\s*)?(\w+)\('
    match = re.search(pattern, closure)
    if match:
        return match.group(1)
    else:
        return None

def extract_function_names(closure):
    pattern = r'return\s+([a-zA-Z_][a-zA-Z0-9_]*)\([^)]*\)(?:\s*\|\|\s*([a-zA-Z_][a-zA-Z0-9_]*)\([^)]*\))?'
    matches = re.findall(pattern, closure)
    functions = [match[0] for match in matches]
    if matches and matches[0][1]:
        functions.append(matches[0][1])

    return functions

def extract_type(line):
    pattern = r'\.to\.be\.(?:a|an)\("([^"]+)"\);'
    match = re.search(pattern, line)
    if match:
        return match.group(1)
    else:
        return None

def starts_with_vowel(word):
    vowels = ['a', 'e', 'i', 'o', 'u']
    return  word.lower()[0] in vowels

# convert the line with "pm.expect"
def convert_assertion(line):
    key = extract_key(line)
    if key:
        functions = []
        function_names = []
        desc = ''
        if 'to.satisfy(' in line:
            function_names = extract_function_names(line.split('to.satisfy(')[1])
            desc = extract_desc(line)
        elif 'to.be.a' in line:
            type = extract_type(line)
            if type:
                function_names = ["typeof " + type]
                ia = 'an' if starts_with_vowel(type) else 'a'
                desc = f'{key} should be {ia} {type}'
            else:
                function_names = [line.split('.')[1]]

        assertion = Assertion(key, desc, function_names)
        return assertion.to_http_client_script()

# does not work well
# Not all postman test line have proper indentation
def get_indentation_do_not_use(string):
    indentation_count = 0
    while string.startswith('\t'):
        indentation_count += 1
        # Remove the first character (a tab) from the string
        string = string[1:]
    return '\t'*indentation_count

def get_indentation(stack):
    level_count = stack.size()
    return '\t'*level_count if level_count > 0 else ''


def convert_line(line, stack):
    line = line.strip()
    indentation = get_indentation(stack)
    if line.startswith('pm.test('):
        test_description = line.split('(')[1].split(',')[0].strip('"')
        if stack.is_in_test():
            # no embedded test allowed, just log the description
            ret = indentation + f'client.log("testing object properties ... {test_description}");'
            stack.push(Scope(EMBEDDED_TEST_SCOPE))
        else:            
            test = Test(test_description)
            ret = indentation + test.to_http_client_script()
            stack.push(Scope(TEST_SCOPE))
    elif line.startswith('pm.expect('):
        ret = indentation + convert_assertion(line)
    elif 'forEach(' in line:        
        ret = indentation + line
        stack.push(Scope(ITERATION_SCOPE))
    elif line.startswith('if'):
        ret = indentation + line
        stack.push(Scope(CONDITION))
    elif line == '});':
        scope = stack.pop()
        indentation = get_indentation(stack) # update indentation for ending scope token
        if scope:
            if scope.is_embedded_test():
                ret = None
            elif scope.is_iteration():
                ret = indentation + line
            elif scope.is_test():
                ret = indentation + line
    elif line.startswith('function') and line.endswith('{'):
        ret = indentation + line
        stack.push(Scope(FUNCTION))
    elif line == '}':
        stack.pop()
        indentation = get_indentation(stack)
        ret = indentation + line
    elif 'pm.response.json()' in line:
        ret = '' # remove line 'const response = pm.response.json();'
    else:
        ret = indentation + line
    
    if ret:
        return ret.replace('response', 'response.body') + '\n'
    else:
        return None # A removed line


def convert(script):
    ret = ''

    my_stack = Stack()
    for line in script.split('\n'):
        converted = convert_line(line, my_stack)
        ret += converted if converted else ''
    return ret

#
# Request Parser
# 

class Request:
    def __init__(self, method, header, body, url, needsAuth=True):
        self.method = method
        self.header = header
        self.body = body
        self.url = url
        self.needsAuth = needsAuth

    @classmethod
    def from_json_data(cls, data):
        header_list = [Header(h["key"], h["value"]) for h in data["header"]]        
        query_list = [Query(q["key"], q["value"], q["description"])
                      for q in data["url"]["query"]]
        variable_list = [Variable(v["key"], v["value"], v["description"])
                         for v in data["url"]["variable"]]
        body = None
        if "body" in data:
            body = Body(
                data["body"]["mode"],
                data["body"]["raw"],
                Options(Raw(data["body"]["options"]["raw"]["language"]))
            )

        url = Url(
            data["url"]["raw"],
            data["url"]["host"],
            data["url"]["path"],
            query_list,
            variable_list
        ) if "url" in data else None
       

        return Request(
            data["method"],
            header_list,
            body,
            url
        )

    def to_http_client(self):
        ret = f"""
###
{self.method} {self.url.raw}
"""
        ret += "Authorization: Bearer {{token}}" if self.needsAuth else ''
        ret += self.body.to_http_client() if self.body else ''
        return ret


class Header:
    def __init__(self, key, value):
        self.key = key
        self.value = value


class Body:
    def __init__(self, mode, raw, options):
        self.mode = mode
        self.raw = raw
        self.options = options

    def to_http_client(self):
        if self.options.raw.language == 'json' and self.raw:
            return f"""
Content-Type: application/json

{self.raw}

"""
        return ""

class Options:
    def __init__(self, raw):
        self.raw = raw

class Raw:
    def __init__(self, language):
        self.language = language

class Url:
    def __init__(self, raw, host, path, query, variable):
        self.raw = raw
        self.host = host
        self.path = path
        self.query = query
        self.variable = variable


class Query:
    def __init__(self, key, value, description):
        self.key = key
        self.value = value
        self.description = description


class Variable:
    def __init__(self, key, value, description):
        self.key = key
        self.value = value
        self.description = description

class Event:
    def __init__(self, data):
        self.listen = data.get('listen', '')
        script = data.get('script', {})
        self.exec = script.get('exec', [])
        self.script_type = script.get('type', '')

    def is_test(self):
        return self.listen == 'test'


class Endpoint:
    def __init__(self, name, request, event):
        self.name = name
        self.request = request
        self.event = event

    def to_http_client(self):
        ret = '\n'
        if self.request.needsAuth:
            ret += AUTH_REQUEST

        ret += self.request.to_http_client()
        
        ret += '\n\n'

        if self.event and self.event.is_test():
            ret += convert('\n'.join(self.event.exec))


        return ret

def find_api_items(data):
    if isinstance(data, dict):
        if "request" in data:
            return [data]
        else:
            inner_items = []
            for value in data.values():
                inner_items.extend(find_api_items(value))
            return inner_items
    elif isinstance(data, list):
        inner_items = []
        for item in data:
            inner_items.extend(find_api_items(item))
        return inner_items
    else:
        return []

# returns the first 'test' event
def find_test(events):
    while len(events) != 0:
        event = events.pop()
        if "listen" in event and event["listen"] == "test":
            return Event(event)
    return None

#
# Convert tests
#

AUTH_REQUEST = """
###
POST {{baseUrl}}/ChiralRest/Authenticate/login
Content-Type: application/json

{
  "groupId": "{{groupId}}",
  "mcId": {{practiceId}},
  "username": "superuser",
  "password": "{{password}}"
}

> {%
if (response.status === 200) {
    client.log("Login success!");
} else {
    client.log(`login error: ${response.status}`)
}


if (response.body.token.length > 0) {
    client.log("Got token: ");
    client.global.set("token", response.body.token);
}

 %}

"""
def build_test_cases(data):
    ret = ''
    items = find_api_items(data)
    for endpoint in items:
        req = Request.from_json_data(endpoint["request"])
        # print(req.url.raw)

        event = None
        if isinstance(endpoint["event"], list) and len(endpoint["event"]) > 0:
            event = find_test(endpoint["event"])
           
        endpoint = Endpoint(endpoint["name"], req, event)        
        ret += endpoint.to_http_client() + '\n\n'

    return ret


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python gen_hc_test.py <path/to/collection/json/file>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        json_data = json.load(f)

    test_cases = build_test_cases(json_data)
    print(test_cases)
    
