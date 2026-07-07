const submitSettingsForm = function (event) {
    event.preventDefault()

    const formInputs = event.target.querySelectorAll('input[name=cookies-analytics]')
    let value = false

    // Retrieve the selected value from the form inputs
    for (let i = 0; i < formInputs.length; i++) {
      const input = formInputs[i]
      if (input.checked) {
        value = input.value === 'on'

        break
      }
    }

    // Set the analytics cookie preferences
    // If 'Off' option not checked, this function will also delete any existing Google Analytics cookies
    setConsentCookie(value)

    // Show settings confirmation message
    const $confirmationMessage = document.querySelector('.cookie-settings__confirmation')
    $confirmationMessage.style.display = 'block'
    $confirmationMessage.focus()
    // Hide the form
    const $cookieSettingsForm = document.querySelector('.cookie-settings__form-wrapper')
    $cookieSettingsForm.style.display = 'none'

    return false
  }

const setInitialFormValues = function () {
    const existingConsent = checkExistingConsent()
    if (existingConsent === 'unknown' || !existingConsent) {
        // Don't populate the form
        return
    }
    let radioButton
    if (existingConsent === 'true') {
        radioButton = document.querySelector('input[name=cookies-analytics][value=on]')
    } else {
        radioButton = document.querySelector('input[name=cookies-analytics][value=off]')
    }
    radioButton.checked = true
}

const initSettingsForm = () => {
  const $cookieSettingsForm = document.querySelector('.cookie-settings-form')
  if ($cookieSettingsForm) {
    $cookieSettingsForm.addEventListener('submit', submitSettingsForm)
  }
  // Hide cookie banner if on the page
  const $cookieBanner = document.querySelector('.govuk-cookie-banner')
  $cookieBanner.style.display = 'none'

  // Populate form with existing consent choice if present
  setInitialFormValues()

}

initSettingsForm()
