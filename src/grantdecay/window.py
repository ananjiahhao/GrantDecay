"""The observation window, and refusing to conclude on a short window.

Absence of use inside a window is not proof that a permission is unneeded. A
permission might be exercised only at quarter close, during an incident, or on a
yearly audit. The honest guard against over-claiming is a minimum window: below
it, grantdecay refuses to label anything as unused and says so plainly.
