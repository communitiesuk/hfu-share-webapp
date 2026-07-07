// Based on https://github.com/alphagov/pay-selfservice/blob/master/src/client-side/cookie-banner.js

const dayInMilliseconds = 24 * 60 * 60 * 1000
const yearInMilliseconds = 365 * dayInMilliseconds
const communitiesDomain = '.communities.gov.uk'

const getCookieDomain = function () {
  let cookieDomain = window.location.hostname
  if (cookieDomain.includes(communitiesDomain)) {
    // Cover dev, staging and production subdomains
    return communitiesDomain
  }
  // Likely to be localhost or 127.0.0.1
  return cookieDomain
}

const expireCookie = function (name) {
  let cookieString = name + '=null; path=/; domain=' + getCookieDomain()

  // Set expiry date to yesterday
  let date = new Date()
  date.setTime(date.getTime() - dayInMilliseconds)
  cookieString = cookieString + '; expires=' + date.toUTCString()

  document.cookie = cookieString
  return cookieString
}

const expireGoogleAnalyticsCookies = function () {
  // Expire the basic _ga cookie
  expireCookie('_ga')
  // Expire the _ga_ABCD1234 cookie
  let analyticsId = getAnalyticsId()
  const gaCookieWithId = '_ga_' + analyticsId.replace('G-', '')
  expireCookie(gaCookieWithId)
}

const setConsentCookie = function (consentValue) {
  let date = new Date()
  // Set expiry date to 1 year from now
  date.setTime(date.getTime() + yearInMilliseconds)
  const expires = '; expires=' + date.toUTCString()
  document.cookie = 'cookie_consent=' + consentValue + expires + '; path=/ ; SameSite=Strict; '

  // If consent is false, delete any GA cookies
  if (!consentValue) {
    expireGoogleAnalyticsCookies()
  }
}

const getConsentCookieValue = function () {
  const nameEQ = 'cookie_consent='
  const decodedCookie = decodeURIComponent(document.cookie)
  const ca = decodedCookie.split(';')
  for (let i = 0; i<ca.length; i++) {
    let c = ca[i]
    while (c.charAt(0) === ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(nameEQ) === 0) {
      return c.substring(nameEQ.length, c.length)
    }
  }

  return 'unknown'
}

const checkExistingConsent = function () {
  // First check for presence of consent cookie
  const consentCookieValue = getConsentCookieValue()
  if (consentCookieValue !== 'unknown') {
    return consentCookieValue
  }

  let cookieBanner = document.querySelector('#hfu-cookie-banner')
  // Then, check the data-consent-value property
  if (cookieBanner) {
    return document.querySelector('#hfu-cookie-banner').getAttribute('data-consent-value')
  }

  return 'unknown'
}

const getAnalyticsId = function () {
  let cookieBanner = document.querySelector('#hfu-cookie-banner')
  if (cookieBanner) {
    return cookieBanner.getAttribute('data-analytics-id')
  } else {
    // Try getting analytics ID from cookie settings form
    // (the cookie banner is not displayed on the cookie settings page)
    let cookieForm = document.querySelector('.cookie-settings-form')
    if (cookieForm) {
      return cookieForm.getAttribute('data-analytics-id')
    }
  }
}

const CookieBanner = function ($module) {
  this.$module = $module
}

CookieBanner.prototype.init = function () {
  this.$module.hideCookieMessage = this.hideCookieMessage.bind(this)
  this.$module.showConfirmationMessage = this.showConfirmationMessage.bind(this)
  this.$module.setCookieConsent = this.setCookieConsent.bind(this)

  this.$module.cookieBanner = document.querySelector('.govuk-cookie-banner__message')
  this.$module.cookieBannerConfirmationMessage = document.querySelector('.govuk-cookie-banner__confirmation_message')
  this.setupCookieMessage()
}

CookieBanner.prototype.setupCookieMessage = function () {
  this.$hideLink = this.$module.querySelector('#hide-cookie-message')
  if (this.$hideLink) {
    this.$hideLink.addEventListener('click', this.$module.hideCookieMessage)
  }

  this.$acceptCookiesLink = this.$module.querySelector('button[data-accept-cookies=true]')
  if (this.$acceptCookiesLink) {
    this.$acceptCookiesLink.addEventListener('click', () => this.$module.setCookieConsent(true))
  }

  this.$rejectCookiesLink = this.$module.querySelector('button[data-accept-cookies=false]')
  if (this.$rejectCookiesLink) {
    this.$rejectCookiesLink.addEventListener('click', () => this.$module.setCookieConsent(false))
  }

  this.showCookieMessage()
}

CookieBanner.prototype.showCookieMessage = function () {
  // Show the cookie banner if policy cookie not set
  const existingConsent = checkExistingConsent()

  if (this.$module) {
    if (existingConsent === 'unknown') {
      this.$module.style.display = 'block'
    } else {
      if (existingConsent === 'false') {
        // Ensure any GA cookies are removed
        expireGoogleAnalyticsCookies()
      }
      this.$module.style.display = 'none'
    }
  }
}

CookieBanner.prototype.hideCookieMessage = function (event) {
  if (this.$module) {
    this.$module.style.display = 'none'
  }

  if (event.target) {
    event.preventDefault()
  }
}

CookieBanner.prototype.setCookieConsent = function (analyticsConsent) {
  setConsentCookie(analyticsConsent)
  this.$module.showConfirmationMessage(analyticsConsent)
  this.$module.cookieBannerConfirmationMessage.focus()
}

CookieBanner.prototype.showConfirmationMessage = function (analyticsConsent) {
  this.$acceptedConfirmationMessage = document.querySelector('#accepted-confirmation')
  this.$rejectedConfirmationMessage = document.querySelector('#rejected-confirmation')

  // Show/hide accepted/rejected messages
  this.$rejectedConfirmationMessage.style.display = analyticsConsent ? 'none' : 'block'
  this.$acceptedConfirmationMessage.style.display = analyticsConsent ? 'block' : 'none'
  // Show confirmation message container
  this.$module.cookieBannerConfirmationMessage.style.display = 'block'
  // Hide consent div
  this.$module.cookieBanner.style.display = 'none'
}


const initCookieBanner = () => {
  const $cookieBanner = document.querySelector('.govuk-cookie-banner')
  if ($cookieBanner) {
    const cookieBanner = new CookieBanner($cookieBanner)
    cookieBanner.init()
    return cookieBanner
  }
}

initCookieBanner()
