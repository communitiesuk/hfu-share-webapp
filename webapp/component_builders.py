from typing import Optional

from crispy_forms.layout import flatatt


class LinkBuilderBase:
    classes: str

    def __init__(
        self,
        text: str,
        href: str,
        css_class: str = "",
        **kwargs,
    ):
        self.text = text
        self.href = href

        if css_class:
            self.classes += f" {css_class.strip()}"

        self.attrs = flatatt(kwargs)


class LinkBuilder(LinkBuilderBase):
    classes = "govuk-link"

    def __init__(
        self,
        text: str,
        href: str,
        *,
        css_class: str = "",
        visually_hidden_text: Optional[str] = None,
        no_visited_state: bool = False,
        opens_in_new_tab: bool = False,
        **kwargs,
    ):
        if no_visited_state:
            css_class += " govuk-link--no-visited-state"

        if opens_in_new_tab:
            kwargs["rel"] = "noreferrer noopener"
            kwargs["target"] = "_blank"
            visually_hidden_text = "(opens in new tab)"

        self.visually_hidden_text = visually_hidden_text

        super().__init__(text, href, css_class, **kwargs)


class LinkAsButtonBuilder(LinkBuilderBase):
    classes = "govuk-button"

    def __init__(
        self,
        text: str,
        href: str,
        *,
        css_class: str = "",
        type: str = "primary",
        **kwargs,
    ):
        match type:
            case "secondary":
                css_class += " govuk-button--secondary"
            case "warning":
                css_class += " govuk-button--warning"

        super().__init__(text, href, css_class, data_module="govuk-button", **kwargs)


class TagBuilder:
    classes = "govuk-tag"

    def __init__(self, text: str, colour: Optional[str] = None, css_class: str = ""):
        self.text = text

        if colour:
            self.classes += f" govuk-tag--{colour}"

        if css_class:
            self.classes += f" {css_class}"
