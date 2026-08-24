// Side navigation focus management for record detail pages.
// Clicking a side navigation link sets a sessionStorage flag that survives
// the full page load. The next page then moves focus to the tab content,
// so keyboard and screen reader users are not sent back to the top of the
// page, and the URL stays free of fragments.
const detailNavFocusFlag = 'detail_nav_clicked'

const initDetailNavFocus = function () {
  const content = document.getElementById('record-detail-content')
  const sideNav = document.querySelector('.moj-side-navigation')
  if (!content || !sideNav) {
    return
  }

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

initDetailNavFocus()
