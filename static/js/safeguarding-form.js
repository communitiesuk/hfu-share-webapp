document.addEventListener("DOMContentLoaded", function () {
    // Cache DOM elements
    const el = id => document.getElementById(id);
    const group = id => el(id)?.closest(".govuk-form-group");

    const checkTypeField = el("id_check_type");
    const statusField = el("id_status");
    const accExistsFail = group("id_accommodation_exists_failure");
    const accSuitableFail = group("id_accommodation_suitable_failure");
    const sponsorDBSType = group("id_sponsor_dbs_passed");
    const sponsorFail = group("id_sponsor_dbs_failure");
    const accommodations = group("id_accommodations");
    const sponsors = group("id_sponsors");
    const notes = group("id_notes");
    const notesField = el("id_notes");
    const sponsorFailReasonField = el("id_sponsor_dbs_failure");
    const statusGroup = statusField?.closest(".govuk-form-group");
    const buttons = document.querySelectorAll("button");

    const ACCOMM_EXISTS = "1";
    const ACCOMM_SUITABLE = "2";
    const SPONSOR_DBS = "3";
    const GROUP_ARRIVED = "4";

    const PASSED = "Passed";
    const FAILED = "Failed";

    const COMMENT_REQUIRED_ERROR = "You must enter a reason.";

    function showField(group) {
        if (!group) return;
        group.style.display = "";
        // Re-enable so inputs are included in the POST request
        group.querySelectorAll("input, select, textarea").forEach(el => el.disabled = false);
    }

    function hideField(group) {
        if (!group) return;
        group.style.display = "none";
        // Disable so inputs are excluded from the POST request
        group.querySelectorAll("input, select, textarea").forEach(el => el.disabled = true);
    }

    function hideAllFields() {
        [accExistsFail, accSuitableFail, sponsorDBSType, sponsorFail, accommodations, sponsors, notes, statusGroup]
            .forEach(hideField);
    }

    function updateVisibility() {
        const selectedCheckType = checkTypeField?.value;
        const selectedStatus = statusField?.value;
        hideAllFields();
        const buttonsDisabled = !selectedCheckType;
        buttons.forEach(btn => btn.disabled = buttonsDisabled);
        if (!selectedCheckType) return;
        showField(statusGroup);
        switch (selectedCheckType) {
            case ACCOMM_EXISTS:
                showField(accommodations);
                showField(notes);
                if (selectedStatus === FAILED) showField(accExistsFail);
                break;
            case ACCOMM_SUITABLE:
                showField(accommodations);
                showField(notes);
                if (selectedStatus === FAILED) showField(accSuitableFail);
                break;
            case SPONSOR_DBS:
                showField(sponsors);
                showField(notes);
                if (selectedStatus === PASSED) showField(sponsorDBSType);
                else if (selectedStatus === FAILED) showField(sponsorFail);
                break;
            case GROUP_ARRIVED:
                showField(notes);
                break;
        }
    }

    function setNotesRequiredIfNeeded() {
        const selectedCheckType = checkTypeField?.value;
        const selectedStatus = statusField?.value;
        const sponsorFailReason = sponsorFailReasonField ? sponsorFailReasonField.value : null;
        const help = document.getElementById('id_notes_hint');
        if (
            selectedCheckType === SPONSOR_DBS &&
            selectedStatus === FAILED &&
            sponsorFailReason === "SPONSOR_NOT_SUITABLE"
        ) {
            if (notesField) notesField.required = true;
            if (help) {
                help.setAttribute("aria-live", "polite");
                help.textContent = "You must add a reason if you select 'Sponsor is not suitable - other reasons' from the list for UKVI to review the comments. For any other reason selected adding a comment is optional.";
            }
        } else {
            if (notesField) notesField.required = false;
            if (help) {
                help.setAttribute("aria-live", "polite");
                help.textContent = "You can add any reason for the option you selected, if needed. The text you enter should be short and clear. (optional)";
            }
            clearNotesError();
        }
    }

    function showNotesError() {
        if (!notes || !notesField) return;
        notes.classList.add("govuk-form-group--error");
        notesField.classList.add("govuk-textarea--error");
        notesField.setAttribute("aria-invalid", "true");
        if (!el("id_notes_error")) {
            const errorSpan = document.createElement("span");
            errorSpan.className = "govuk-error-message";
            errorSpan.id = "id_notes_error";
            errorSpan.innerHTML = `<span class="govuk-visually-hidden">Error:</span> ${COMMENT_REQUIRED_ERROR}`;
            notesField.parentNode.insertBefore(errorSpan, notesField);
        }
        let describedby = notesField.getAttribute("aria-describedby") || "";
        if (!describedby.includes("id_notes_error")) {
            notesField.setAttribute("aria-describedby", (describedby + " id_notes_error").trim());
        }
        let errorSummary = document.querySelector('.govuk-error-summary');
        if (!errorSummary) {
            errorSummary = document.createElement('div');
            errorSummary.className = 'govuk-error-summary';
            errorSummary.setAttribute('role', 'alert');
            errorSummary.setAttribute('aria-live', 'assertive');
            errorSummary.setAttribute('tabindex', '-1');
            errorSummary.innerHTML = `
                <h2 class="govuk-error-summary__title">There is a problem</h2>
                <div class="govuk-error-summary__body">
                    <ul class="govuk-list govuk-error-summary__list"></ul>
                </div>
            `;
            const h1 = document.querySelector('h1.govuk-body-l');
            if (h1 && h1.parentNode) {
                h1.parentNode.insertBefore(errorSummary, h1);
            } else {
                const form = notes.closest('form');
                if (form) form.insertBefore(errorSummary, form.firstChild?.nextSibling || form.firstChild);
            }
        }
        errorSummary.focus();
        const errorList = errorSummary.querySelector('.govuk-error-summary__list');
        if (errorList && !errorList.querySelector('#error-summary-notes')) {
            const li = document.createElement('li');
            li.id = 'error-summary-notes';
            li.innerHTML = `<a href="#id_notes">${COMMENT_REQUIRED_ERROR}</a>`;
            errorList.appendChild(li);
        }
    }

    function clearNotesError() {
        if (!notes || !notesField) return;
        notes.classList.remove("govuk-form-group--error");
        notesField.classList.remove("govuk-textarea--error");
        notesField.removeAttribute("aria-invalid");
        const errorSpan = el("id_notes_error");
        if (errorSpan) errorSpan.remove();
        let describedby = notesField.getAttribute("aria-describedby") || "";
        notesField.setAttribute("aria-describedby", describedby.replace("id_notes_error", "").trim());
        const errorSummary = document.querySelector('.govuk-error-summary');
        if (errorSummary) {
            const li = errorSummary.querySelector('#error-summary-notes');
            if (li) li.remove();
            if (!errorSummary.querySelector('li')) errorSummary.remove();
        }
    }

    function validateNotesOnSubmit(e) {
        const selectedCheckType = checkTypeField?.value;
        const selectedStatus = statusField?.value;
        const sponsorFailReason = sponsorFailReasonField ? sponsorFailReasonField.value : null;
        if (
            selectedCheckType === SPONSOR_DBS &&
            selectedStatus === FAILED &&
            sponsorFailReason === "SPONSOR_NOT_SUITABLE" &&
            (!notesField || !notesField.value.trim())
        ) {
            showNotesError();
            if (notesField) notesField.focus();
            e.preventDefault();
            return false;
        } else {
            clearNotesError();
        }
    }

    // Listen for changes
    if (checkTypeField) checkTypeField.addEventListener("change", updateVisibility);
    if (statusField) statusField.addEventListener("change", updateVisibility);
    if (checkTypeField) checkTypeField.addEventListener("change", setNotesRequiredIfNeeded);
    if (statusField) statusField.addEventListener("change", setNotesRequiredIfNeeded);
    if (sponsorFailReasonField) sponsorFailReasonField.addEventListener("change", setNotesRequiredIfNeeded);
    buttons.forEach(btn => {
        if (btn.type === "submit") {
            btn.addEventListener("click", validateNotesOnSubmit);
        }
    });
    updateVisibility();
});
