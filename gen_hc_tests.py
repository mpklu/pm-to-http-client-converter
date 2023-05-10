# Author: Kun Lu
#
# Created on 2023-05-10 10:00:20

import json
import sys


class Request:
    def __init__(self, method, header, body, url):
        self.method = method
        self.header = header
        self.body = body
        self.url = url

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
                Options(data["body"]["options"]["raw"])
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


class Header:
    def __init__(self, key, value):
        self.key = key
        self.value = value


class Body:
    def __init__(self, mode, raw, options):
        self.mode = mode
        self.raw = raw
        self.options = options


class Options:
    def __init__(self, raw):
        self.raw = raw


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


def find_request(data):
    if isinstance(data, dict):
        if "request" in data:
            return [data]
        else:
            inner_items = []
            for value in data.values():
                inner_items.extend(find_request(value))
            return inner_items
    elif isinstance(data, list):
        inner_items = []
        for item in data:
            inner_items.extend(find_request(item))
        return inner_items
    else:
        return []


def build_test_cases(data):
    requests = find_request(data)
    for endpoint in requests:
        print(endpoint["name"])
        req = Request.from_json_data(endpoint["request"])
        print(req.url.raw)

        # print(req["method"])
    return "TBD"


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python gen_hc_test.py <path/to/collection/json/file>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        json_data = json.load(f)

    test_cases = build_test_cases(json_data)
    print(test_cases)
