import json
from unittest import TestCase
from paraclient.paraobject import ParaObject


class ParaObjectTests(TestCase):

    def testSetFields(self):
        o1 = ParaObject("123", "dog")
        o1.one = 1
        o1.two = "two"

        assert o1.type == "dog"
        assert o1.id == "123"

        obj = json.loads(o1.jsonSerialize())
        obj1 = ParaObject()
        obj1.setFields(obj)

        assert obj1.type == "dog"
        assert obj1.id == "123"
        assert obj1.two == "two"

    def testGetObjectURI(self):
        o1 = ParaObject()
        self.assertEqual(o1.getObjectURI(), "/sysprop")
        o1.type = "dog"
        self.assertEqual(o1.getObjectURI(), "/dog")
        o1.id = "123"
        self.assertEqual(o1.getObjectURI(), "/dog/123")

        o2 = ParaObject(id_="123 56", type_="dog 2")
        self.assertEqual(o2.getObjectURI(), "/dog%202/123%2056")
