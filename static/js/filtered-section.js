class Filter {
    optionSets = {
        open: {
            filterContainerClassAdd: "block",
            filterContainerClassRemove: "none",
            showFilterLinkText: "Hide filters",
            showFilterAriaExpandedStatus: true,
            inputValue: "True",
            localStorageValue: "true",
        },
        hidden: {
            filterContainerClassAdd: "none",
            filterContainerClassRemove: "block",
            showFilterLinkText: "Show filters",
            showFilterAriaExpandedStatus: false,
            inputValue: "False",
            localStorageValue: "false",
        },
    };
    showFiltersPanelParam = "show_filters_panel";

    constructor() {
        this.filterContainer = document.getElementById("filter-container");
        this.showFilterLink = document.getElementById("show-filter-link");
        this.input = document.getElementById("show_filters_panel");
        this.viewKey = `filtersPanelOpen_${window.location.pathname}`;
    }

    init() {
        if (!this.filterContainer || !this.showFilterLink) return;

        this.showHideFilter(this.getStateFromUrl() ?? this.getStateFromStorage());

        this.removeFilterFromUrl();

        this.showFilterLink.addEventListener("click", (e) => this.handleClickEvent(e));
    }

    handleClickEvent(e) {
        e.preventDefault();
        this.showHideFilter(!this.getStateFromStorage());
    }

    getStateFromStorage() {
        return localStorage.getItem(this.viewKey) === "true";
    }

    getStateFromUrl() {
        const url = new URL(window.location.href);

        const currentValue = url.searchParams.get(this.showFiltersPanelParam);

        if (!currentValue) return null;

        return currentValue === "True";
    }

    showHideFilter(open) {
        const optionSet = open ? this.optionSets.open : this.optionSets.hidden;

        this.filterContainer.classList.add(`app-display--${optionSet.filterContainerClassAdd}`)
        this.filterContainer.classList.remove(`app-display--${optionSet.filterContainerClassRemove}`)
        this.showFilterLink.textContent = optionSet.showFilterLinkText;
        this.showFilterLink.setAttribute("aria-expanded", optionSet.showFilterAriaExpandedStatus);
        if (this.input) this.input.value = optionSet.inputValue;

        localStorage.setItem(this.viewKey, optionSet.localStorageValue);
    }

    removeFilterFromUrl() {
        const url = new URL(window.location.href);

        if (url.searchParams.has(this.showFiltersPanelParam)) {
            url.searchParams.delete(this.showFiltersPanelParam);
            window.history.replaceState({}, "", url);
        }
    }
}

const initFilteredSection = () => {
    $('[data-module="filtered-section"]').each(() => {
        new Filter().init()
    })
}

export { initFilteredSection }
