import mock
import unittest
import tempfile
import time
import re
import os
from orvsd_central import models
from orvsd_central import util


class TestUtils(unittest.TestCase):

    def test_string_to_type(self):
        self.assertEqual(util.string_to_type("null"), None)
        self.assertEqual(util.string_to_type("true"), True)
        self.assertEqual(util.string_to_type("false"), False)
        self.assertEqual(util.string_to_type("3.141529"), 3.141529)
        self.assertEqual(util.string_to_type("1234567890"), 1234567890)
        self.assertEqual(util.string_to_type("asdfghjkl"), "asdfghjkl")
        self.assertEqual(util.string_to_type("192.168.1.255"), "192.168.1.255")

    def test_get_obj_by_category(self):
        expected = models.District
        category = util.get_obj_by_category('districts')
        self.assertEquals(category, expected)
        expected = models.School
        category = util.get_obj_by_category('schools')
        self.assertEquals(category, expected)
        expected = models.Course
        category = util.get_obj_by_category('courses')
        self.assertEquals(category, expected)
        expected = models.CourseDetail
        category = util.get_obj_by_category('coursedetails')
        self.assertEquals(category, expected)
        expected = models.User
        category = util.get_obj_by_category('users')
        self.assertEquals(category, expected)
        expected = models.SiteDetail
        category = util.get_obj_by_category('sitedetails')
        self.assertEquals(category, expected)

    def test_get_obj_identifier(self):
        expected = str
        identifier = 'districts'
        self.assertEquals(type(util.get_obj_identifier(identifier)), expected)
        identifier = 'sites'
        self.assertEquals(type(util.get_obj_identifier(identifier)), expected)
        identifier = 'courses'
        self.assertEquals(type(util.get_obj_identifier(identifier)), expected)
        identifier = 'users'
        self.assertEquals(type(util.get_obj_identifier(identifier)), expected)
        identifier = 'coursedetails'
        self.assertEquals(type(util.get_obj_identifier(identifier)), expected)
        identifier = 'sitedetails'
        self.assertEquals(type(util.get_obj_identifier(identifier)), expected)
        identifier = 'gibberish'
        self.assertIsNone(util.get_obj_identifier(identifier))

    def test_get_path_and_source(self):
        # There is a bug here, so test should fail. - Dean
        base_path = '/data/moodle/somepath'
        file_path = '/data/moodle/somepath/nroc/file.txt'
        result = ('nroc/', 'file.txt')
        self.assertTupleEqual(util.get_path_and_source(base_path, file_path), result)

    def build_test_directory_structure_repeated_subdirs(self):
        """Create a testing directory structure with
         repeated sub directories"""
        temp_root = tempfile.mkdtemp()
        os.makedirs(temp_root + '/foo/bar/baz')
        os.makedirs(temp_root + '/bar/foo')
        os.makedirs(temp_root + '/baz/')
        return temp_root

    def build_test_directory_structure(self):
        """Create a structure with no repeated sub
         directories"""
        temp_root = tempfile.mkdtemp()
        os.makedirs(temp_root + '/foo')
        os.makedirs(temp_root + '/bar')
        os.makedirs(temp_root + '/baz')
        return temp_root

    def test_get_course_folders_repeated_subdirs(self):
        # get_course_folders returns a dictionary
        # containing the names of sub folders 2 levels deep
        expected = ['None', 'baz', 'bar', 'foo']
        test_directory = self.build_test_directory_structure()
        self.assertEqual(util.get_course_folders(test_directory).sort(), expected.sort())

    def test_get_course_folders(self):
        # get_course_folders returns a dictionary
        # containing the names of sub folders 2 levels deep
        expected = ['None', 'baz', 'bar', 'foo']
        test_directory = self.build_test_directory_structure()
        self.assertEqual(util.get_course_folders(test_directory).sort(), expected.sort())
