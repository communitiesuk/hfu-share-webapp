// Below 40.0625em MOJ Frontend lays the side navigation out as a
// horizontally scrolling row, so the active item can load out of view.
const scrollCurrentSectionIntoView = (sideNav) => {
  const active = sideNav.querySelector('.moj-side-navigation__item--active')
  if (!active || sideNav.scrollWidth <= sideNav.clientWidth) {
    return
  }
  const navRect = sideNav.getBoundingClientRect()
  const activeRect = active.getBoundingClientRect()
  sideNav.scrollLeft += activeRect.left - navRect.left - (navRect.width - activeRect.width) / 2
}

const initMOJSideNavMobileScroll = () => {
  const sideNav = document.querySelector('.moj-side-navigation')

  if (sideNav) {
    scrollCurrentSectionIntoView(sideNav)
  }
}

export { initMOJSideNavMobileScroll }
