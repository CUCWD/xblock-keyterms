/* Javascript for KeytermsXBlock. */

// https://edx.readthedocs.io/projects/edx-developer-guide/en/latest/preventing_xss/preventing_xss.html

// Rather than import lodash, just get the function we want.
function camelize(str) {
    return str.toLowerCase()
        // Replaces any - or _ characters with a space 
        .replace(/[-_/]+/g, ' ')
        // Removes any non alphanumeric characters 
        .replace(/[^\w\s]/g, '')
        // Ensure there are no double spaces after removing characters
        .replace(/  /g, ' ')
        // Uppercases the first character in each group immediately following a space 
        // (delimited by spaces) 
        .replace(/ (.)/g, function($1) { return $1.toUpperCase(); })
        // Removes spaces 
        .replace(/ /g, '');
}

function KeytermsXBlock(runtime, element, initData) {
    // Getting the handles for the python functions
    var cmsBaseURL = initData.cmsBaseURL;
    var keyTermsAPIRootURL = initData.keyTermsAPIRootURL;
    var learningMicrofrontendURL = initData.learningMicrofrontendURL;
    var addkeywordhandlerUrl = runtime.handlerUrl(element, 'add_keyterm');
    var removekeywordhandlerUrl = runtime.handlerUrl(element, 'remove_keyterm');
    var editlessonhandlerUrl = runtime.handlerUrl(element, 'edit_lesson');
    var getincludedkeytermshandlerUrl = runtime.handlerUrl(element, 'get_included_keyterms');

    // Variables needed to store the data for this page.
    var keytermsJson;
    var allKeytermsSet = new Set();
    var courseid;

    // Used to update the keyterms html
    function updateSummary(result) {
        edx.HtmlUtils.setHtml($('.lessonsummary'), edx.HtmlUtils.HTML(result.lessonsummary));
    }

    // Used to update the keyterms html
    function updateKeyterms(result) {
        edx.HtmlUtils.setHtml($('.allKeytermsList'), edx.HtmlUtils.HTML(result.keytermhtml));
    }

    // Used for getting courseID
    function getStringBetween(str, start, end) {
        const result = str.match(new RegExp(start + "(.*)" + end));
        return result[1];
    }

    // Gets the information about a specific keyterm
    function getKeyTermInfo(keyterm) {
        for (var i = 0; i < keytermsJson.length; i++) {
            if (keytermsJson[i]["key_name"] === keyterm) {
                return keytermsJson[i];
            }
        }
    }

    // Editing lesson summary handler
    $(".editLessonSummary").click(function(event) {
        event.preventDefault();
        var lesson = $(".lesson-field").val();
        var data = { lessonsummary: lesson };

        $.ajax({
            type: "POST",
            url: editlessonhandlerUrl,
            data: JSON.stringify(data),
            success: updateSummary
        });
    });

    // Used for editing the keyterms
    function populateOptions(result) {
        var available = $('#id_keyterms_from');
        var chosen = $('#id_keyterms_to');

        // Adds each term to appropriate side of list
        allKeytermsSet.forEach(term => {
            var html = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<option value="'), gettext(term), edx.HtmlUtils.HTML('" title="'),
                gettext(term), edx.HtmlUtils.HTML('">'), gettext(term), edx.HtmlUtils.HTML('</option>'));
            (result.includedkeyterms).includes(term) ? edx.HtmlUtils.append($(chosen), html) : edx.HtmlUtils.append($(available), html);
        });

        // Handle search feature
        $('#id_keyterms_input').keyup(function() {
            $('#id_keyterms_from').find('option').each(function() {
                var txt = $(this).val();
                var regex = new RegExp($('#id_keyterms_input').val(), "i");
                $(this).css("display", regex.test(txt) ? 'block' : 'none');
            });
        });

        // Handle double clicking an element
        $("#id_keyterms_from option").on('dblclick', function(event) {
            event.preventDefault();
            var term = $(this).val();
            data = { keyterm: term, course_id: courseid }
            $.ajax({
                type: "POST",
                url: addkeywordhandlerUrl,
                data: JSON.stringify(data),
                async: false,
                success: function(result) { updateKeyterms(result) }
            });
            $(`#id_keyterms_from option[value='${term}']`).remove();
            var html = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<option value="'), gettext(term), edx.HtmlUtils.HTML('" title="'),
                gettext(term), edx.HtmlUtils.HTML('">'), gettext(term), edx.HtmlUtils.HTML('</option>'));
            edx.HtmlUtils.append($(chosen), html);
        });

        // Handle double clicking an element
        $("#id_keyterms_to option").on('dblclick', function(event) {
            event.preventDefault();
            var term = $(this).val();
            data = { keyterm: term, course_id: courseid }
            $.ajax({
                type: "POST",
                url: removekeywordhandlerUrl,
                data: JSON.stringify(data),
                async: false,
                success: function(result) { updateKeyterms(result) }
            });
            $(`#id_keyterms_to option[value='${term}']`).remove();
            var html = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<option value="'), gettext(term), edx.HtmlUtils.HTML('" title="'),
                gettext(term), edx.HtmlUtils.HTML('">'), gettext(term), edx.HtmlUtils.HTML('</option>'));
            edx.HtmlUtils.append($(available), html);
        });

        // Handle selecting many elements
        $('#id_keyterms_add_link').on('click', function(event) {
            event.preventDefault();
            var arr = $.map($('#id_keyterms_from option:selected'), function(option) {
                return option.value;
            });
            arr.forEach(term => {
                data = { keyterm: term, course_id: courseid }
                $.ajax({
                    type: "POST",
                    url: addkeywordhandlerUrl,
                    data: JSON.stringify(data),
                    async: false,
                    success: function(result) { updateKeyterms(result) }
                });
                $(`#id_keyterms_from option[value='${term}']`).remove();
                var html = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<option value="'), gettext(term), edx.HtmlUtils.HTML('" title="'),
                    gettext(term), edx.HtmlUtils.HTML('">'), gettext(term), edx.HtmlUtils.HTML('</option>'));
                edx.HtmlUtils.append($(chosen), html);
            });
        });

        // Handle selecting many elements
        $('#id_keyterms_remove_link').on('click', function(event) {
            event.preventDefault();
            var arr = $.map($('#id_keyterms_to option:selected'), function(option) {
                return option.value;
            });
            arr.forEach(term => {
                data = { keyterm: term, course_id: courseid }
                $.ajax({
                    type: "POST",
                    url: removekeywordhandlerUrl,
                    data: JSON.stringify(data),
                    async: false,
                    success: function(result) { updateKeyterms(result) }
                });
                $(`#id_keyterms_to option[value='${term}']`).remove();
                var html = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<option value="'), gettext(term), edx.HtmlUtils.HTML('" title="'),
                    gettext(term), edx.HtmlUtils.HTML('">'), gettext(term), edx.HtmlUtils.HTML('</option>'));
                edx.HtmlUtils.append($(available), html);
            });
        });

        // Handle remove all button
        $('#id_keyterms_remove_all_link').on('click', function(event) {
            event.preventDefault();
            var arr = $.map($('#id_keyterms_to option'), function(option) {
                return option.value;
            });
            arr.forEach(term => {
                data = { keyterm: term, course_id: courseid }
                $.ajax({
                    type: "POST",
                    url: removekeywordhandlerUrl,
                    data: JSON.stringify(data),
                    async: false,
                    success: function(result) { updateKeyterms(result) }
                });
                $(`#id_keyterms_to option[value='${term}']`).remove();
                var html = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<option value="'), gettext(term), edx.HtmlUtils.HTML('" title="'),
                    gettext(term), edx.HtmlUtils.HTML('">'), gettext(term), edx.HtmlUtils.HTML('</option>'));
                edx.HtmlUtils.append($(available), html);
            });
        });

        // Handle choose all button
        $('#id_keyterms_add_all_link').on('click', function(event) {
            event.preventDefault();
            var arr = $.map($('#id_keyterms_from option'), function(option) {
                return option.value;
            });
            arr.forEach(term => {
                data = { keyterm: term, course_id: courseid }
                $.ajax({
                    type: "POST",
                    url: addkeywordhandlerUrl,
                    data: JSON.stringify(data),
                    async: false,
                    success: function(result) { updateKeyterms(result) }
                });
                $(`#id_keyterms_from option[value='${term}']`).remove();

                var html = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<option value="'), gettext(term), edx.HtmlUtils.HTML('" title="'),
                    gettext(term), edx.HtmlUtils.HTML('">'), gettext(term), edx.HtmlUtils.HTML('</option>'));
                edx.HtmlUtils.append($(chosen), html);
            });
        });
    }

    // initializing the data

    $(function() {
        // Getting courseid
        const url = window.location.href;
        courseid = getStringBetween(url, 'block\-v1:', 'type').slice(0, -1);

        // Setting glossary url
        // $("#glossarymsg").html(`Click on or hover the term to reveal the definitions on the <a target="_blank" rel="noopener noreferrer" href="http://localhost:2000/course/course-v1:${courseid}/glossary">Glossary</a> page.`)
        $(".glossarymsg").html(`Click on the term to reveal definition(s), links to courseware textbook or page content and external links for additional information.`)

        // Getting all the keyterms. For devstack environments make sure to add 
        // `127.0.0.1  edx.devstack.keyterms-api` to `/etc/hosts` for your host machine since this
        // API call is handled in the client side.
        courseid.replace(" ", "+");
        resturl = keyTermsAPIRootURL + '/api/v1/course_terms/?course_id=course-v1:' + courseid;

        $.getJSON(resturl,
            function(data, err) {
                // Store list of all keyterms
                keytermsJson = data;
                // Sorts the keyterms into alphabetical order
                keytermsJson.sort((a, b) => {
                    if (a.key_name < b.key_name) {
                      return -1;
                    }
                    if (a.key_name > b.key_name) {
                      return 1;
                    }
                    return 0;
                  });
                allKeytermsSet.clear();
                keytermsJson.forEach(keyterm => allKeytermsSet.add(keyterm["key_name"]));
            }).then(data => {
            // Was adding code to style the accordian card header when clicked.
            $(".card-header").each(function() {
                const keyterm = this.getElementsByTagName("button")[0].innerText;
                const keytermCardHeaderId = $(this).attr('id');
                const keytermDataTarget = camelize("collapse " + keyterm);
                const keytermDataTargetHashed = "#" + keytermDataTarget;
                const keytermInformation = getKeyTermInfo(keyterm);

                var formattedContent = `<div class="collapsible-box">`;

                // Definitions
                if (keytermInformation["definitions"].length > 0) {
                    formattedContent += `<div class="flex-col">`
                    if (keytermInformation["definitions"].length > 1) {
                        formattedContent += `<b>Definitions</b>`
                    }
                    else {
                        formattedContent += `<b>Definition</b>`
                    }
                    formattedContent += `<ul class="bullets">`;
                    keytermInformation["definitions"].forEach(definition => {
                        formattedContent += `<li>${definition["description"]}</li>`
                    })
                    formattedContent += `</ul></div>`;
                }

                // Textbooks
                if (keytermInformation["textbooks"].length > 0) {
                    formattedContent += `<div class="flex-col"><b>Textbooks</b><ul class="bullets">`
                    keytermInformation["textbooks"].forEach(textbook => {
                        formattedContent += `<li><a target="_blank" rel="noopener noreferrer" href='http://${cmsBaseURL}/textbooks_api/course-v1:${courseid}/${textbook["textbook_link"]}' class="btn">`
                        formattedContent += `${textbook["chapter"]}\n(Page ${textbook["page_num"]})`
                        formattedContent += `</a></li>`
                    })
                    formattedContent += `</ul></div>`;
                }

                // Lessons
                if (keytermInformation["lessons"].length > 0) {
                    formattedContent += `<div class="flex-col"><b>Lesson Pages</b><ul class="bullets">`
                    keytermInformation["lessons"].sort((a, b) => a.module_name === b.module_name ? (a.lesson_name > b.lesson_name ? 1 : -1) : (a.module_name > b.module_name ? 1 : -1))
                    keytermInformation["lessons"].forEach(lesson => {
                        formattedContent += `<li><a target="_blank" rel="noopener noreferrer" href='${learningMicrofrontendURL}/course/course-v1:${courseid}/${lesson["lesson_link"]}' class="btn">`
                        formattedContent += `${lesson["module_name"]} &gt; ${lesson["lesson_name"]} &gt; ${lesson["unit_name"]}`
                        formattedContent += `</a></li>`
                    })
                    formattedContent += `</ul></div>`;
                }

                // Resources
                if (keytermInformation["resources"].length > 0) {
                    formattedContent += `<div class="flex-col"><b>Resources</b><ul class="bullets">`
                    keytermInformation["resources"].forEach(resource => {
                        formattedContent += `<li><a target="_blank" rel="noopener noreferrer" href="${resource["resource_link"]}">${resource["friendly_name"]}</a></li>`
                    })
                    formattedContent += `</ul></div>`;
                }

                formattedContent += `</div>`;

                try {
                    var cardbody = keytermDataTargetHashed + " .card-body"
                    $(cardbody).html(formattedContent);
                } catch (e) {
                    console.log(e);
                }

                /*
                $(keytermDataTargetHashed).on('show.bs.collapse', function () {
                    $(keytermCardHeaderId).addClass("show");
                });
                $(keytermDataTargetHashed).on('hide.bs.collapse', function () {
                    $(keytermCardHeaderId).removeClass("show");
                });
                */
            });

            var data = { keyterms: allKeytermsSet, course_id: courseid };
            $.ajax({
                type: "POST",
                url: getincludedkeytermshandlerUrl,
                data: JSON.stringify(data),
                success: populateOptions
            });
        })
    });
}