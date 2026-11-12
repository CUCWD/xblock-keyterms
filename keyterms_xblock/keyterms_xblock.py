"""TO-DO: Write a description of what this XBlock is."""

import json
import logging
import os
from importlib import resources

from django.utils import translation
from django.utils.html import escape
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Integer, Scope, String
from xblock.utils.resources import ResourceLoader
from xblock.utils.studio_editable import StudioEditableXBlockMixin

LOG = logging.getLogger(__name__)
resource_loader = ResourceLoader(__name__)


class MyXBlock(StudioEditableXBlockMixin, XBlock):
    """
    TO-DO: document what your XBlock does.
    """

    display_name = String(
        display_name="Display Name",
        default="Key Terms",
        help="The name shown for this component in Studio.",
        scope=Scope.settings,
    )
    module_number = String(
        display_name="Module", default="", scope=Scope.settings,
        values_provider=lambda self: self._module_options(), resettable_editor=False,
    )
    lesson_number = String(
        display_name="Lesson", default="", scope=Scope.settings,
        values_provider=lambda self: self._lesson_options(), resettable_editor=False,
    )
    editable_fields = ("module_number", "lesson_number")

    def _course_outline(self):
        """Return the ordered course modules and lessons."""
        from xmodule.modulestore.django import modulestore  # pylint: disable=import-outside-toplevel

        store = modulestore()
        course = store.get_course(self.scope_ids.usage_id.course_key)
        if course is None:
            raise ValueError("Course outline is unavailable.")
        modules = []
        for chapter_key in course.children:
            chapter = store.get_item(chapter_key)
            if chapter.category != 'chapter':
                continue
            lessons = []
            for sequential_key in chapter.children:
                sequential = store.get_item(sequential_key)
                if sequential.category == 'sequential':
                    lessons.append(sequential.display_name or '')
            modules.append({'name': chapter.display_name or '', 'lessons': lessons})
        return modules

    def _module_options(self):
        return [{'display_name': 'Select a module', 'value': ''},
                {'display_name': 'All course terms', 'value': 'all'}] + [
            {'display_name': module['name'], 'value': str(index)}
            for index, module in enumerate(self._course_outline(), 1)
        ]

    def _lesson_options(self):
        outline = self._course_outline()
        index = int(self.module_number) - 1 if self.module_number.isdigit() else -1
        lessons = outline[index]['lessons'] if 0 <= index < len(outline) else []
        return [{'display_name': 'All terms in this module', 'value': ''}] + [
            {'display_name': name, 'value': str(number)} for number, name in enumerate(lessons, 1)
        ]

    def studio_view(self, context):
        """Extend the native Studio editor with dependent lesson options."""
        fragment = super().studio_view(context)
        outline = escape(json.dumps(self._course_outline()))
        fragment.add_content('<div class="keyterms-outline" data-outline="{}"></div>'.format(outline))
        fragment.add_javascript(self.resource_string('js/src/studio_location.js'))
        fragment.initialize_js('KeyTermsLocationEditor')
        return fragment

    def clean_studio_edits(self, values):
        """Reject positions outside the current course outline."""
        module = values.get('module_number', self.module_number)
        lesson = values.get('lesson_number', self.lesson_number)
        outline = self._course_outline()
        if not isinstance(module, str) or not isinstance(lesson, str):
            raise JsonHandlerError(400, 'Select a valid module and lesson.')
        if not module and not lesson:
            return
        if module == 'all' and not lesson:
            return
        if not module.isdigit() or not 1 <= int(module) <= len(outline):
            raise JsonHandlerError(400, 'Select a valid module.')
        lessons = outline[int(module) - 1]['lessons']
        if lesson and (not lesson.isdigit() or not 1 <= int(lesson) <= len(lessons)):
            raise JsonHandlerError(400, 'Select a valid lesson.')


    # Fields are defined on the class.  You can access them in your code as
    # self.<fieldname>.

    # TO-DO: delete count, and define your own fields.
    count = Integer(
        default=0, scope=Scope.user_state,
        help="A simple counter, to show something happening",
    )

    def resource_string(self, path):
        """
        Retrieve string contents for the file path
        """
        path = os.path.join('static', path)
        return resource_loader.load_unicode(path)

    def _location_terms(self, module=None, lesson=None):
        """Return distinct terms for this course and selected location."""
        from openedx_keyterms_ext.models import Term  # pylint: disable=import-outside-toplevel

        course_number = self.scope_ids.usage_id.course_key.course
        module = self.module_number if module is None else module
        lesson = self.lesson_number if lesson is None else lesson
        filters = {'course_number': course_number}
        if module != 'all':
            filters.update({
                'course_lessons__course_number': course_number,
                'course_lessons__module_number': int(module),
            })
            if lesson:
                filters['course_lessons__lesson_number'] = int(lesson)
        return Term.objects.filter(**filters).distinct().order_by('key_name', 'id')

    # TO-DO: change this view to display your data your own way.
    def student_view(self, context=None):
        """
        Create primary view of the MyXBlock, shown to students when viewing courses.
        """
        del context
        try:
            outline = self._course_outline()
            module_index = int(self.module_number) - 1 if self.module_number.isdigit() else -1
            module = outline[module_index] if 0 <= module_index < len(outline) else None
            lesson_index = int(self.lesson_number) - 1 if self.lesson_number.isdigit() else -1
            lesson = module['lessons'][lesson_index] if module and 0 <= lesson_index < len(module['lessons']) else None
            if self.module_number == 'all' and not self.lesson_number:
                content = '<p><strong>Module:</strong> All course terms</p>'
                show_terms = True
            elif module:
                content = '<p><strong>Module:</strong> {}</p>'.format(escape(module['name']))
                if lesson is not None:
                    content += '<p><strong>Lesson:</strong> {}</p>'.format(escape(lesson))
                show_terms = not self.lesson_number or lesson is not None
                if not show_terms:
                    content += '<p>The selected lesson is unavailable.</p>'
            else:
                content = '<p>No module or lesson selected.</p>'
                show_terms = False
            if show_terms:
                terms = self._location_terms()
                items = ''.join('<p><strong>{}</strong>: {}</p>'.format(
                    escape(term.key_name), escape(term.definition)) for term in terms)
                content += items or '<p>No key terms found for this selection.</p>'
        except Exception:  # Keep course content available if the outline or terms cannot be read.
            LOG.exception('Unable to load key terms for %s', self.scope_ids.usage_id)
            content = '<p>Module, lesson, and key term information is temporarily unavailable.</p>'
        return Fragment('<div class="keyterms_xblock_block">{}</div>'.format(content))

    # TO-DO: change this handler to perform your own actions.  You may need more
    # than one handler, or you may not need any handlers at all.
    @XBlock.json_handler
    def increment_count(self, data, suffix=''):
        """
        Increments data. An example handler.
        """
        if suffix:
            pass  # TO-DO: Use the suffix when storing data.
        # Just to show data coming in...
        assert data['hello'] == 'world'

        self.count += 1
        return {"count": self.count}

    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """Create canned scenario for display in the workbench."""
        return [
            ("MyXBlock",
             """<keyterms_xblock/>
             """),
            ("Multiple MyXBlock",
             """<vertical_demo>
                <keyterms_xblock/>
                <keyterms_xblock/>
                <keyterms_xblock/>
                </vertical_demo>
             """),
        ]

    @staticmethod
    def _get_statici18n_js_url():
        """
        Return the Javascript translation file for the currently selected language, if any.

        Defaults to English if available.
        """
        locale_code = translation.get_language()
        if locale_code is None:
            return None
        text_js = 'static/js/translations/{locale_code}/text.js'
        lang_code = locale_code.split('-')[0]
        for code in (locale_code, lang_code, 'en'):
            text_js_path = text_js.format(locale_code=code)
            if resources.files(__package__).joinpath(text_js_path).is_file():
                return text_js_path
        return None

    @staticmethod
    def get_dummy():
        """
        Generate initial i18n with dummy method.
        """
        return translation.gettext_noop('Dummy')
