from typing import Optional


class TagBuilder:
    classes = "govuk-tag"

    def __init__(self, text: str, colour: Optional[str] = None, css_class: str = ""):
        self.text = text

        if colour:
            self.classes += f" govuk-tag--{colour}"

        if css_class:
            self.classes += f" {css_class}"
