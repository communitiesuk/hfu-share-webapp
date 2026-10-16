// On narrow viewports MOJ Frontend turns the side navigation into a
// horizontally scrolling row, so the active section's nav item can load
// scrolled out of view. Re-center it so it is visible without the user
// having to scroll the navigation themselves.
const scrollCurrentSectionIntoView = function (sideNav) {
  const active = sideNav.querySelector('.moj-side-navigation__item--active')
  if (!active || sideNav.scrollWidth <= sideNav.clientWidth) {
    return
  }
  const navRect = sideNav.getBoundingClientRect()
  const activeRect = active.getBoundingClientRect()
  sideNav.scrollLeft += activeRect.left - navRect.left - (navRect.width - activeRect.width) / 2
}

const initDetailViewFocus = function () {
  const sideNav = document.querySelector('.moj-side-navigation')
  if (!sideNav) {
    return
  }

  scrollCurrentSectionIntoView(sideNav)
}

export { initDetailViewFocus }
