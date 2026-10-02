const updateIndices = (container) => {
    const items = container.querySelectorAll(".array-input-item:not(.array-input-template)");
    const fieldName = container.dataset.name;
    const isRequired = container.dataset.required === "true";
    const max = parseInt(container.dataset.max || "5", 10);
    const addLink = container.querySelector(".add-array-item");

    // Update input names
    items.forEach((item, index) => {
        const input = item.querySelector("input");
        const label = item.querySelector("label");
        const labelNumber = label.querySelector(".array-input-item-label--counter");

        const idSuffix = index > 0 ? `-${index}` : "";
        const inputId = `id_${fieldName}${idSuffix}`;

        input.name = `${fieldName}-${index}`;
        input.id = inputId;

        label.setAttribute("for", inputId);
        labelNumber.textContent = index + 1;
    });

    // Add button
    if (addLink) {
        updateElementVisibility(addLink, items.length < max);
    }

    // Remove button visibility
    items.forEach((item) => {
        const removeLink = item.querySelector(".remove-array-item");
        if (removeLink) {
            updateElementVisibility(removeLink, !(isRequired && items.length === 1));
        }
    });
};

const initArrayWidget = (container) => {
    if (container.dataset.initialized) return;

    const addLink = container.querySelector(".add-array-item");
    const template = container.querySelector(".array-input-template");

    addLink?.addEventListener("click", (e) => {
        e.preventDefault();
        const max = parseInt(container.dataset.max || "5", 10);
        const items = container.querySelectorAll(".array-input-item:not(.array-input-template)");
        if (items.length >= max) return;

        const clone = template.cloneNode(true);
        clone.classList.remove("array-input-template", "app-display--none");
        clone.classList.add("app-display--flex");
        clone.querySelector("input").value = "";
        container.insertBefore(clone, addLink);
        updateIndices(container);
    });

    container.addEventListener("click", (e) => {
        if (e.target.classList.contains("remove-array-item")) {
            e.preventDefault();
            const item = e.target.closest(".array-input-item");
            if (!item.classList.contains("array-input-template")) {
                item.remove();
                updateIndices(container);
            }
        }
    });

    container.dataset.initialized = "true";
    updateIndices(container);
};

const updateElementVisibility = (element, isVisible) => {
    if (isVisible) {
        element.classList.add("app-display--block");
        element.classList.remove("app-display--none");
    } else {
        element.classList.add("app-display--none");
        element.classList.remove("app-display--block");
    }
};

const initMultiValueTextInput = () => {
    document.querySelectorAll('[data-module="array-input-group"]').forEach(initArrayWidget);
};

export { initMultiValueTextInput };
