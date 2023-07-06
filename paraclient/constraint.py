"""
 * Copyright 2013-2023 Erudika. https://erudika.com
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * For issues and patches go to: https://github.com/erudika
"""


class Constraint:
    """
    Represents a validation constraint.
    @author Alex Bogdanovski [alex@erudika.com]
    """

    name: str
    payload: dict

    def __init__(self, name: str, payload: dict):
        self.name = name
        self.payload = payload

    @staticmethod
    def required():
        return Constraint("required", {"message": "messages.required"})

    @staticmethod
    def min(minimum: int = 0):
        return Constraint("min", {
            "message": {
                "value": minimum,
                "message": "messages.min"
            }
        })

    @staticmethod
    def max(maximum: int = 0):
        return Constraint("max", {
            "message": {
                "value": maximum,
                "message": "messages.max"
            }
        })

    @staticmethod
    def size(minimum: int = 0, maximum: int = 0):
        return Constraint("size", {
            "message": {
                "min": minimum,
                "max": maximum,
                "message": "messages.size"
            }
        })

    @staticmethod
    def digits(i: int = 0, f: int = 0):
        return Constraint("digits", {
            "message": {
                "integer": i,
                "fraction": f,
                "message": "messages.digits"
            }
        })

    @staticmethod
    def pattern(regex: str):
        return Constraint("pattern", {
            "message": {
                "value": regex,
                "message": "messages.pattern"
            }
        })

    @staticmethod
    def email():
        return Constraint("email", {"message": "messages.email"})

    @staticmethod
    def falsy():
        return Constraint("false", {"message": "messages.false"})

    @staticmethod
    def truthy():
        return Constraint("true", {"message": "messages.true"})

    @staticmethod
    def future():
        return Constraint("future", {"message": "messages.future"})

    @staticmethod
    def past():
        return Constraint("past", {"message": "messages.past"})

    @staticmethod
    def url():
        return Constraint("url", {"message": "messages.url"})
