/* Add dependent lesson choices to the built-in Studio editor. */
function KeyTermsLocationEditor(runtime, element) {
    'use strict';
    var root = $(element);
    var outline = JSON.parse(root.find('.keyterms-outline').attr('data-outline'));
    var module = root.find('[data-field-name="module_number"] select');
    var lesson = root.find('[data-field-name="lesson_number"] select');
    function updateLessons(preserve) {
        var value = preserve ? lesson.val() : '';
        var index = Number(module.val()) - 1;
        var allCourses = module.val() === 'all';
        lesson.empty().append($('<option>').val('').text('All terms in this module'));
        if (index >= 0 && outline[index]) {
            outline[index].lessons.forEach(function (name, i) {
                lesson.append($('<option>').val(String(i + 1)).text(name));
            });
        }
        lesson.val(value || '');
        lesson.prop('disabled', allCourses || !module.val());
        if (!preserve) { lesson.trigger('change'); }
    }
    StudioEditableXBlockMixin(runtime, element);
    module.on('change', function () { updateLessons(false); });
    updateLessons(true);
}
