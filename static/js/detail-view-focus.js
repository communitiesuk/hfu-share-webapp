// After a side navigation click, the next record section opens at the same
// scroll position and focus moves to its content, so the sections behave like
// tabs. The click is remembered in sessionStorage because it has to survive
// the page load, and is only acted on by the page the link pointed to.
const detailNavClickKey = 'detail_nav_click'

const scrollCurrentSectionIntoView = function (sideNav) {
  const active = sideNav.querySelector('.moj-side-navigation__item--active')
  if (!active || sideNav.scrollWidth <= sideNav.clientWidth) {
    return
  }
  const navRect = sideNav.getBoundingClientRect()
  const activeRect = active.getBoundingClientRect()
  sideNav.scrollLeft += activeRect.left - navRect.left - (navRect.width - activeRect.width) / 2
}

// Clicks that open the link in a new tab or window should not leave a saved
// position behind in this tab.
const isPlainClick = function (event) {
  return event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey
}

// Storage access throws when the browser blocks it. Both functions then do
// nothing, and the section opens at the top like a normal page load.
const restorePositionAfterNavClick = function (content) {
  let saved
  try {
    const raw = sessionStorage.getItem(detailNavClickKey)
    sessionStorage.removeItem(detailNavClickKey)
    saved = JSON.parse(raw)
  } catch {
    return
  }
  if (!saved || saved.path !== window.location.pathname) {
    return
  }
  window.scrollTo(0, saved.scrollY)
  content.focus({ preventScroll: true })
}

const saveNavClick = function (link) {
  try {
    sessionStorage.setItem(
      detailNavClickKey,
      JSON.stringify({ path: new URL(link.href).pathname, scrollY: window.scrollY })
    )
  } catch {}
}

const initDetailViewFocus = function () {
  const content = document.getElementById('record-detail-content')
  const sideNav = document.querySelector('.moj-side-navigation')
  if (!content || !sideNav) {
    return
  }

  scrollCurrentSectionIntoView(sideNav)
  restorePositionAfterNavClick(content)

  sideNav.addEventListener('click', function (event) {
    const link = event.target.closest('a')
    if (link && isPlainClick(event)) {
      saveNavClick(link)
    }
  })
}

export { initDetailViewFocus }
