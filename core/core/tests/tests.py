from django.test import TestCase, Client


class MainTest(TestCase):
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        pass

    def test_homepage(self):
        response = self.client.get("")
        self.assertContains(response, "FlowLeaf", status_code=200)
