import { initAll as initGovukFrontend } from "../govuk-frontend/govuk-frontend-6.6.0.min.js";
import { initAll as initMOJFrontend } from "../moj-frontend/moj-frontend-11.1.0.min.js";
import { initMOJSideNavMobileScroll } from "./moj-side-nav-mobile-scroll.js";

const SIDE_NAV_LIST_CLASS = ".moj-side-navigation__list";
const RECORD_DETAIL_CONTENT_ELEMENT = "#record-detail-content";

// True unless the click should open a new tab/window (modifier key or
// non-primary button), which the browser should handle itself.
const isPlainClick = (event) =>
  event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey;

// Fetches the page content, returning null if unsuccessful.
const fetchSideNavPage = async (href) => {
  try {
    const response = await fetch(href);

    if (response.status === 200) {
      const body = await response.text();
      const doc = new DOMParser().parseFromString(body, "text/html");
      const sideNavListElement = doc.querySelector(SIDE_NAV_LIST_CLASS);
      const recordDetailContentElement = doc.querySelector(RECORD_DETAIL_CONTENT_ELEMENT);

      if (sideNavListElement && recordDetailContentElement) {
        return { sideNavListElement, recordDetailContentElement, title: doc.title };
      }
    }
  } catch (error) {
    // Fall back to normal navigation.
  }

  return null;
};

class SideNavLinkManager {
  constructor($sideNav) {
    this.$sideNav = $sideNav;
  }

  init() {
    this.bindLinks();

    // Handle browser back/forward navigation.
    window.addEventListener("popstate", () => {
      this.loadPage(window.location.href, false);
    });
  }

  // Rebind links after the side navigation is replaced.
  bindLinks() {
    this.$sideNav.find(".moj-side-navigation__item > a").each((_index, linkElement) => {
      $(linkElement).click(async (event) => {
        if (!isPlainClick(event) || linkElement.target === "_blank") {
          return;
        }

        event.preventDefault();

        await this.loadPage($(linkElement).attr("href"), true);
      });
    });
  }

  async loadPage(href, pushState) {
    const page = await fetchSideNavPage(href);

    if (!page) {
      // Fall back to a full navigation rather than leave stale content
      // showing under a mismatched URL.
      window.location.href = href;
      return;
    }

    $(SIDE_NAV_LIST_CLASS).replaceWith(page.sideNavListElement);
    $(RECORD_DETAIL_CONTENT_ELEMENT).replaceWith(page.recordDetailContentElement);
    document.title = page.title;

    if (pushState) {
      window.history.pushState(null, "", href);
    }

    // Re-bind the fresh nav links and re-centre the active one on mobile.
    this.$sideNav = $(".moj-side-navigation");
    this.bindLinks();
    initMOJSideNavMobileScroll();

    // Progressively enhance the new content, scoped to it so components
    // elsewhere on the page aren't re-initialised.
    initGovukFrontend({ scope: page.recordDetailContentElement });
    initMOJFrontend({ scope: page.recordDetailContentElement });

    // Restore keyboard focus to the updated content.
    document.getElementById("record-detail-content").focus({ preventScroll: true });
  }
}

const initMOJSideNavReload = () => {
  const $sideNav = $(".moj-side-navigation");

  if ($sideNav.length) {
    new SideNavLinkManager($sideNav).init();
  }
};

export { initMOJSideNavReload };
