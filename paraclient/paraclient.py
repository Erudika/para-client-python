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
import logging
import time
import base64
from builtins import object
from json import JSONDecodeError
from urllib.parse import quote_plus
import requests
from aws_requests_auth.aws_auth import AWSRequestsAuth
from requests import RequestException, Response
from paraclient.auth import AWSAuth
from paraclient.constraint import Constraint
from paraclient.pager import Pager
from paraclient.paraobject import ParaObject


class ParaClient:
    """
    Python client for communicating with a Para backend server.
    @author: Alex Bogdanovski [alex@erudika.com]
    """

    DEFAULT_ENDPOINT = "https://paraio.com"
    DEFAULT_PATH = "/v1/"
    JWT_PATH = "/jwt_auth"
    SEPARATOR = ":"

    __endpoint: str
    __accessKey: str
    __secretKey: str
    __path: str = DEFAULT_PATH
    __tokenKey: str = None
    __tokenKeyExpires: int = None
    __tokenKeyNextRefresh: int = None

    def __init__(self, accessKey: str, secretKey: str):
        self.__accessKey = accessKey
        self.__secretKey = secretKey
        self.__endpoint = self.DEFAULT_ENDPOINT

    def setEndpoint(self, endpoint: str):
        """
        Sets the API endpoint URL
        @param endpoint: endpoint URL
        """
        self.__endpoint = endpoint if endpoint else self.DEFAULT_ENDPOINT

    def getEndpoint(self):
        """
        Returns the endpoint URL
        @return: the endpoint
        """
        if not self.__endpoint:
            return self.DEFAULT_ENDPOINT
        else:
            return self.__endpoint

    def setApiPath(self, path: str):
        """
        Sets the API request path
        @param path: a new path
        """
        self.__path = path

    def getApiPath(self):
        """
        Returns the API request path
        @return: the request path without parameters
        """
        if not self.__path:
            return self.DEFAULT_ENDPOINT
        else:
            if not self.__path.endswith("/"):
                self.__path += "/"
            return self.__path

    def getApp(self):
        """
        Returns the App for the current access key (appid).
        @return: the App object
        """
        return self.me()

    def getServerVersion(self):
        """
        @return: the version of Para server
        """
        res = self.getEntity(self.invokeGet(""))
        if not res or not res["version"]:
            return "unknown"
        else:
            return res["version"]

    def getAccessToken(self):
        """
        @return: returns the JWT access token, or null if not signed in
        """
        return self.__tokenKey

    def setAccessToken(self, token: str):
        """
        Sets the JWT access token.
        @param token: a valid JWT access token
        """
        if token:
            parts = token.split(".")
            decoded = json.loads(base64.b64decode(parts[1] + "==").decode("utf-8"))
            if decoded and "exp" in decoded:
                self.__tokenKeyExpires = decoded.get("exp")
                self.__tokenKeyNextRefresh = decoded.get("refresh")
            else:
                del self.__tokenKeyExpires
                del self.__tokenKeyNextRefresh
        self.__tokenKey = token

    def clearAccessToken(self):
        """
        Clears the JWT token from memory, if such exists.
        """
        del self.__tokenKey
        del self.__tokenKeyExpires
        del self.__tokenKeyNextRefresh

    @staticmethod
    def urlenc(string: str):
        return quote_plus(string).replace("+", "%20")

    @staticmethod
    def getEntity(res: Response, returnRawJSON: bool = True):
        """
        Deserializes a Response object to POJO of some type.
        @param res: response
        @param returnRawJSON: true if an array should be returned
        @return: an object
        """
        if res:
            code = res.status_code
            if code == 200 or code == 201 or code == 304:
                if returnRawJSON:
                    try:
                        body = res.json()
                        return body if body else {}
                    except JSONDecodeError:
                        return res.text
                else:
                    obj = ParaObject()
                    obj.setFields(res.json())
                    return obj
            elif code != 404 or code != 304 or code != 204:
                error = res.json()
                if error and error["code"]:
                    msg = (error["message"] if error["message"] else "error")
                    logging.error(msg + " - " + error["code"])
                else:
                    logging.error(code + " - " + res.reason)
        return None

    def getFullPath(self, resourcepath: str):
        """
        @param resourcepath: API subpath
        @return: the full resource path, e.g. "/v1/path"
        """
        if resourcepath and resourcepath.startswith(self.JWT_PATH):
            return resourcepath
        if not resourcepath:
            resourcepath = ""
        elif resourcepath.startswith("/"):
            resourcepath = resourcepath[1:]
        return self.getApiPath() + resourcepath

    def invokeGet(self, resourcePath: str = "/", params=None):
        """
        Invoke a GET request to the Para API.
        @param resourcePath: the subpath after '/v1/', should not start with '/'
        @param params: query parameters
        @return: response object
        """
        if params is None:
            params = {}
        return self.invokeSignedRequest(httpMethod="GET", endpointURL=self.getEndpoint(),
                                        reqPath=self.getFullPath(resourcePath), params=params)

    def invokePost(self, resourcePath: str = "/", entity: str = None):
        """
        Invoke a POST request to the Para API.
        @param resourcePath: the subpath after '/v1/', should not start with '/'
        @param entity: request body
        @return: response object
        """
        return self.invokeSignedRequest(httpMethod="POST", endpointURL=self.getEndpoint(),
                                        reqPath=self.getFullPath(resourcePath), jsonEntity=entity)

    def invokePut(self, resourcePath: str = "/", entity: str = None):
        """
        Invoke a PUT request to the Para API.
        @param resourcePath: the subpath after '/v1/', should not start with '/'
        @param entity: request body
        @return: response object
        """
        return self.invokeSignedRequest(httpMethod="PUT", endpointURL=self.getEndpoint(),
                                        reqPath=self.getFullPath(resourcePath), jsonEntity=entity)

    def invokePatch(self, resourcePath: str = "/", entity: str = None):
        """
        Invoke a PATCH request to the Para API.
        @param resourcePath: the subpath after '/v1/', should not start with '/'
        @param entity: request body
        @return: response object
        """
        return self.invokeSignedRequest(httpMethod="PATCH", endpointURL=self.getEndpoint(),
                                        reqPath=self.getFullPath(resourcePath), jsonEntity=entity)

    def invokeDelete(self, resourcePath: str = "/", params=None):
        """
        Invoke a DELETE request to the Para API.
        @param resourcePath: the subpath after '/v1/', should not start with '/'
        @param params: query parameters
        @return: response object
        """
        if params is None:
            params = {}
        return self.invokeSignedRequest(httpMethod="DELETE", endpointURL=self.getEndpoint(),
                                        reqPath=self.getFullPath(resourcePath), params=params)

    def invokeSignedRequest(self, httpMethod: str, endpointURL: str, reqPath: str,
                            headers=None, params=None, jsonEntity: str = None):
        if headers is None:
            headers = {}
        if params is None:
            params = {}
        if not self.__accessKey:
            logging.error("Blank access key: " + httpMethod + " " + reqPath)
            return None

        do_sign = (not self.__tokenKey or self.__tokenKey is None)
        if not self.__secretKey and not self.__tokenKey:
            headers["Authorization"] = "Anonymous " + self.__accessKey
            do_sign = False

        if self.__tokenKey:
            if not (httpMethod == "GET" and reqPath == self.JWT_PATH):
                self.refreshToken()
            headers["Authorization"] = "Bearer " + self.__tokenKey

        response = None
        try:
            if do_sign:
                auth = AWSRequestsAuth(aws_access_key=self.__accessKey, aws_secret_access_key=self.__secretKey,
                                       aws_host=self.getEndpoint().replace("http://", "").replace("https://", ""),
                                       aws_region='us-east-1', aws_service='para')
                response = requests.request(httpMethod, url=(endpointURL + reqPath), auth=AWSAuth(auth), params=params,
                                            headers=headers, data=jsonEntity)
                # print("sign ", httpMethod, reqPath, response.status_code)
            else:
                response = requests.request(httpMethod, url=(endpointURL + reqPath), params=params,
                                            headers=headers, data=jsonEntity)
        except RequestException:
            logging.error("Request " + httpMethod + " " + reqPath + " failed!")

        return response

    @staticmethod
    def pagerToParams(p: Pager = None):
        """
        Converts a {@link Pager} object to query parameters.
        @param p: a pager
        @return: a list of query parameters
        """
        parammap = {}
        if p:
            parammap["page"] = p.page
            parammap["desc"] = str(p.desc).lower()
            parammap["limit"] = p.limit
            if p.lastKey:
                parammap["lastKey"] = p.lastKey
            if p.sortby:
                parammap["sort"] = p.sortby
            if p.select:
                parammap["select"] = p.select
        return parammap

    @staticmethod
    def getItemsFromList(result: list):
        """
        Deserializes ParaObjects from a JSON array (the "items:[]" field in search results).
        @param result: a list of deserialized objects
        @return: a list of ParaObjects
        """
        if result and len(result) > 0:
            # this isn't very efficient but there's no way to know what type of objects we're reading
            objects = []
            for obj in result:
                if obj and len(obj) > 0:
                    p = ParaObject()
                    p.setFields(obj)
                    objects.append(p)
            return objects
        return []

    def getItems(self, result: dict, at: str = "items", pager: Pager = None):
        """
        Converts a list of Maps to a List of ParaObjects, at a given path within the JSON tree structure.
        @param result: the response body for an API request
        @param at: the path (field) where the array of objects is located (defaults to 'items')
        @param pager: a pager
        @return: a list of ParaObjects
        """
        if result and at and at in result:
            if pager and "totalHits" in result:
                pager.count = result["totalHits"]
            if pager and "lastKey" in result:
                pager.lastKey = result["lastKey"]
            return self.getItemsFromList(result[at])
        return []

    # /////////////////////////////////////////////
    # //				 PERSISTENCE
    # /////////////////////////////////////////////

    def create(self, obj: ParaObject):
        """
        Persists an object to the data store. If the object's type and id are given,
        then the request will be a {@code PUT} request and any existing object will be overwritten.
        @param obj: the domain object
        @return: the same object with assigned id or null if not created.
        """
        if not obj:
            return None
        if obj.id and obj.type:
            return self.getEntity(self.invokePut(obj.getObjectURI(), obj.jsonSerialize()), False)
        else:
            return self.getEntity(self.invokePost(self.urlenc(obj.type), obj.jsonSerialize()), False)

    def read(self, type_: str = None, id_: str = None):
        """
        Retrieves an object from the data store.
        @param type_: the type of the object
        @param id_: the id of the object
        @return: the retrieved object or null if not found
        """
        if not id_:
            return None
        if type_:
            return self.getEntity(self.invokeGet(self.urlenc(type_) + "/" + self.urlenc(id_)), False)
        else:
            return self.getEntity(self.invokeGet("_id/" + self.urlenc(id_)), False)

    def update(self, obj: ParaObject):
        """
        Updates an object permanently. Supports partial updates.
        @param obj: the object to update
        @return: updated object
        """
        if not obj:
            return None
        return self.getEntity(self.invokePatch(obj.getObjectURI(), obj.jsonSerialize()), False)

    def delete(self, obj: ParaObject):
        """
        Deletes an object permanently.
        @param obj: the object
        """
        if obj:
            self.invokeDelete(obj.getObjectURI())

    def createAll(self, objects: list):
        """
        Saves multiple objects to the data store.
        @param objects: the list of objects to save
        @return: a list of objects
        """
        if not objects or not objects[0]:
            return []
        return self.getItemsFromList(self.getEntity(self.invokePost("_batch",
                                                                    json.dumps([obj.__dict__ for obj in objects]))))

    def readAll(self, keys: list):
        """
        Retrieves multiple objects from the data store.
        @param keys: a list of object ids
        @return: a list of objects
        """
        if not keys:
            return []
        return self.getItemsFromList(self.getEntity(self.invokeGet("_batch", {"ids": keys})))

    def updateAll(self, objects: list):
        """
        Updates multiple objects.
        @param objects: the objects to update
        @return: a list of objects
        """
        if not objects:
            return []
        return self.getItemsFromList(self.getEntity(self.invokePatch("_batch",
                                                                     json.dumps([obj.__dict__ for obj in objects]))))

    def deleteAll(self, keys: list):
        """
        Deletes multiple objects.
        @param keys: the ids of the objects to delete
        """
        if not keys:
            return
        self.invokeDelete("_batch", {"ids": keys})

    def list(self, type_: str = None, pager: Pager = None):
        """
        Returns a list all objects found for the given type.
        The result is paginated so only one page of items is returned, at a time.
        @param type_: the type of objects to search for
        @param pager: a Pager
        @return: a list of objects
        """
        if not type_:
            return []
        return self.getItems(self.getEntity(self.invokeGet(self.urlenc(type_), self.pagerToParams(pager))), pager=pager)

    # /////////////////////////////////////////////
    # //				 SEARCH
    # /////////////////////////////////////////////

    def findById(self, id_: str):
        """
        Simple id search.
        @param id_: the id
        @return: the object if found or null
        """
        objects = self.getItems(self.find("id", {"id": id_}))
        return objects[0] if objects else None

    def findByIds(self, ids: list):
        """
        Simple multi id search.
        @param ids: a list of ids to search for
        @return: the object if found or null
        """
        return self.getItems(self.find("ids", {"ids": ids}))

    def findNearby(self, type_: str, query: str, radius: int, lat: float, lng: float, pager: Pager = None):
        """
        Search for Address objects in a radius of X km from a given point.
        @param type_: the type of object to search for. @see ParaObject::type
        @param query: the query string
        @param radius: the radius of the search circle (in km)
        @param lat: latitude
        @param lng: longitude
        @param pager: a Pager
        @return: a list of objects found
        """
        params = self.pagerToParams(pager)
        params["latlng"] = str(lat) + "," + str(lng)
        params["radius"] = str(radius)
        params["q"] = query
        params["type"] = type_
        return self.getItems(self.find("nearby", params), pager=pager)

    def findPrefix(self, type_: str, field: str, prefix: str, pager: Pager = None):
        """
        Searches for objects that have a property which value starts with a given prefix.
        @param type_: the type of object to search for. @see ParaObject::type
        @param field: the property name of an object
        @param prefix: the prefix
        @param pager: a Pager
        @return: a list of objects found
        """
        params = self.pagerToParams(pager)
        params["field"] = field
        params["prefix"] = prefix
        params["type"] = type_
        return self.getItems(self.find("prefix", params), pager=pager)

    def findQuery(self, type_: str, query: str, pager: Pager = None):
        """
        Simple query string search. This is the basic search method.
        @param type_: the type of object to search for. @see ParaObject::type
        @param query: the query string
        @param pager: a Pager
        @return: a list of objects found
        """
        params = self.pagerToParams(pager)
        params["q"] = query
        params["type"] = type_
        return self.getItems(self.find("", params), pager=pager)

    def findNestedQuery(self, type_: str, field: str, query: str, pager: Pager = None):
        """
        Searches within a nested field. The objects of the given type must contain a nested field "nstd".
        @param type_: the type of object to search for. @see ParaObject::type
        @param field: the name of the field to target (within a nested field "nstd")
        @param query: the query string
        @param pager: a Pager
        @return: a list of objects found
        """
        params = self.pagerToParams(pager)
        params["q"] = query
        params["field"] = field
        params["type"] = type_
        return self.getItems(self.find("nested", params), pager=pager)

    def findSimilar(self, type_: str, filterkey: str, fields: list, liketext: str, pager: Pager = None):
        """
        Searches for objects that have similar property values to a given text. A "find like this" query.
        @param type_: the type of object to search for. @see ParaObject::type
        @param filterkey: exclude an object with this key from the results (optional)
        @param fields: a list of property names
        @param liketext: text to compare to
        @param pager: a Pager
        @return: a list of objects found
        """
        params = self.pagerToParams(pager)
        params["fields"] = fields if fields else None
        params["filterid"] = filterkey
        params["like"] = liketext
        params["type"] = type_
        return self.getItems(self.find("similar", params), pager=pager)

    def findTagged(self, type_: str, tags: list, pager: Pager = None):
        """
        Searches for objects tagged with one or more tags.
        @param type_: the type of object to search for. @see ParaObject::type
        @param tags: the list of tags
        @param pager: a Pager
        @return: a list of objects found
        """
        params = self.pagerToParams(pager)
        params["tags"] = tags if tags else None
        params["type"] = type_
        return self.getItems(self.find("tagged", params), pager=pager)

    def findTags(self, keyword, pager: Pager = None):
        """
        Searches for Tag objects. This method might be deprecated in the future.
        @param keyword: the tag keyword to search for
        @param pager: a Pager
        @return: a list of objects found
        """
        keyword = keyword + "*" if keyword else "*"
        return self.findWildcard("tag", "tag", keyword, pager)

    def findTermInList(self, type_: str, field: str, terms: list, pager: Pager = None):
        """
        Searches for objects having a property value that is in list of possible values.
        @param type_: the type of object to search for. @see ParaObject::type
        @param field: the property name of an object
        @param terms: a list of terms (property values)
        @param pager: a Pager
        @return: a list of objects found
        """
        params = self.pagerToParams(pager)
        params["field"] = field
        params["terms"] = terms
        params["type"] = type_
        return self.getItems(self.find("in", params), pager=pager)

    def findTerms(self, type_: str, terms=None, matchall: bool = True, pager: Pager = None):
        """
        Searches for objects that have properties matching some given values. A terms query.
        @param type_: the type of object to search for. @see ParaObject::type
        @param terms: a map of fields (property names) to terms (property values)
        @param matchall: match all terms. If true - AND search, if false - OR search
        @param pager: a Pager
        @return: a list of objects found
        """
        if not terms:
            return []
        params = self.pagerToParams(pager)
        params["matchall"] = str(matchall).lower()
        termz = [(key + self.SEPARATOR + value) for key, value in terms.items() if value]
        if termz:
            params["terms"] = termz
        params["type"] = type_
        return self.getItems(self.find("terms", params), pager=pager)

    def findWildcard(self, type_: str, field: str, wildcard: str = "*", pager: Pager = None):
        """
        Searches for objects that have a property with a value matching a wildcard query.
        @param type_: the type of object to search for. @see ParaObject::type
        @param field: the property name of an object
        @param wildcard: wildcard query string. For example "cat*".
        @param pager: a Pager
        @return: a list of objects found
        """
        params = self.pagerToParams(pager)
        params["field"] = field
        params["q"] = wildcard
        params["type"] = type_
        return self.getItems(self.find("wildcard", params), pager=pager)

    # noinspection PyDefaultArgument
    def getCount(self, type_: str, terms={}):
        """
        Counts indexed objects matching a set of terms/values.
        @param type_: the type of object to search for. @see ParaObject::type
        @param terms: a list of terms (property values)
        @return: the number of results found
        """
        if terms is None:
            return 0
        params = {}
        pager = Pager()
        if not terms:
            params["type"] = type_
            self.getItems(self.find("count", params), pager=pager)
            return pager.count
        else:
            termz = [(key + self.SEPARATOR + value) for key, value in terms.items() if value]
            params["terms"] = termz
        params["type"] = type_
        params["count"] = "true"
        self.getItems(self.find("terms", params), pager=pager)
        return pager.count

    def find(self, queryType=None, params=None):
        if params is None:
            params = {}
        if params:
            qtype = ("/" + queryType) if queryType else "/default"
            if "type" in params and params["type"]:
                return self.getEntity(self.invokeGet(params["type"] + "/search" + qtype, params))
            else:
                return self.getEntity(self.invokeGet("search" + qtype, params))
        else:
            return {"items": [], "totalHits": 0}

    # /////////////////////////////////////////////
    # //				 LINKS
    # /////////////////////////////////////////////

    def countLinks(self, obj: ParaObject, type2: str):
        """
        Count the total number of links between this object and another type of object.
        @param obj: the object to execute this method on
        @param type2: the other type of object
        @return: the number of links for the given object
        """
        if not obj or not obj.id or not type2:
            return 0
        pager = Pager()
        url = obj.getObjectURI() + "/links/" + self.urlenc(type2)
        self.getItems(self.getEntity(self.invokeGet(url, {"count": "true"})), pager=pager)
        return pager.count

    def getLinkedObjects(self, obj: ParaObject, type2: str, pager: Pager = None):
        """
        Returns all objects linked to the given one. Only applicable to many-to-many relationships.
        @param obj: the object to execute this method on
        @param type2: type of linked objects to search for
        @param pager: a Pager
        @return: a list of linked objects
        """
        if not obj or not obj.id or not type2:
            return []
        url = obj.getObjectURI() + "/links/" + self.urlenc(type2)
        return self.getItems(self.getEntity(self.invokeGet(url, self.pagerToParams(pager))), pager=pager)

    def findLinkedObjects(self, obj: ParaObject, type2: str, field: str = "name", query: str = "*",
                          pager: Pager = None):
        """
        Searches through all linked objects in many-to-many relationships.
        @param obj: the object to execute this method on
        @param type2: type of linked objects to search for
        @param field: the name of the field to target (within a nested field "nstd")
        @param query: a query string
        @param pager: a Pager
        @return: a list of linked objects
        """
        if not obj or not obj.id or not type2:
            return []
        params = self.pagerToParams(pager)
        params["field"] = field
        params["q"] = query
        url = obj.getObjectURI() + "/links/" + self.urlenc(type2)
        return self.getItems(self.getEntity(self.invokeGet(url, params)), pager=pager)

    def isLinked(self, obj: ParaObject, type2: str, id2: str):
        """
        Checks if this object is linked to another.
        @param obj: the object to execute this method on
        @param type2: type of linked objects to search for
        @param id2: the other id
        @return: true if the two are linked
        """
        if not obj or not obj.id or not type2 or not id2:
            return False
        url = obj.getObjectURI() + "/links/" + self.urlenc(type2) + "/" + self.urlenc(id2)
        res = self.getEntity(self.invokeGet(url))
        return True if res else False

    def isLinkedToObject(self, obj: ParaObject, toobj: ParaObject):
        """
        Checks if a given object is linked to this one.
        @param obj: the object to execute this method on
        @param toobj: the other object
        @return: true if linked
        """
        if not obj or not obj.id or not toobj or not toobj.id:
            return False
        return self.isLinked(obj, toobj.type, toobj.id)

    def link(self, obj: ParaObject, id2: str):
        """
        Links an object to this one in a many-to-many relationship.
        Only a link is created. Objects are left untouched.
        The type of the second object is automatically determined on read.
        @param obj: the object to execute this method on
        @param id2: link to the object with this id
        @return: the id of the Linker object that is created
        """
        if not obj or not obj.id or not id2:
            return
        url = obj.getObjectURI() + "/links/" + self.urlenc(id2)
        return self.getEntity(self.invokePost(url))

    def unlink(self, obj: ParaObject, type2: str, id2: str):
        """
        Unlinks an object from this one. Only a link is deleted. Objects are left untouched.
        @param obj: the object to execute this method on
        @param type2: the other type
        @param id2: the other id
        """
        if not obj or not obj.id or not type2 or not id2:
            return
        url = obj.getObjectURI() + "/links/" + self.urlenc(type2) + "/" + self.urlenc(id2)
        self.invokeDelete(url)

    def unlinkAll(self, obj: ParaObject):
        """
        Unlinks all objects that are linked to this one.
        Deletes all Linker objects. Only the links are deleted. Objects are left untouched.
        @param obj: the object to execute this method on
        """
        if not obj or not obj.id:
            return
        url = obj.getObjectURI() + "/links"
        self.invokeDelete(url)

    def countChildren(self, obj: ParaObject, type2: str):
        """
        Count the total number of child objects for this object.
        @param obj: the object to execute this method on
        @param type2: the type of the other object
        @return: the number of links
        """
        if not obj or not obj.id or not type2:
            return 0
        params = {"count": "true", "childrenonly": "true"}
        pager = Pager()
        url = obj.getObjectURI() + "/links/" + self.urlenc(type2)
        self.getItems(self.getEntity(self.invokeGet(url, params)), pager=pager)
        return pager.count

    def getChildren(self, obj: ParaObject, type2: str, field: str, term: str, pager: Pager = None):
        """
        Returns all child objects linked to this object.
        @param obj: the object to execute this method on
        @param type2: the type of children to look for
        @param field: the field name to use as filter
        @param term: the field value to use as filter
        @param pager: a Pager
        @return: a list of ParaObject in a one-to-many relationship with this object
        """
        if not obj or not obj.id or not type2:
            return []
        params = self.pagerToParams(pager)
        params["childrenonly"] = "true"
        if field:
            params["field"] = field
        if term:
            params["term"] = term
        url = obj.getObjectURI() + "/links/" + self.urlenc(type2)
        return self.getItems(self.getEntity(self.invokeGet(url, params)), pager=pager)

    def findChildren(self, obj: ParaObject, type2: str, query: str, pager: Pager = None):
        """
        Search through all child objects. Only searches child objects directly
        connected to this parent via the {@code parentid} field.
        @param obj: the object to execute this method on
        @param type2: the type of children to look for
        @param query: a query string
        @param pager: a Pager
        @return: a list of ParaObject in a one-to-many relationship with this object
        """
        if not obj or not obj.id or not type2:
            return []
        params = self.pagerToParams(pager)
        params["childrenonly"] = "true"
        params["q"] = query
        url = obj.getObjectURI() + "/links/" + self.urlenc(type2)
        return self.getItems(self.getEntity(self.invokeGet(url, params)), pager=pager)

    def deleteChildren(self, obj: ParaObject, type2: str):
        """
        Deletes all child objects permanently.
        @param obj: the object to execute this method on
        @param type2: the children's type.
        """
        params = {"childrenonly": "true"}
        url = obj.getObjectURI() + "/links/" + self.urlenc(type2)
        self.invokeDelete(url, params)

    # /////////////////////////////////////////////
    # //				 UTILS
    # /////////////////////////////////////////////

    def newId(self):
        """
        Generates a new unique id.
        @return: a new id
        """
        res = self.getEntity(self.invokeGet("utils/newid"))
        return res if res else ""

    def getTimestamp(self):
        """
        Returns the current timestamp.
        @return: a long number
        """
        res = self.getEntity(self.invokeGet("utils/timestamp"))
        return res if res else 0

    def formatDate(self, format_: str = "", loc: str = None):
        """
        Formats a date in a specific format.
        @param format_: the date format
        @param loc: the locale instance
        @return: a formatted date
        """
        return self.getEntity(self.invokeGet("utils/formatdate", {"format": format_, "locale": loc}))

    def noSpaces(self, string: str = "", replacement: str = ""):
        """
        Converts spaces to dashes.
        @param string: a string with spaces
        @param replacement: a string to replace spaces with
        @return: a string with dashes
        """
        return self.getEntity(self.invokeGet("utils/nospaces", {"string": string, "replacement": replacement}))

    def stripAndTrim(self, string: str = ""):
        """
        Strips all symbols, punctuation, whitespace and control chars from a string.
        @param string: a dirty string
        @return: a clean string
        """
        return self.getEntity(self.invokeGet("utils/nosymbols", {"string": string}))

    def markdownToHtml(self, markdown: str = ""):
        """
        Converts Markdown to HTML
        @param markdown: Markdown
        @return: HTML
        """
        return self.getEntity(self.invokeGet("utils/md2html", {"md": markdown}))

    def approximately(self, delta: int = 0):
        """
        Returns the number of minutes, hours, months elapsed for a time delta (milliseconds).
        @param delta: the time delta between two events, in milliseconds
        @return: a string like "5m", "1h"
        """
        return self.getEntity(self.invokeGet("utils/timeago", {"delta": str(delta)}))

    # /////////////////////////////////////////////
    # //				 MISC
    # /////////////////////////////////////////////

    def newKeys(self):
        """
        Generates a new set of access/secret keys. Old keys are discarded and invalid after this.
        @return: a map of new credentials
        """
        keys = self.getEntity(self.invokePost("_newkeys"))
        if keys and keys["secretKey"]:
            self.__secretKey = keys["secretKey"]
        return keys

    def types(self):
        """
        Returns all registered types for this App.
        @return: a map of plural-singular form of all the registered types.
        """
        return self.getEntity(self.invokeGet("_types"))

    def typesCount(self):
        """
        Returns the number of objects for each existing type in this App.
        @return: a map of singular object type to object count.
        """
        return self.getEntity(self.invokeGet("_types", {"count": "true"}))

    def me(self, jwt: str = None):
        """
        Returns a User or an App that is currently authenticated.
        @param jwt: a valid JWT access token (optional)
        @return: User or App
        """
        if not jwt:
            return self.getEntity(self.invokeGet("_me"), False)
        if not jwt.startswith("Bearer"):
            jwt = "Bearer " + jwt
        return self.getEntity(self.invokeSignedRequest("GET", endpointURL=self.getEndpoint(),
                                                       reqPath=self.getFullPath("_me"),
                                                       headers={"Authorization": jwt}), False)

    def voteUp(self, obj: ParaObject, voterid: str):
        """
        Upvote an object and register the vote in DB.
        @param obj: the object to receive +1 votes
        @param voterid: the userid of the voter
        @return: true if vote was successful
        """
        if not obj or not voterid:
            return False
        res = self.getEntity(self.invokePatch(obj.getObjectURI(), json.dumps({"_voteup": voterid})))
        return True if res else False

    def voteDown(self, obj: ParaObject, voterid: str):
        """
        Downvote an object and register the vote in DB.
        @param obj: the object to receive -1 votes
        @param voterid: the userid of the voter
        @return: true if vote was successful
        """
        if not obj or not voterid:
            return False
        res = self.getEntity(self.invokePatch(obj.getObjectURI(), json.dumps({"_votedown": voterid})))
        return True if res else False

    def rebuildIndex(self, destination: str = None):
        """
        Rebuilds the entire search index.
        @param destination: an existing index as destination
        @return: a response object with properties "tookMillis" and "reindexed"
        """
        if destination:
            return self.getEntity(self.invokeSignedRequest("POST", self.getEndpoint(), self.getFullPath("_reindex"),
                                                           params={"destinationIndex": destination}), True)
        else:
            return self.getEntity(self.invokePost("_reindex"))

    # /////////////////////////////////////////////
    # //	    Validation Constraints
    # /////////////////////////////////////////////

    def validationConstraints(self, type_: str = ""):
        """
        Returns the validation constraints map.
        @param type_: a type
        @return: a map containing all validation constraints.
        """
        return self.getEntity(self.invokeGet("_constraints/" + self.urlenc(type_)))

    def addValidationConstraint(self, type_: str, field: str, c: Constraint):
        """
        Add a new constraint for a given field.
        @param type_: a type
        @param field: a field name
        @param c: the constraint
        @return: a map containing all validation constraints for this type.
        """
        if not type_ or not field or not c:
            return {}
        url = "_constraints/" + self.urlenc(type_) + "/" + field + "/" + c.name
        return self.getEntity(self.invokePut(url, json.dumps(c.payload)))

    def removeValidationConstraint(self, type_: str, field: str, constraintname: str):
        """
        Removes a validation constraint for a given field.
        @param type_: a type
        @param field: a field name
        @param constraintname: the name of the constraint to remove
        @return: a map containing all validation constraints for this type.
        """
        if not type_ or not field or not constraintname:
            return {}
        return self.getEntity(self.invokeDelete("_constraints/" +
                                                self.urlenc(type_) + "/" + field + "/" + constraintname))

    # /////////////////////////////////////////////
    # //	    Resource Permissions
    # /////////////////////////////////////////////

    def resourcePermissions(self, subjectid: str = None):
        """
        Returns only the permissions for a given subject (user) of the current app.
        If subject is not given returns the permissions for all subjects and resources for current app.
        @param subjectid: the subject id (user id)
        @return: a map of subject ids to resource names to a list of allowed methods
        """
        if subjectid:
            return self.getEntity(self.invokeGet("_permissions/" + self.urlenc(subjectid)))
        else:
            return self.getEntity(self.invokeGet("_permissions"))

    def grantResourcePermission(self, subjectid: str, resourcepath: str, permission: list, allowguests: bool = False):
        """
        Grants a permission to a subject that allows them to call the specified HTTP methods on a given resource.
        @param subjectid: subject id (user id)
        @param resourcepath: resource path or object type
        @param permission: a set of HTTP methods - GET, POST, PUT, PATCH, DELETE
        @param allowguests: if true - all unauthenticated requests will go through, 'false' by default.
        @return: a map of the permissions for this subject id
        """
        if not subjectid or not resourcepath or not permission:
            return {}
        if allowguests and subjectid == "*":
            permission.append("?")
        url = "_permissions/" + self.urlenc(subjectid) + "/" + self.urlenc(resourcepath)
        return self.getEntity(self.invokePut(url, json.dumps(permission)))

    def revokeResourcePermission(self, subjectid: str, resourcepath: str):
        """
        Revokes a permission for a subject, meaning they no longer will be able to access the given resource.
        @param subjectid: subject id (user id)
        @param resourcepath: resource path or object type
        @return: a map of the permissions for this subject id
        """
        if not subjectid or not resourcepath:
            return {}
        return self.getEntity(self.invokeDelete(("_permissions/" +
                                                 self.urlenc(subjectid) + "/" + self.urlenc(resourcepath))))

    def revokeAllResourcePermissions(self, subjectid: str):
        """
        Revokes all permission for a subject.
        @param subjectid: ubject id (user id)
        @return: a map of the permissions for this subject id
        """
        if not subjectid:
            return {}
        return self.getEntity(self.invokeDelete("_permissions/" + self.urlenc(subjectid)))

    def isAllowedTo(self, subjectid: str, resourcepath: str, httpmethod: str):
        """
        Checks if a subject is allowed to call method X on resource Y.
        @param subjectid: subject id
        @param resourcepath: resource path or object type
        @param httpmethod: HTTP method name
        @return: true if allowed
        """
        if not subjectid or not resourcepath or not httpmethod:
            return False
        url = "_permissions/" + self.urlenc(subjectid) + "/" + self.urlenc(resourcepath) + "/" + httpmethod
        res = self.getEntity(self.invokeGet(url))
        return True if res else False

    # /////////////////////////////////////////////
    # //	           App Settings
    # /////////////////////////////////////////////

    def appSettings(self, key: str = None):
        """
        Returns the value of a specific app setting (property). If $key is blank all settings are returned.
        @param key: a key (optional)
        @return: a map of app settings
        """
        if key and not key.isspace():
            return self.getEntity(self.invokeGet("_settings/" + key))
        return self.getEntity(self.invokeGet("_settings"))

    def addAppSetting(self, key: str, value: object):
        """
        Adds or overwrites an app-specific setting.
        @param key: a key
        @param value: a value
        """
        if key and not key.isspace():
            self.invokePut("_settings/" + key, json.dumps({"value": value}))

    def setAppSettings(self, settings: dict):
        """
        Overwrites all app-specific settings.
        @param settings: a key-value map of properties
        """
        self.invokePut("_settings", json.dumps(settings))

    def removeAppSetting(self, key: str):
        """
        Removes an app-specific setting.
        @param key: a key
        """
        if key and not key.isspace():
            self.invokeDelete("_settings/" + key)

    # /////////////////////////////////////////////
    # //	           Access Tokens
    # /////////////////////////////////////////////

    def signIn(self, provider: str, providertoken: str, rememberjwt: bool = True):
        """
        Takes an identity provider access token and fetches the user data from that provider.
        A new User object is created if that user doesn't exist.
        Access tokens are returned upon successful authentication using one of the SDKs from
        Facebook, Google, Twitter, etc.
        <b>Note:</b> Twitter uses OAuth 1 and gives you a token and a token secret.
        <b>You must concatenate them like this: <code>{oauth_token}:{oauth_token_secret}</code> and
        use that as the provider access token.</b>
        @param provider: identity provider, e.g. 'facebook', 'google'...
        @param providertoken: access token from a provider like Facebook, Google, Twitter
        @param rememberjwt: it true the access token returned by Para will be stored locally and
        available through getAccessToken(). True by default.
        @return: a User object or None if something failed
        """
        if not provider or not providertoken:
            return None
        credentials = {"appid": self.__accessKey, "provider": provider, "token": providertoken}
        result = self.getEntity(self.invokePost(self.JWT_PATH, json.dumps(credentials)))
        if result and result["user"] and result["jwt"]:
            jwt_data = result["jwt"]
            if rememberjwt:
                self.__tokenKey = jwt_data["access_token"]
                self.__tokenKeyExpires = jwt_data["expires"]
                self.__tokenKeyNextRefresh = jwt_data["refresh"]
            obj = ParaObject()
            obj.setFields(result["user"])
            return obj
        else:
            self.clearAccessToken()
            return None

    def signOut(self):
        """
        Clears the JWT access token but token is not revoked.
        Tokens can be revoked globally per user with revokeAllTokens().
        """
        self.clearAccessToken()

    def refreshToken(self):
        """
        Refreshes the JWT access token. This requires a valid existing token. Call signIn() first.
        @return: true if token was refreshed
        """
        now = int(round(time.time() * 1000))
        notexpired = self.__tokenKeyExpires and self.__tokenKeyExpires > now
        canrefresh = self.__tokenKeyNextRefresh and \
                     (self.__tokenKeyNextRefresh < now or self.__tokenKeyNextRefresh > self.__tokenKeyExpires)
        # token present and NOT expired
        if self.__tokenKey and notexpired and canrefresh:
            result = self.getEntity(self.invokeGet(self.JWT_PATH))
            if result and result["user"] and result["jwt"]:
                jwt_data = result["jwt"]
                self.__tokenKey = jwt_data["access_token"]
                self.__tokenKeyExpires = jwt_data["expires"]
                self.__tokenKeyNextRefresh = jwt_data["refresh"]
                return True
            else:
                self.clearAccessToken()
        return False

    def revokeAllTokens(self):
        """
        Revokes all user tokens for a given user id.
        This would be equivalent to "logout everywhere".
        <b>Note:</b> Generating a new API secret on the server will also invalidate all client tokens.
        Requires a valid existing token.
        @return: true if successful
        """
        return self.getEntity(self.invokeDelete(self.JWT_PATH)) is not None
