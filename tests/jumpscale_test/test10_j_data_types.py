from .testcases_base import TestcasesBase
from parameterized import parameterized


class TestJDataTypes(TestcasesBase):

    def test001_test_uuid4(self):
        """ JS-001

        **Test Scenario:**
        create 100 random uuids.  test them
        """
        y = self.j.data.types.guid
        for i in range(100):
            u = self.j.data.idgenerator.generateGUID()
            self.assertTrue(y.check(u))

        # https://gist.github.com/ShawnMilo/7777304)
        self.assertFalse(y.check('89eb35868a8247a4c911758a62601cf7'))
        self.assertTrue (y.check('89eb35868a8247a4a911758a62601cf7'))
