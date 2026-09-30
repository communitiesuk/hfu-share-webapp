const dropdownArrow = () =>
    '<svg class="autocomplete__dropdown-arrow-down" width="10" height="6" viewBox="0 0 10 6" fill="none" xmlns="http://www.w3.org/2000/svg"> <path d="M1.25 0.5L5.25 4.5L9.25 0.5" stroke="#0B0C0C" /> </svg>';

class SearchableSelectContainer {
    constructor($element) {
        this.element = $element.get(0);
        this.type = $element.data("searchableType");
        this.inputId = $element.data("searchableInputId");
        this.inputName = $element.data("searchableInputName");
        this.dataAjaxUrl = $element.data("searchableDataAjaxUrl");
        this.defaultValue = $element.data("searchableDefaultValue");
    }

    init() {
        if (this.type === "lazy") {
            this.initSearchableSelectLazyContainer();
        } else {
            this.initSearchableSelectNormalContainer();
        }
    }

    initSearchableSelectLazyContainer() {
        accessibleAutocomplete({
            element: this.element,
            id: this.inputId,
            name: this.inputName,
            placeholder: "Start typing postcode...",
            minLength: 2,
            showAllValues: true,
            menuClasses: "govuk-body",
            autoselect: false,
            dropdownArrow: dropdownArrow,
            defaultValue: this.defaultValue,
            source: (query, populateResults) => {
                if (query.length < 2) {
                    populateResults([]);
                    return;
                }

                fetch(`${this.dataAjaxUrl}?q=${encodeURIComponent(query)}`)
                    .then((response) => {
                        return response.json();
                    })
                    .then((data) => {
                        var searchResults = data.results || [];
                        populateResults(searchResults);
                    })
                    .catch((error) => {
                        populateResults([]);
                    });
            },
        });
    }

    initSearchableSelectNormalContainer() {
        accessibleAutocomplete.enhanceSelectElement({
            selectElement: this.element,
            placeholder: "Start typing or select one...",
            showAllValues: true,
            autoselect: false,
            dropdownArrow: dropdownArrow,
            menuClasses: "govuk-body",
        });
    }
}

const initSearchableSelect = () => {
    $('[data-module="searchable-select"]').each((_, element) => {
        new SearchableSelectContainer($(element)).init();
    });
};

export { initSearchableSelect };
