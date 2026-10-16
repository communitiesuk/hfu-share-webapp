// On narrow viewports MOJ Frontend turns the side navigation into a
// horizontally scrolling row, so the active section's nav item can load
// scrolled out of view. Re-center it so it is visible without the user
// having to scroll the navigation themselves.
const scrollCurrentSectionIntoView = ($sideNav) => {
  const $active = $sideNav.find('.moj-side-navigation__item--active')
  if (!$active.length || $sideNav[0].scrollWidth <= $sideNav[0].clientWidth) {
    return
  }
  const navRect = $sideNav[0].getBoundingClientRect()
  const activeRect = $active[0].getBoundingClientRect()
  $sideNav.scrollLeft($sideNav.scrollLeft() + activeRect.left - navRect.left - (navRect.width - activeRect.width) / 2);
}

const initMOJSideNavMobileScroll = () => {
  const $sideNav = $('.moj-side-navigation')

  if ($sideNav.length) {
    scrollCurrentSectionIntoView($sideNav)
  }
}

export { initMOJSideNavMobileScroll }
