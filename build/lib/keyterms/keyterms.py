"""This Xblock creates a module that makes it easy to manage what keywords are displayed to the user."""

from typing import List
import pkg_resources
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import String, Scope, List
from django.conf import settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
import json
import bleach

class KeytermsXBlock(XBlock):
    """
    This Xblock creates a module that makes it easy to manage what keywords are displayed to the user.
    """

    includedkeyterms = List(
        default=[], scope=Scope.content,
        help="A set to hold all keyterms that are selected to be displayed.",
    )

    keytermhtml = String(
        default="", scope=Scope.content,
        help="A string to hold the html code to display the keyterms.",
    )

    lessonsummary = String(
        default="", scope=Scope.content,
        help="A string to hold the html code to display the lesson summary.",
    )

    display_name = String(
        display_name="Display Name",
        help="This name appears in the horizontal navigation at the top of the page.",
        scope=Scope.settings,
        default="Key Terms"
    )

    # Tags to allow in HTML, attempting to prevent XSS
    allowedtags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 
    'ul', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'u', 'table', 'tbody', 'td', 'tr', 'th', 'img', 'em', 'br']

    root_url = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)

    root_url = "localhost"

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    # Different views
    def student_view(self, context=None):
        """
        The primary view of the KeytermsXBlock, shown to students
        when viewing courses.
        """
        html = self.resource_string("static/html/keyterms.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/keyterms.css"))
        frag.add_css(self.resource_string("static/css/popover.css"))
        frag.add_css(self.resource_string("static/css/textbox.css"))
        frag.add_css(self.resource_string("static/css/multiselect.css"))
        frag.add_javascript(self.resource_string("static/js/src/keyterms.js"))
        frag.initialize_js('KeytermsXBlock')
        return frag

    def studio_view(self, context=None):
        html = self.resource_string("static/html/keytermsstudio.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/keyterms.css"))
        frag.add_css(self.resource_string("static/css/popover.css"))
        frag.add_css(self.resource_string("static/css/multiselect.css"))
        frag.add_javascript(self.resource_string("static/js/src/keyterms.js"))
        frag.initialize_js('KeytermsXBlock')
        return frag

    @XBlock.json_handler
    def edit_lesson(self, data, suffix=''):
        """
        This handler is used to edit the lesson summary that is displayed to the user.
        """
        self.lessonsummary = bleach.clean(data['lessonsummary'], tags=self.allowedtags)
        return {"lessonsummary": self.lessonsummary}

    @XBlock.json_handler
    def get_included_keyterms(self, data, suffix=''):
        """
        This handler returns all keyterms that are being listed to the user.
        """
        return {"includedkeyterms": self.includedkeyterms}

    @XBlock.json_handler
    def add_keyterm(self, data, suffix=''):
        """
        This handler adds a keyterm to the list of included keyterms.
        """
        self.includedkeyterms.append(data['keyterm'])
        self.update_keyterm_html(self.includedkeyterms, data['course_id'])
        return {"keytermhtml": self.keytermhtml}

    @XBlock.json_handler
    def remove_keyterm(self, data, suffix=''):
        """
        This handler removes a keyterm from the list of included keyterms.
        """
        self.includedkeyterms.remove(data['keyterm'])
        self.update_keyterm_html(self.includedkeyterms, data['course_id'])
        return {"keytermhtml": self.keytermhtml}

    def update_keyterm_html(self, list, course_id):
        """
        This handler updates the html to be displayed to the user.
        """
        self.keytermhtml = ""
        for keyterm in list:
            # listItem = '<li class="list-group-item"><a class="keytermli" target="_blank" rel="noopener noreferrer" id="{keyterm}" href="http://{glossaryurl}:2000/course/course-v1:{courseid}/glossary?scrollTo={keyterm}">{keyterm}</a></li>\n'
            listItem = '<li class="keytermli list-group-item">{keyterm}</li>\n'
            listItem = listItem.format(keyterm = keyterm, glossaryurl = self.root_url, courseid=course_id)
            self.keytermhtml += bleach.clean(listItem, tags=self.allowedtags)
