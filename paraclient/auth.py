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
import copy
from urllib.parse import urlparse, quote_plus
import requests


class AWSAuth(requests.auth.AuthBase):
    auth = None

    def __init__(self, auth):
        self.auth = auth

    def __call__(self, r):
        query = {}
        multi_valued_params = False
        paramz = urlparse(r.url).query.split('&')
        querystring = ""
        if paramz and len(paramz) > 0:
            for param in paramz:
                if param:
                    key_val = param.split('=', 1)
                    key = key_val[0]
                    value = key_val[1]
                    # no spec on this case, so choose first param in array
                    if not multi_valued_params and key in query:
                        multi_valued_params = True
                    elif key and key not in query:
                        if querystring:
                            querystring += "&"
                        query[key] = value
                        querystring += u'='.join([key, quote_plus(value).replace("+", "%20")])

        if multi_valued_params:
            newr = copy.deepcopy(r)
            newr.url = newr.url.split("?")[0] + "?" + querystring
            self.auth.__call__(newr)
            r.headers.update(newr.headers)
        else:
            r.url = r.url.replace("+", "%20")
            self.auth.__call__(r)

        return r
