class GovUKFormGroup {
    static INPUT_ELEMENT_NAME = null;

    constructor() {
        const { INPUT_ELEMENT_NAME } = this.constructor;

        this.$formGroup = $(`#div_id_${INPUT_ELEMENT_NAME}`);
        this.$inputElement = this.$formGroup.find(`#id_${INPUT_ELEMENT_NAME}`);
    }

    toggleVisibility(show) {
        if (show) {
            this.$formGroup.removeClass("govuk-visually-hidden");
            this.$inputElement.removeAttr("tabIndex");
            this.$inputElement.removeAttr('disabled')
        } else {
            this.$formGroup.addClass("govuk-visually-hidden");
            this.$inputElement.attr("tabIndex", -1);
            this.$inputElement.attr('disabled', 'disabled')
        }
    }
}

class SelectField extends GovUKFormGroup {
    selectedValue() {
        return this.$inputElement.find(":selected").val();
    }
}

class CheckType extends SelectField {
    static INPUT_ELEMENT_NAME = "check_type";

    static OPTIONS = {
        ACCOMM_EXISTS: "1",
        ACCOMM_SUITABLE: "2",
        SPONSOR_DBS: "3",
        GROUP_ARRIVED: "4",
    };
}

class Status extends SelectField {
    static INPUT_ELEMENT_NAME = "status";

    static OPTIONS = {
        NOT_STARTED: "Not Started",
        PASSED: "Passed",
        FAILED: "Failed",
        NO_LONGER_REQUIRED: "No Longer Required",
    };
}

class AccExistsFailureReason extends SelectField {
    static INPUT_ELEMENT_NAME = "accommodation_exists_failure";

    static OPTIONS = {
        DOES_NOT_EXIST: "DOES_NOT_EXIST",
        NOT_RESIDENTIAL: "NOT_RESIDENTIAL",
    };
}

class AccSuitableFailureReason extends SelectField {
    static INPUT_ELEMENT_NAME = "accommodation_suitable_failure";

    static OPTIONS = {
        POOR_CONDITION: "POOR_CONDITION",
        OVERCROWDED: "OVERCROWDED",
        UNSUITABLE_FACILITIES: "UNSUITABLE_FACILITIES",
        NOT_ENOUGH_SPACE: "NOT_ENOUGH_SPACE",
        SPONSOR_DOES_NOT_LIVE_AT_ADDRESS: "SPONSOR_DOES_NOT_LIVE_AT_ADDRESS",
        SPONSOR_NOT_LINKED_TO_ADDRESS: "SPONSOR_NOT_LINKED_TO_ADDRESS",
        NO_CONSENT_TO_LIVE_AT_ADDRESS: "NO_CONSENT_TO_LIVE_AT_ADDRESS",
    };
}

class SponsorDBSFailureReason extends SelectField {
    static INPUT_ELEMENT_NAME = "sponsor_dbs_failure";

    static OPTIONS = {
        DBS_CHECK_FAILED: "DBS_CHECK_FAILED",
        NO_RESPONSE: "NO_RESPONSE",
        SPONSOR_NOT_SUITABLE: "SPONSOR_NOT_SUITABLE",
        NO_CONSENT_TO_BE_SPONSOR: "NO_CONSENT_TO_BE_SPONSOR",
    };
}

class Accommodations extends SelectField {
    static INPUT_ELEMENT_NAME = "accommodations";
}

class Sponsors extends SelectField {
    static INPUT_ELEMENT_NAME = "sponsors";
}

class SponsorDBSType extends SelectField {
    static INPUT_ELEMENT_NAME = "sponsor_dbs_passed";

    static OPTIONS = {
        BASIC: "BASIC_DBS",
        ENHANCED: "ENHANCED_DBS",
    };
}

class Comments extends GovUKFormGroup {
    static INPUT_ELEMENT_NAME = "notes";
    static ERROR_ID = `id_${this.INPUT_ELEMENT_NAME}-error`;
    static ERROR_MESSAGE = "You must enter a reason.";

    constructor(errorSummary) {
        super();

        this.$hint = $(`#id_${Comments.INPUT_ELEMENT_NAME}_hint`);
        this.errorSummary = errorSummary;
    }

    getValue() {
        return this.$inputElement.val().trim();
    }

    focus() {
        this.$inputElement.focus();
    }

    toggleRequired(isRequired) {
        if (isRequired) {
            this.$inputElement.attr("required", true);
            this.$hint.attr("aria-live", "polite");
            this.$hint.text(
                "You must add a reason if you select 'Sponsor is not suitable - other reasons' from the list for UKVI to review the comments. For any other reason selected adding a comment is optional.",
            );
        } else {
            this.$inputElement.removeAttr("required");
            this.$hint.attr("aria-live", "polite");
            this.$hint.text(
                "You can add any reason for the option you selected, if needed. The text you enter should be short and clear. (optional)",
            );
        }
        this.toggleError(false);
    }

    toggleError(show) {
        if (show) {
            this.errorSummary.addErrorMessage(Comments.ERROR_ID, Comments.ERROR_MESSAGE);
            this.addErrorMessage();
        } else {
            this.errorSummary.removeErrorMessage(Comments.ERROR_ID);
            this.removeErrorMessage();
        }
    }

    hasErrorMessage() {
        return this.findErrorMessage().length > 0;
    }

    findErrorMessage() {
        return this.$formGroup.find(`#${Comments.ERROR_ID}`);
    }

    addErrorMessage() {
        if (!this.hasErrorMessage()) {
            this.$formGroup.addClass("govuk-form-group--error");
            this.$inputElement.addClass("govuk-textarea--error");

            const ariaDescribedBy = this.$inputElement.attr("aria-describedby");
            this.$inputElement.attr("aria-describedby", `${ariaDescribedBy} ${Comments.ERROR_ID}`);

            this.$inputElement.before(
                $(`
<p id="${Comments.ERROR_ID}" class="govuk-error-message">
    <span class="govuk-visually-hidden">Error:</span> ${Comments.ERROR_MESSAGE}
</p>
`),
            );
        }
    }

    removeErrorMessage() {
        if (this.hasErrorMessage()) {
            this.$formGroup.removeClass("govuk-form-group--error");
            this.$inputElement.removeClass("govuk-textarea--error");

            const ariaDescribedBy = this.$inputElement.attr("aria-describedby");
            this.$inputElement.attr(
                "aria-describedby",
                ariaDescribedBy.replace(Comments.ERROR_ID, "").trim(),
            );

            this.findErrorMessage().remove();
        }
    }
}

class ErrorSummary {
    static ERROR_SUMMARY_HTML = `
<div class="govuk-error-summary" data-module="govuk-error-summary">
    <div role="alert">
        <h2 class="govuk-error-summary__title">
            There is a problem
        </h2>
        <div class="govuk-error-summary__body">
            <ul class="govuk-list govuk-error-summary__list"></ul>
        </div>
    </div>
</div>
`;

    constructor() {
        this.$container = $("#safeguarding-errors-container");
        this.$errorSummary = this.$container.find(".govuk-error-summary");
    }

    hasErrorSummary() {
        return this.$errorSummary.length > 0;
    }

    hasErrorMessage(errorId) {
        return this.findErrorMessage(errorId).length > 0;
    }

    findErrorMessage(errorId) {
        return this.$errorSummary.find(`[href='#${errorId}']`).parent();
    }

    numberOfErrorMessages() {
        return this.$errorSummary.find("ul > li").length;
    }

    addErrorMessage(errorId, errorMessage) {
        if (!this.hasErrorSummary()) {
            this.$errorSummary = $(ErrorSummary.ERROR_SUMMARY_HTML);
            this.$container.append(this.$errorSummary);
        }

        if (!this.hasErrorMessage(errorId)) {
            const $errorMessage = $(`
<li>
    <a href="#${errorId}">${errorMessage}</a>
</li>
`);
            this.$errorSummary.find("ul").append($errorMessage);
        }
    }

    removeErrorMessage(errorId) {
        if (this.hasErrorSummary()) {
            if (this.hasErrorMessage(errorId)) {
                this.findErrorMessage(errorId).remove();
            }

            if (this.numberOfErrorMessages() === 0) {
                this.$errorSummary.remove();
            }
        }
    }
}

class Form {
    constructor() {
        this.$form = $("#safeguarding-form");
        this.checkType = new CheckType();
        this.status = new Status();
        this.accExistsFailureReason = new AccExistsFailureReason();
        this.accSuitableFailureReason = new AccSuitableFailureReason();
        this.sponsorDBSFailureReason = new SponsorDBSFailureReason();
        this.accommodations = new Accommodations();
        this.sponsors = new Sponsors();
        this.sponsorDBSType = new SponsorDBSType();
        this.comments = new Comments(new ErrorSummary());
        this.$buttons = this.$form.find("button");
    }

    init() {
        this.checkType.$inputElement.on("change", () => {
            this.updateVisibility();
            this.setNotesRequiredIfNeeded();
        });

        this.status.$inputElement.on("change", () => {
            this.updateVisibility();
            this.setNotesRequiredIfNeeded();
        });

        this.sponsorDBSFailureReason.$inputElement.on("change", () => {
            this.setNotesRequiredIfNeeded();
        });

        this.$form.on("submit", (event) => {
            this.validateNotes(event);
        });

        this.setNotesRequiredIfNeeded();
        this.updateVisibility();
    }

    hideAllFormsExceptCheckType() {
        [
            this.status,
            this.accExistsFailureReason,
            this.accSuitableFailureReason,
            this.sponsorDBSFailureReason,
            this.accommodations,
            this.sponsors,
            this.sponsorDBSType,
            this.comments,
        ].forEach((formGroup) => {
            formGroup.toggleVisibility(false);
        });
    }

    toggleButtonInteractability(disabled) {
        if (disabled) {
            this.$buttons.attr("disabled", true);
            this.$buttons.attr("aria-disabled", true);
        } else {
            this.$buttons.removeAttr("disabled");
            this.$buttons.removeAttr("aria-disabled");
        }
    }

    updateVisibility() {
        const selectedCheckType = this.checkType.selectedValue();
        const selectedStatus = this.status.selectedValue();

        this.hideAllFormsExceptCheckType();
        this.toggleButtonInteractability(!selectedCheckType);

        if (!selectedCheckType) return;

        this.status.toggleVisibility(true);

        switch (selectedCheckType) {
            case CheckType.OPTIONS.ACCOMM_EXISTS:
                this.accommodations.toggleVisibility(true);
                this.comments.toggleVisibility(true);
                if (selectedStatus === Status.OPTIONS.FAILED)
                    this.accExistsFailureReason.toggleVisibility(true);
                break;
            case CheckType.OPTIONS.ACCOMM_SUITABLE:
                this.accommodations.toggleVisibility(true);
                this.comments.toggleVisibility(true);
                if (selectedStatus === Status.OPTIONS.FAILED)
                    this.accSuitableFailureReason.toggleVisibility(true);
                break;
            case CheckType.OPTIONS.SPONSOR_DBS:
                this.sponsors.toggleVisibility(true);
                this.comments.toggleVisibility(true);
                if (selectedStatus === Status.OPTIONS.PASSED)
                    this.sponsorDBSType.toggleVisibility(true);
                else if (selectedStatus === Status.OPTIONS.FAILED)
                    this.sponsorDBSFailureReason.toggleVisibility(true);
                break;
            case CheckType.OPTIONS.GROUP_ARRIVED:
                this.comments.toggleVisibility(true);
                break;
        }
    }

    isNotesRequired() {
        const selectedCheckType = this.checkType.selectedValue();
        const selectedStatus = this.status.selectedValue();
        const sponsorFailReason = this.sponsorDBSFailureReason.selectedValue();

        return (
            selectedCheckType === CheckType.OPTIONS.SPONSOR_DBS &&
            selectedStatus === Status.OPTIONS.FAILED &&
            sponsorFailReason === SponsorDBSFailureReason.OPTIONS.SPONSOR_NOT_SUITABLE
        );
    }

    setNotesRequiredIfNeeded() {
        this.comments.toggleRequired(this.isNotesRequired());
    }

    validateNotes(event) {
        if (this.isNotesRequired() && !this.comments.getValue()) {
            this.comments.toggleError(true);
            this.comments.focus();

            event.preventDefault();

            return false;
        } else {
            this.comments.toggleError(false);
        }
    }
}

$(() => new Form().init());
