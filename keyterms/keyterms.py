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
import pydash

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
    allowed_tags = [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'button', 'code', 'div', 'em',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'i', 'img', 'li', 'ol', 'p', 'strong',
        'table', 'tbody', 'td', 'th', 'tr',
        'u', 'ul'
    ]

    allowed_attributes = [
        'aria-controls', 'aria-expanded', 'aria-labelledby', 'class',
        'data-parent', 'data-target', 'data-toggle', 'id', 'type'
    ]

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
        frag.add_css(self.resource_string("static/css/popover.css"))
        frag.add_css(self.resource_string("static/css/textbox.css"))
        frag.add_css(self.resource_string("static/css/multiselect.css"))
        frag.add_css(self.resource_string("static/css/collapse.css"))
        frag.add_css(self.resource_string("static/css/keyterms.css"))
        frag.add_javascript(self.resource_string("static/js/src/keyterms.js"))
        frag.initialize_js(
            'KeytermsXBlock', {
                'cmsBaseURL': settings.CMS_BASE,
                'keyTermsAPIRootURL': settings.KEY_TERMS_API_ROOT_URL,
                'learningMicrofrontendURL': settings.LEARNING_MICROFRONTEND_URL
            }
        )

        return frag

    def studio_view(self, context=None):
        """
        The primary view of the KeytermsXBlock, shown to staff course
        developers when viewing the courses.
        """
        html = self.resource_string("static/html/keytermsstudio.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/popover.css"))
        frag.add_css(self.resource_string("static/css/textbox.css"))
        frag.add_css(self.resource_string("static/css/multiselect.css"))
        frag.add_css(self.resource_string("static/css/collapse.css"))
        frag.add_css(self.resource_string("static/css/keyterms.css"))
        frag.add_javascript(self.resource_string("static/js/src/keyterms.js"))
        frag.initialize_js(
            'KeytermsXBlock', {
                'cmsBaseURL': settings.CMS_BASE,
                'keyTermsAPIRootURL': settings.KEY_TERMS_API_ROOT_URL,
                'learningMicrofrontendURL': settings.LEARNING_MICROFRONTEND_URL
            }
        )

        return frag

    @XBlock.json_handler
    def edit_lesson(self, data, suffix=''):
        """
        This handler is used to edit the lesson summary that is displayed to the user.
        """
        self.lessonsummary = bleach.clean(data['lessonsummary'], tags=self.allowed_tags)
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
        # make sure keyterms are in alphabetical order
        list.sort()

        self.keytermhtml = ""
        for keyterm in list:
            div_parent_id = "#allKeytermsList"
            keyterm_card_header_id = pydash.camel_case("heading" + keyterm)
            keyterm_data_target = pydash.camel_case("collapse" + keyterm)
            keyterm_data_target_hashed = f'#{keyterm_data_target}'
            keyterm_show = ("show" if list[0] == keyterm else "")
            cardItem = '<div class="card">\n'
            cardItem += '   <div class="card-header" id="{keyterm_card_header_id}">\n'
            cardItem += '      <h5 class="mb-0">\n'
            cardItem += '         <button class="collapse-btn collapse-btn-link" data-toggle="collapse" data-target="{keyterm_data_target_hashed}" aria-expanded="true" aria-controls="{keyterm_data_target}">\n'
            cardItem += '            <i class="fa fa-chevron-down pull-right"></i>'
            cardItem += '            <div class="keyterm-title"> {keyterm} </div> \n'
            cardItem += '         </button>\n'
            cardItem += '      </h5>\n'
            cardItem += '   </div>\n'
            cardItem += '   <div id="{keyterm_data_target}" class="collapse {keyterm_show}" aria-labelledby="{keyterm_card_header_id}" data-parent="{div_parent_id}">\n'
            cardItem += '      <div class="{keyterm_data_target} card-body">\n'
            cardItem += '         Example Content.\n'
            cardItem += '      </div>\n'
            cardItem += '   </div>\n'
            cardItem += '</div>\n'
            cardItem = cardItem.format(
                div_parent_id = div_parent_id,
                keyterm_card_header_id = keyterm_card_header_id,
                keyterm_data_target_hashed = keyterm_data_target_hashed,
                keyterm_data_target = keyterm_data_target,
                keyterm = keyterm,
                keyterm_show = keyterm_show
            )
            self.keytermhtml += bleach.clean(cardItem, tags=self.allowed_tags, attributes=self.allowed_attributes)
