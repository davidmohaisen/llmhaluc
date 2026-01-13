$(document).ready(function () {
    let processing = false;
    let decision = null;
    let lastReviewToken = null;
    let progressInterval = null;
    let objectInterval = null;
    const displayFields = [
        'id',
        'sub_id',
        'code_id',
        'prompt_eval_count',
        'prompt_eval_duration',
        'eval_count',
        'eval_duration',
        'total_duration',
        'load_duration',
        'response',
        'relevance_analysis'
    ];

    // Initialize empty fields with placeholder
    $('.json-field-value').text('-');

    $('#start-processing').click(function () {
        if (!processing) {
            $.get('/start_processing', function (data) {
                console.log(data.status);
                processing = true;
                $('#start-processing').addClass('d-none');
                $('#stop-processing').removeClass('d-none');
                startPolling();
            });
        }
    });

    $('#stop-processing').click(function () {
        if (processing) {
            $.get('/stop_processing', function (data) {
                console.log(data.status);
                processing = false;
                $('#stop-processing').addClass('d-none');
                $('#start-processing').removeClass('d-none');
                stopPolling();
            });
        }
    });

    function updateProgress() {
        if (!processing) {
            return;
        }
        $.get('/progress', function (data) {
            $('#file-progress').val(data.file_progress).text(data.file_progress.toFixed(2) + '%');
            $('#total-progress').val(data.total_progress).text(data.total_progress.toFixed(2) + '%');
        });
    }

    function updateObject() {
        if (!processing) {
            return;
        }
        $.get('/current_object', function (data) {
            console.log('Received object from server:', data);  // Debug log

            if (!data) {
                clearJsonDisplay();
                return;
            }

            $('#current-filename').text(data.current_filename || 'No file selected');
            $('#decision-buttons').removeClass('d-none');
            updateReviewBanner(data);
            updateFields(data);
            maybeResetDecision(data);
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error('Error fetching object:', textStatus, errorThrown);  // Debug log
        });
    }

    function startPolling() {
        if (progressInterval || objectInterval) {
            return;
        }
        updateProgress();
        updateObject();
        progressInterval = setInterval(updateProgress, 1000);
        objectInterval = setInterval(updateObject, 1000);
    }

    function stopPolling() {
        if (progressInterval) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
        if (objectInterval) {
            clearInterval(objectInterval);
            objectInterval = null;
        }
        clearJsonDisplay();
    }

    function setDecisionStatus(statusClass, text) {
        const status = $('#decision-status');
        status
            .removeClass('d-none status-vulnerable status-not-vulnerable status-not-relevant status-pending')
            .addClass(statusClass)
            .text(text);
    }

    function clearDecisionStatus() {
        $('#decision-status')
            .addClass('d-none')
            .removeClass('status-vulnerable status-not-vulnerable status-not-relevant status-pending')
            .text('');
    }

    function updateReviewBanner(data) {
        const reviewPhase = data.review_phase || 1;
        const showAnalysis = Boolean(data.show_analysis);
        const conflict = Boolean(data.conflict);

        $('#review-banner')
            .removeClass('d-none')
            .toggleClass('conflict', conflict);
        $('#review-phase').text(`Review ${reviewPhase}`);

        if (conflict) {
            $('#review-status-text').text('Conflict detected: review again with relevance analysis shown.');
            $('#json-display-title').text('Current JSON Object (Second Review)');
        } else if (showAnalysis) {
            $('#review-status-text').text('Review with relevance analysis shown.');
            $('#json-display-title').text('Current JSON Object (Analysis Review)');
        } else {
            $('#review-status-text').text('Blind review: relevance analysis hidden.');
            $('#json-display-title').text('Current JSON Object (Blind Review)');
        }

        if (showAnalysis) {
            $('#relevance_analysis').removeClass('d-none');
        } else {
            $('#relevance_analysis .json-field-value').text('-');
            $('#relevance_analysis').addClass('d-none');
        }
    }

    function updateFields(data) {
        displayFields.forEach((key) => {
            if (key === 'relevance_analysis' && !data.show_analysis) {
                return;
            }

            const element = $(`#${key} .json-field-value`);
            if (!element.length) {
                return;
            }

            let newValue = data[key];
            if (newValue === null || newValue === undefined) {
                newValue = '-';
            }

            if (element.text() !== String(newValue)) {
                element.fadeOut(200, function () {
                    element.text(String(newValue)).fadeIn(200);
                });
            }
        });
    }

    function maybeResetDecision(data) {
        const reviewToken = `${data.id || ''}:${data.review_phase || ''}`;
        if (reviewToken !== lastReviewToken) {
            decision = null;
            $('.btn-decision').removeClass('active');
            clearDecisionStatus();
            lastReviewToken = reviewToken;
        }
    }

    function clearJsonDisplay() {
        $('#json-display-title').text('JSON Object Details');
        $('#decision-buttons').addClass('d-none');
        $('#review-banner').addClass('d-none').removeClass('conflict');
        $('#relevance_analysis').removeClass('d-none');
        clearDecisionStatus();

        // Reset all fields with animation
        $('.json-field-value').fadeOut(200, function () {
            $(this).text('-').fadeIn(200);
        });

        $('#current-filename').text('No file selected');
        decision = null;
        lastReviewToken = null;
        $('.btn-decision').removeClass('active');
    }

    $('#not-vulnerable-btn').click(function () {
        decision = false;
        $('.btn-decision').removeClass('active');
        $(this).addClass('active');
        setDecisionStatus('status-not-vulnerable', 'Selected: Not Vulnerable');
    });

    $('#vulnerable-btn').click(function () {
        decision = true;
        $('.btn-decision').removeClass('active');
        $(this).addClass('active');
        setDecisionStatus('status-vulnerable', 'Selected: Vulnerable');
    });

    $('#not-relevant-btn').click(function () {
        decision = -1;
        $('.btn-decision').removeClass('active');
        $(this).addClass('active');
        setDecisionStatus('status-not-relevant', 'Selected: Not Relevant');
    });

    $('#submit-decision').click(function () {
        if (decision === null) {
            alert("Please select a decision.");
            return;
        }

        $(this).prop('disabled', true).text('Submitting...');
        setDecisionStatus('status-pending', 'Submitting decision...');

        // Convert decision to the correct type
        let decisionValue;
        if (decision === true) {
            decisionValue = 1;  // Vulnerable
        } else if (decision === false) {
            decisionValue = 0;  // Not vulnerable
        } else {
            decisionValue = decision;  // Already -1 for Not relevant
        }

        console.log('Submitting decision:', decisionValue);  // Debug log

        $.ajax({
            url: '/submit_decision',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ decision: decisionValue }),
            success: function (data) {
                console.log("Decision submitted successfully:", data.status);
                clearJsonDisplay();
            },
            error: function (xhr, status, error) {
                console.error("Error submitting decision:", error);
                console.error("Response:", xhr.responseText);  // Add response text to debug
                alert("Error submitting decision. Please try again.");
            },
            complete: function () {
                $('#submit-decision').prop('disabled', false).text('Submit Decision (S)');
            }
        });
    });

    // Keyboard shortcuts
    $(document).keydown(function (e) {
        if (!$('#decision-buttons').hasClass('d-none')) {
            switch (e.key.toLowerCase()) {
                case 'q':
                    $('#not-vulnerable-btn').click();
                    break;
                case 'w':
                    $('#vulnerable-btn').click();
                    break;
                case 'e':
                    $('#not-relevant-btn').click();
                    break;
                case 's':
                    $('#submit-decision').click();
                    break;
            }
        }
    });

    // Polling starts only after processing begins
}); 
