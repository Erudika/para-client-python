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


class Pager:
    """
    This class stores pagination data. It limits the results for queries in the DAO
    and Search objects and also counts the total number of results that are returned.
    @author Alex Bogdanovski [alex@erudika.com]
    """

    page: int = 1
    count: int = 0
    sortby: str = "timestamp"
    desc: bool = True
    limit: int = 0
    name: str = "Pager"
    lastKey: str = None
    select: list = None

    def __init__(self, page: int = 1, sortby: str = "timestamp", desc: bool = True, limit: int = 30):
        self.page = page
        self.sortby = sortby
        self.limit = limit
        self.desc = desc





