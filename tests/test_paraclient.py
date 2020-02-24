import json
from datetime import date
from time import sleep
from unittest import TestCase

from paraclient.constraint import Constraint
from paraclient.pager import Pager
from paraclient.paraclient import ParaClient
from paraclient.paraobject import ParaObject


class ParaClientTests(TestCase):
    pc: ParaClient
    pc2: ParaClient
    catsType = "cat"
    dogsType = "dog"
    batsType = "bat"

    u: ParaObject
    u1: ParaObject
    u2: ParaObject
    t: ParaObject
    s1: ParaObject
    s2: ParaObject
    a1: ParaObject
    a2: ParaObject

    @classmethod
    def setUpClass(cls):
        cls.pc = ParaClient("app:test", "Yi/b6Bw6dCFWBqHiExNUwqqT/UoUf8NuWbwOcxe7ddKuqF9luUxagA==")
        cls.pc.setEndpoint("http://localhost:8080")
        cls.pc2 = ParaClient("app:test", "")
        cls.pc2.setEndpoint("http://localhost:8080")
        if not cls.pc.me():
            raise Exception("Local Para server must be started before testing.")

        cls.u = ParaObject("111")
        cls.u.name = "John Doe"
        cls.u.tags = ["one", "two", "three"]

        cls.u1 = ParaObject("222")
        cls.u1.name = "Joe Black"
        cls.u1.tags = ["two", "four", "three"]

        cls.u2 = ParaObject("333")
        cls.u2.name = "Ann Smith"
        cls.u2.tags = ["four", "five", "three"]

        cls.t = ParaObject("tag:test", "tag")
        cls.t["count"] = 3
        cls.t["tag"] = "test"

        cls.a1 = ParaObject("adr1", "address")
        cls.a1.name = "Place 1"
        cls.a1["address"] = "NYC"
        cls.a1["country"] = "US"
        cls.a1["latlng"] = "40.67,-73.94"
        cls.a1.parentid = cls.u.id
        cls.a1.creatorid = cls.u.id

        cls.a2 = ParaObject("adr2", "address")
        cls.a2.name = "Place 2"
        cls.a2["address"] = "NYC"
        cls.a2["country"] = "US"
        cls.a2["latlng"] = "40.69,-73.95"
        cls.a2.parentid = cls.t.id
        cls.a2.creatorid = cls.t.id

        cls.s1 = ParaObject("s1")
        cls.s1["text"] = "This is a little test sentence. Testing, one, two, three."

        cls.s2 = ParaObject("s2")
        cls.s2["text"] = "We are testing this thing. This sentence is a test. One, two."

        cls.pc.createAll([cls.u, cls.u1, cls.u2, cls.t, cls.s1, cls.s2, cls.a1, cls.a2])

    @classmethod
    def tearDownClass(cls):
        cls.pc.deleteAll([obj.id for obj in [cls.u, cls.u1, cls.u2, cls.t, cls.s1, cls.s2, cls.a1, cls.a2]])

    def testCRUD(self):
        self.assertIsNotNone(self.pc.create(ParaObject()))
        t1 = self.pc.create(ParaObject("test1", "tag"))
        t1["tag"] = "test1"
        self.assertIsNotNone(t1)

        self.assertIsNone(self.pc.read(None, None))
        self.assertIsNone(self.pc.read("", ""))

        tr_id = self.pc.read(id_=t1.id)
        self.assertIsNotNone(tr_id)
        self.assertIsNotNone(tr_id.timestamp)
        self.assertEqual(t1.tag, tr_id.tag)

        tr = self.pc.read(t1.type, t1.id)
        self.assertIsNotNone(tr)
        self.assertIsNotNone(tr.timestamp)
        self.assertEqual(t1["tag"], tr["tag"])

        tr["count"] = 15
        tu = self.pc.update(tr)
        self.assertIsNone(self.pc.update(ParaObject("None")))
        self.assertIsNotNone(tu)
        self.assertEqual(tu["count"], tr["count"])
        self.assertIsNotNone(tu.updated)

        s = ParaObject()
        s.type = self.dogsType
        s["foo"] = "bark!"
        s = self.pc.create(s)

        dog = self.pc.read(self.dogsType, s.id)
        self.assertIsNotNone(dog["foo"])
        self.assertEqual("bark!", dog["foo"])

        self.pc.delete(t1)
        self.pc.delete(dog)
        self.assertIsNone(self.pc.read(tr.type, tr.id))

    def testBatchCRUD(self):
        dogs = []
        for i in range(0, 3):
            s = ParaObject()
            s.type = self.dogsType
            s["foo"] = "bark!"
            dogs.append(s)

        self.assertIs(len(self.pc.createAll(None)), 0)
        l1 = self.pc.createAll(dogs)
        self.assertEqual(3, len(l1))
        self.assertIsNotNone(l1[0].id)

        self.assertIs(len(self.pc.readAll(None)), 0)
        nl = []
        self.assertIs(len(self.pc.readAll(nl)), 0)
        nl.append(l1[0].id)
        nl.append(l1[1].id)
        nl.append(l1[2].id)
        l2 = self.pc.readAll(nl)
        self.assertEqual(3, len(l2))
        self.assertEqual(l1[0].id, l2[0].id)
        self.assertEqual(l1[1].id, l2[1].id)
        self.assertIsNotNone(l2[0]["foo"])
        self.assertEqual("bark!", l2[0]["foo"])

        self.assertIs(len(self.pc.updateAll(None)), 0)

        part1 = ParaObject(l1[0].id)
        part2 = ParaObject(l1[1].id)
        part3 = ParaObject(l1[2].id)
        part1.type = self.dogsType
        part2.type = self.dogsType
        part3.type = self.dogsType

        part1["custom"] = "prop"
        part1.name = "NewName1"
        part2.name = "NewName2"
        part3.name = "NewName3"

        l3 = self.pc.updateAll([part1, part2, part3])

        self.assertIsNotNone(l3[0]["custom"])
        self.assertEqual(self.dogsType, l3[0].type)
        self.assertEqual(self.dogsType, l3[1].type)
        self.assertEqual(self.dogsType, l3[2].type)

        self.assertEqual(part1.name, l3[0].name)
        self.assertEqual(part2.name, l3[1].name)
        self.assertEqual(part3.name, l3[2].name)

        self.pc.deleteAll(nl)
        sleep(1)

        l4 = self.pc.list(self.dogsType)
        self.assertIs(len(l4), 0)

        self.assertIs(self.dogsType in self.pc.getApp()["datatypes"].values(), True)

    def testList(self):
        cats = []
        for i in range(0, 3):
            s = ParaObject(self.catsType + str(i))
            s.type = self.catsType
            cats.append(s)

        self.pc.createAll(cats)
        sleep(1)

        self.assertIs(len(self.pc.list(None)), 0)
        self.assertIs(len(self.pc.list("")), 0)

        list1 = self.pc.list(self.catsType)
        self.assertIsNot(len(list1), 0)
        self.assertEqual(3, len(list1))
        self.assertEqual(isinstance(list1[0], ParaObject), True)

        list2 = self.pc.list(self.catsType, Pager(limit=2))
        self.assertIsNot(len(list2), 0)
        self.assertEqual(2, len(list2))

        nl = [cats[0].id, cats[1].id, cats[2].id]
        self.pc.deleteAll(nl)

        self.assertIs(self.catsType in self.pc.getApp()["datatypes"].values(), True)

    def testSearch(self):
        self.assertIsNone(self.pc.findById(None))
        self.assertIsNone(self.pc.findById(""))
        self.assertIsNotNone(self.pc.findById(self.u.id))
        self.assertIsNotNone(self.pc.findById(self.t.id))

        self.assertIs(len(self.pc.findByIds(None)), 0)
        self.assertEqual(3, len(self.pc.findByIds([self.u.id, self.u1.id, self.u2.id])))

        self.assertIs(len(self.pc.findNearby(None, None, 100, 1, 1)), 0)
        l1 = self.pc.findNearby(self.u.type, "*", 10, 40.60, -73.90)
        self.assertIsNot(len(l1), 0)

        self.assertIs(len(self.pc.findNearby(None, None, 100, 1, 1)), 0)
        l1 = self.pc.findNearby(self.u.type, "*", 10, 40.60, -73.90)
        self.assertIsNot(len(l1), 0)

        self.assertIs(len(self.pc.findPrefix(None, None, "")), 0)
        self.assertIs(len(self.pc.findPrefix("", "None", "xx")), 0)
        self.assertIsNot(len(self.pc.findPrefix(self.u.type, "name", "Ann")), 0)

        self.assertIsNot(len(self.pc.findQuery(None, None)), 0)
        self.assertIsNot(len(self.pc.findQuery("", "*")), 0)
        self.assertEqual(2, len(self.pc.findQuery(self.a1.type, "country:US")))
        self.assertIsNot(len(self.pc.findQuery(self.u.type, "Ann*")), 0)
        self.assertIsNot(len(self.pc.findQuery(self.u.type, "Ann*")), 0)
        self.assertGreater(len(self.pc.findQuery(None, "*")), 4)

        p = Pager()
        self.assertEqual(0, p.count)
        res = self.pc.findQuery(self.u.type, "*", p)
        self.assertEqual(len(res), p.count)
        self.assertGreater(p.count, 0)

        self.assertIs(len(self.pc.findSimilar(self.t.type, "", None, None)), 0)
        self.assertIs(len(self.pc.findSimilar(self.t.type, "", [], "")), 0)
        res = self.pc.findSimilar(self.s1.type, self.s1.id, ["properties.text"], self.s1["text"])
        self.assertIsNot(len(res), 0)
        self.assertEqual(self.s2.id, res[0].id)

        i0 = len(self.pc.findTagged(self.u.type, None))
        i1 = len(self.pc.findTagged(self.u.type, ["two"]))
        i2 = len(self.pc.findTagged(self.u.type, ["one", "two"]))
        i3 = len(self.pc.findTagged(self.u.type, ["three"]))
        i4 = len(self.pc.findTagged(self.u.type, ["four", "three"]))
        i5 = len(self.pc.findTagged(self.u.type, ["five", "three"]))
        i6 = len(self.pc.findTagged(self.t.type, ["four", "three"]))

        self.assertEqual(0, i0)
        self.assertEqual(2, i1)
        self.assertEqual(1, i2)
        self.assertEqual(3, i3)
        self.assertEqual(2, i4)
        self.assertEqual(1, i5)
        self.assertEqual(0, i6)

        self.assertIsNot(len(self.pc.findTags(None)), 0)
        self.assertIsNot(len(self.pc.findTags("")), 0)
        self.assertIs(len(self.pc.findTags("unknown")), 0)
        self.assertGreaterEqual(len(self.pc.findTags(self.t["tag"])), 1)

        self.assertEqual(3, len(self.pc.findTermInList(self.u.type, "id", [self.u.id, self.u1.id, self.u2.id, "xxx", "yyy"])))

        # many terms
        terms = {"id": self.u.id}
        # terms.put("type", u.type)

        terms1 = {"type": None, "id": " "}

        terms2 = {" ": "bad", "": ""}

        self.assertEqual(1, len(self.pc.findTerms(self.u.type, terms, True)))
        self.assertIs(len(self.pc.findTerms(self.u.type, terms1, True)), 0)
        self.assertIs(len(self.pc.findTerms(self.u.type, terms2, True)), 0)

        # single term
        self.assertIs(len(self.pc.findTerms(None, None, True)), 0)
        self.assertIs(len(self.pc.findTerms(self.u.type, {"": None}, True)), 0)
        self.assertIs(len(self.pc.findTerms(self.u.type, {"": ""}, True)), 0)
        self.assertIs(len(self.pc.findTerms(self.u.type, {"term": None}, True)), 0)
        self.assertGreaterEqual(len(self.pc.findTerms(self.u.type, {"type": self.u.type}, True)), 2)

        self.assertIs(len(self.pc.findWildcard(self.u.type, None, None)), 0)
        self.assertIs(len(self.pc.findWildcard(self.u.type, "", "")), 0)
        self.assertIsNot(len(self.pc.findWildcard(self.u.type, "name", "An*")), 0)

        self.assertGreater(self.pc.getCount(None), 4)
        self.assertNotEqual(0, self.pc.getCount(""))
        self.assertEqual(0, self.pc.getCount("test"))
        self.assertGreaterEqual(self.pc.getCount(self.u.type), 3)

        self.assertEqual(0, self.pc.getCount(None, None))
        self.assertEqual(0, self.pc.getCount(self.u.type, {"id": " "}))
        self.assertEqual(1, self.pc.getCount(self.u.type, {"id": self.u.id}))
        self.assertGreater(self.pc.getCount(None, {"type": self.u.type}), 1)

    def testLinks(self):
        self.assertIsNotNone(self.pc.link(self.u, self.t.id))
        self.assertIsNotNone(self.pc.link(self.u, self.u2.id))

        self.assertIs(self.pc.isLinkedToObject(self.u, None), False)
        self.assertIs(self.pc.isLinkedToObject(self.u, self.t), True)
        self.assertIs(self.pc.isLinkedToObject(self.u, self.u2), True)

        sleep(1)

        self.assertEqual(1, len(self.pc.getLinkedObjects(self.u, "tag")))
        self.assertEqual(1, len(self.pc.getLinkedObjects(self.u, "sysprop")))

        self.assertEqual(0, self.pc.countLinks(self.u, None))
        self.assertEqual(1, self.pc.countLinks(self.u, "tag"))
        self.assertEqual(1, self.pc.countLinks(self.u, "sysprop"))

        self.pc.unlinkAll(self.u)

        self.assertIsNot(self.pc.isLinkedToObject(self.u, self.t), True)
        self.assertIsNot(self.pc.isLinkedToObject(self.u, self.u2), True)

    def testUtils(self):
        id1 = self.pc.newId()
        id2 = self.pc.newId()
        self.assertIsNotNone(id1)
        self.assertNotEqual(id1, "")
        self.assertNotEqual(id1, id2)

        ts = self.pc.getTimestamp()
        self.assertIsNotNone(ts)
        self.assertNotEqual(0, ts)

        date1 = self.pc.formatDate("MM dd yyyy", "US")
        date2 = date.today().strftime("%m %d %Y")
        self.assertEqual(date1, date2)

        ns1 = self.pc.noSpaces(" test  123		test ", "")
        self.assertEqual(ns1, "test123test")

        st1 = self.pc.stripAndTrim(" %^&*( cool )		@!")
        self.assertEqual(st1, "cool")

        md1 = self.pc.markdownToHtml("# hello **test**")
        self.assertEqual(md1, "<h1>hello <strong>test</strong></h1>\n")

        ht1 = self.pc.approximately(15000)
        self.assertEqual(ht1, "15s")

    def testMisc(self):
        types = self.pc.types()
        self.assertIsNotNone(types)
        self.assertIsNot(len(types), 0)
        self.assertIs(ParaObject(None, "user").type in types.values(), True)

        self.assertEqual("app:test", self.pc.me().id)

    def testValidationConstraints(self):
        # Validations string
        kittenType = "kitten"
        constraints = self.pc.validationConstraints()
        self.assertIsNot(len(constraints), 0)
        self.assertIs("app" in constraints.keys(), True)
        self.assertIs("user" in constraints.keys(), True)

        constraint = self.pc.validationConstraints("app")

        self.assertIsNot(len(constraint), 0)
        self.assertIs("app" in constraint.keys(), True)
        self.assertEqual(1, len(constraint))

        self.pc.addValidationConstraint(kittenType, "paws", Constraint.required())
        constraint = self.pc.validationConstraints(kittenType)
        self.assertIs("paws" in constraint[kittenType].keys(), True)

        ct = ParaObject("felix")
        ct.type = kittenType

        # validation fails
        ct2 = self.pc.create(ct)

        self.assertIsNone(ct2)
        ct["paws"] = "4"
        self.assertIsNotNone(self.pc.create(ct))

        self.pc.removeValidationConstraint(kittenType, "paws", "required")
        constraint = self.pc.validationConstraints(kittenType)
        self.assertIs(kittenType in constraint.keys(), False)

        # votes
        self.assertIs(self.pc.voteUp(ct, self.u.id), True)
        self.assertIsNot(self.pc.voteUp(ct, self.u.id), True)
        self.assertIs(self.pc.voteDown(ct, self.u.id), True)
        self.assertIs(self.pc.voteDown(ct, self.u.id), True)
        self.assertIsNot(self.pc.voteDown(ct, self.u.id), True)
        self.pc.delete(ct)
        self.pc.delete(ParaObject("vote:" + self.u.id + ":" + ct.id, "vote"))

        self.assertIs(self.pc.getServerVersion().startswith("1"), True)
        self.assertNotEqual("unknown", self.pc.getServerVersion())

    def testResourcePermissions(self):
        # Permissions
        permits = self.pc.resourcePermissions()
        self.assertIsNotNone(permits)

        self.assertIs(len(self.pc.grantResourcePermission(None, self.dogsType, [])), 0)
        self.assertIs(len(self.pc.grantResourcePermission(" ", "", [])), 0)

        self.pc.grantResourcePermission(self.u1.id, self.dogsType, ["GET"])
        permits = self.pc.resourcePermissions(self.u1.id)
        self.assertIs(self.u1.id in permits.keys(), True)
        self.assertIs(self.dogsType in permits[self.u1.id].keys(), True)
        self.assertIs(self.pc.isAllowedTo(self.u1.id, self.dogsType, "GET"), True)
        self.assertIsNot(self.pc.isAllowedTo(self.u1.id, self.dogsType, "POST"), True)
        # anonymous permissions
        self.assertIsNot(self.pc.isAllowedTo("*", "utils/timestamp", "GET"), True)
        self.assertIsNotNone(self.pc.grantResourcePermission("*", "utils/timestamp", ["GET"], True))
        self.assertGreater(self.pc2.getTimestamp(), 0)
        self.assertIsNot(self.pc.isAllowedTo("*", "utils/timestamp", "DELETE"), True)

        permits = self.pc.resourcePermissions()
        self.assertIs(self.u1.id in permits.keys(), True)
        self.assertIs(self.dogsType in permits[self.u1.id].keys(), True)

        self.pc.revokeResourcePermission(self.u1.id, self.dogsType)
        permits = self.pc.resourcePermissions(self.u1.id)
        self.assertIsNot(self.dogsType in permits[self.u1.id].keys(), True)
        self.assertIsNot(self.pc.isAllowedTo(self.u1.id, self.dogsType, "GET"), True)
        self.assertIsNot(self.pc.isAllowedTo(self.u1.id, self.dogsType, "POST"), True)

        self.pc.grantResourcePermission(self.u2.id, "*", ["POST", "PUT", "PATCH", "DELETE"])
        self.assertIs(self.pc.isAllowedTo(self.u2.id, self.dogsType, "PUT"), True)
        self.assertIs(self.pc.isAllowedTo(self.u2.id, self.dogsType, "PATCH"), True)

        self.pc.revokeAllResourcePermissions(self.u2.id)
        permits = self.pc.resourcePermissions()
        self.assertIsNot(self.pc.isAllowedTo(self.u2.id, self.dogsType, "PUT"), True)
        self.assertIs(self.u2.id in permits.keys(), False)
        # self.assertIs(permits[u2.id].Count, 0)

        self.pc.grantResourcePermission(self.u1.id, self.dogsType, ["POST", "PUT", "PATCH", "DELETE"])
        self.pc.grantResourcePermission("*", "*", ["GET"])
        self.pc.grantResourcePermission("*", self.catsType, ["POST", "PUT", "PATCH", "DELETE"])
        # user - specific permissions are in effect
        self.assertIs(self.pc.isAllowedTo(self.u1.id, self.dogsType, "PUT"), True)
        self.assertIsNot(self.pc.isAllowedTo(self.u1.id, self.dogsType, "GET"), True)
        self.assertIs(self.pc.isAllowedTo(self.u1.id, self.catsType, "PUT"), True)
        self.assertIs(self.pc.isAllowedTo(self.u1.id, self.catsType, "GET"), True)

        self.pc.revokeAllResourcePermissions(self.u1.id)
        # user - specific permissions not found so check wildcard
        self.assertIsNot(self.pc.isAllowedTo(self.u1.id, self.dogsType, "PUT"), True)
        self.assertIs(self.pc.isAllowedTo(self.u1.id, self.dogsType, "GET"), True)
        self.assertIs(self.pc.isAllowedTo(self.u1.id, self.catsType, "PUT"), True)
        self.assertIs(self.pc.isAllowedTo(self.u1.id, self.catsType, "GET"), True)

        self.pc.revokeResourcePermission("*", self.catsType)
        # resource - specific permissions not found so check wildcard
        self.assertIsNot(self.pc.isAllowedTo(self.u1.id, self.dogsType, "PUT"), True)
        self.assertIsNot(self.pc.isAllowedTo(self.u1.id, self.catsType, "PUT"), True)
        self.assertIs(self.pc.isAllowedTo(self.u1.id, self.dogsType, "GET"), True)
        self.assertIs(self.pc.isAllowedTo(self.u1.id, self.catsType, "GET"), True)
        self.assertIs(self.pc.isAllowedTo(self.u2.id, self.dogsType, "GET"), True)
        self.assertIs(self.pc.isAllowedTo(self.u2.id, self.catsType, "GET"), True)

        self.pc.revokeAllResourcePermissions("*")
        self.pc.revokeAllResourcePermissions(self.u1.id)

    def testAppSettings(self):
        settings = self.pc.appSettings()
        self.assertIsNotNone(settings)
        self.assertEqual(len(settings), 0)

        self.pc.addAppSetting("", None)
        self.pc.addAppSetting(" ", " ")
        self.pc.addAppSetting(None, " ")
        self.pc.addAppSetting("prop1", 1)
        self.pc.addAppSetting("prop2", True)
        self.pc.addAppSetting("prop3", "string")

        self.assertEqual(len(self.pc.appSettings()), 3)
        self.assertEqual(len(self.pc.appSettings()), len(self.pc.appSettings(None)))
        self.assertEqual(self.pc.appSettings("prop1")["value"], 1)
        self.assertIs(self.pc.appSettings("prop2")["value"], True)
        self.assertEqual(self.pc.appSettings("prop3")["value"], "string")

        self.pc.removeAppSetting("prop3")
        self.pc.removeAppSetting(" ")
        self.pc.removeAppSetting(None)
        self.assertIsNone(self.pc.appSettings("prop3")["value"])
        self.assertIs(len(self.pc.appSettings()), 2)
        self.pc.setAppSettings({})

    def testGetTimestamp(self):
        ts = self.pc.getTimestamp()
        self.assertIsNotNone(ts)
        self.assertIsNot(0, ts)
