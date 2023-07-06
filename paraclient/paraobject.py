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
import json
import time
from urllib.parse import quote_plus


class ParaObject(dict):
    """
    A basic object for storing data - ParaObject.
    @author Alex Bogdanovski [alex@erudika.com]
    """

    id: str
    timestamp: int
    type: str = "sysprop"
    appid: str
    parentid: str
    creatorid: str
    updated: int
    name: str = "ParaObject"
    tags: list = []
    votes: int = 0
    version: int = 0
    stored: bool = True
    indexed: bool = True
    cached: bool = True

    def __init__(self, id_: str = None, type_: str = "sysprop"):
        dict.__init__(self)
        self.id = id_
        self.type = type_
        self.timestamp = int(round(time.time() * 1000))

    def urlenc(self, string: str):
        return quote_plus(string).replace("+", "%20")

    def getObjectURI(self):
        u = "/" + self.urlenc(self.type)
        return u + "/" + self.urlenc(self.id) if self.id else u

    def jsonSerialize(self):
        return json.dumps(self.__dict__)

    def setFields(self, data: dict):
        self.__dict__.update(data)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, val):
        setattr(self, key, val)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

