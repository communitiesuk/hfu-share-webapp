// Moves focus to the record section content after a side navigation click,
// via a sessionStorage flag that survives the page load.
const detailNavFocusFlag = 'detail_nav_clicked'

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
  const content = document.getElementById('record-detail-content')
  const sideNav = document.querySelector('.moj-side-navigation')
  if (!content || !sideNav) {
    return
  }

  scrollCurrentSectionIntoView(sideNav)

  if (sessionStorage.getItem(detailNavFocusFlag)) {
    sessionStorage.removeItem(detailNavFocusFlag)
    content.focus()
  }

  sideNav.addEventListener('click', function (event) {
    if (event.target.closest('a')) {
      sessionStorage.setItem(detailNavFocusFlag, 'true')
    }
  })
}

export { initDetailViewFocus }
