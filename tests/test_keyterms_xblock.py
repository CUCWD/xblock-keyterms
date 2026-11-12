"""Tests for the Key Terms location editor."""
import json
from unittest.mock import patch
from types import SimpleNamespace

from django.test import SimpleTestCase
from webob import Request
from xblock.fields import ScopeIds
from xblock.test.toy_runtime import ToyRuntime

from keyterms_xblock import MyXBlock


class TestKeyTermsLocation(SimpleTestCase):
    def setUp(self):
        self.block = MyXBlock(ToyRuntime(), scope_ids=ScopeIds('user', 'type', 'definition', 'usage'))
        self.block.module_number = ''
        self.block.lesson_number = ''
        self.outline = [{'name': 'Module <One>', 'lessons': ['Lesson 1', 'Lesson 2']},
                        {'name': 'Module Two', 'lessons': ['Other lesson']}]
        self.outline_patch = patch.object(self.block, '_course_outline', return_value=self.outline)
        self.outline_patch.start()
        terms_patch = patch.object(self.block, '_location_terms', return_value=[])
        terms_patch.start()
        self.addCleanup(terms_patch.stop)
        self.addCleanup(self.outline_patch.stop)

    def submit(self, values):
        request = Request.blank('/')
        request.method = 'POST'
        request.body = json.dumps({'values': values, 'defaults': []}).encode('utf-8')
        return self.block.handle('submit_studio_edits', request)

    def test_studio_has_location_fields_and_native_actions(self):
        fragment = self.block.studio_view({})
        self.assertIn('module_number', fragment.content)
        self.assertIn('lesson_number', fragment.content)
        self.assertNotIn('data-field-name="display_name"', fragment.content)
        self.assertIn('save-button', fragment.content)
        self.assertIn('cancel-button', fragment.content)
        self.assertIn('All course terms', fragment.content)
        self.assertIn('All terms in this module', fragment.content)

    def test_selected_location_saves_and_displays_escaped_names(self):
        self.assertEqual(self.submit({'module_number': '1', 'lesson_number': '2'}).status_int, 200)
        content = self.block.student_view().content
        self.assertIn('Module &lt;One&gt;', content)
        self.assertIn('Lesson 2', content)
        self.assertEqual(self.block.display_name, 'Key Terms')

    def test_rejects_invalid_locations_and_keeps_previous_selection(self):
        self.assertEqual(self.submit({'module_number': '1', 'lesson_number': '2'}).status_int, 200)
        self.assertEqual(self.submit({'module_number': '2', 'lesson_number': '2'}).status_int, 400)
        self.assertEqual(self.block.module_number, '1')
        self.assertEqual(self.block.lesson_number, '2')
        self.assertEqual(self.submit({'module_number': '', 'lesson_number': '1'}).status_int, 400)

    def test_no_location_and_missing_outline(self):
        self.assertIn('No module or lesson selected', self.block.student_view().content)
        with patch.object(self.block, '_course_outline', side_effect=RuntimeError('unavailable')):
            self.assertIn('temporarily unavailable', self.block.student_view().content)

    def test_terms_render_as_escaped_names_and_definitions(self):
        self.block.module_number = '1'
        self.block.lesson_number = '2'
        terms = [SimpleNamespace(key_name='<Term>', definition='A & B')]
        with patch.object(self.block, '_location_terms', return_value=terms):
            content = self.block.student_view().content
        self.assertIn('<strong>&lt;Term&gt;</strong>: A &amp; B', content)

    def test_module_without_lesson_and_empty_terms(self):
        self.block.module_number = '1'
        content = self.block.student_view().content
        self.assertIn('No key terms found for this selection.', content)
        self.assertNotIn('<strong>Lesson:</strong>', content)

    def test_invalid_lesson_does_not_show_terms(self):
        self.block.module_number = '1'
        self.block.lesson_number = '9'
        with patch.object(self.block, '_location_terms') as lookup:
            self.assertIn('selected lesson is unavailable', self.block.student_view().content)
            lookup.assert_not_called()

    def test_all_course_terms_selection_displays_terms(self):
        self.assertEqual(self.submit({'module_number': 'all', 'lesson_number': ''}).status_int, 200)
        terms = [SimpleNamespace(key_name='Course term', definition='Meaning')]
        with patch.object(self.block, '_location_terms', return_value=terms):
            content = self.block.student_view().content
        self.assertIn('All course terms', content)
        self.assertIn('<strong>Course term</strong>: Meaning', content)
        self.assertEqual(self.submit({'module_number': 'all', 'lesson_number': '1'}).status_int, 400)

    def test_all_module_terms_remains_compatible_with_existing_selection(self):
        self.assertEqual(self.submit({'module_number': '1', 'lesson_number': ''}).status_int, 200)
        self.assertIn('Module &lt;One&gt;', self.block.student_view().content)

