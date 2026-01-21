/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	var __webpack_modules__ = ({

/***/ "./static_src/sass/main.scss":
/*!***********************************!*\
  !*** ./static_src/sass/main.scss ***!
  \***********************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
// extracted by mini-css-extract-plugin


/***/ }),

/***/ "./static_src/javascript/components/header-search-panel.js":
/*!*****************************************************************!*\
  !*** ./static_src/javascript/components/header-search-panel.js ***!
  \*****************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./utils */ "./static_src/javascript/components/utils.js");


class HeaderSearch {
    static selector() {
        return '[data-toggle-search-panel]';
    }

    constructor(node) {
        this.searchToggleButton = node;

        this.searchDropdown = document.querySelector('[data-search-panel]');
        this.searchDropdownContent = document.querySelector(
            '[data-search-content]',
        );
        this.searchInput = this.searchDropdown.querySelector(
            '[data-search-input]',
        );
        this.navigationMenuItems = document.querySelectorAll(
            '[data-desktop-nav-item]',
        );

        this.bindEvents();
    }

    openSearch() {
        (0,_utils__WEBPACK_IMPORTED_MODULE_0__.showDropdownElement)(this.searchDropdown);

        // Make sure that the page is not scrollable.
        document.body.style.overflowY = 'hidden';

        // Focus on the input.
        this.searchInput.focus();
    }

    closeSearch() {
        (0,_utils__WEBPACK_IMPORTED_MODULE_0__.hideDropdownElement)(this.searchDropdown);

        // Set the page to be scrollable.
        document.body.style.overflowY = 'visible';
    }

    bindEvents() {
        this.searchToggleButton.addEventListener('click', (e) => {
            e.preventDefault();

            if (this.searchDropdown.classList.contains('invisible')) {
                this.openSearch();
            } else {
                this.closeSearch();
            }
        });

        this.searchDropdown.addEventListener('click', (e) => {
            // Close the dropdown if clicking anywhere else on the page
            if (!this.searchDropdownContent.contains(e.target)) {
                this.closeSearch();
            }
        });
    }
}

/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (HeaderSearch);


/***/ }),

/***/ "./static_src/javascript/components/mobile-menu.js":
/*!*********************************************************!*\
  !*** ./static_src/javascript/components/mobile-menu.js ***!
  \*********************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./utils */ "./static_src/javascript/components/utils.js");


class MobileMenu {
    static selector() {
        return '[data-mobile-menu-toggle]';
    }

    constructor(node) {
        this.node = node;
        this.body = document.querySelector('body');
        this.mobileMenu = document.querySelector('[data-mobile-menu-content]');
        this.headerLogo = document.querySelector('[data-header-logo]');

        this.bindEventListeners();
    }

    bindEventListeners() {
        this.node.addEventListener('click', () => {
            if (this.mobileMenu.classList.contains('invisible')) {
                this.open();
            } else {
                this.close();
            }
        });
    }

    open() {
        // Set the menu button to be a cross.
        this.node.classList.add('mobile-menu-is-open');
        this.headerLogo.classList.add('mobile-menu-is-open');
        this.node.setAttribute('aria-expanded', 'true');
        this.node.setAttribute('aria-label', 'close navigation menu');
        this.body.classList.add('no-scroll');

        // Make sure that the page is not scrollable. Only the drawer.
        document.body.style.overflowY = 'hidden';

        // Open the mobile menu. Mobile menu slides from the right.
        this.mobileMenu.classList.remove('invisible');
        this.mobileMenu.classList.remove('translate-x-full');
        this.mobileMenu.classList.add('translate-x-0');

        // Focus on the first link in the mobile menu.
        const firstItem = this.mobileMenu.querySelector('a');
        firstItem?.focus();
    }

    close() {
        // Set the cross button to be a menu button.
        this.node.classList.remove('mobile-menu-is-open');
        this.headerLogo.classList.remove('mobile-menu-is-open');
        this.node.setAttribute('aria-expanded', 'false');
        this.node.setAttribute('aria-label', 'Open navigation menu');
        this.body.classList.remove('no-scroll');

        // Set the page to be scrollable.
        document.body.style.overflowY = 'visible';

        // Close the mobile menu.
        this.mobileMenu.classList.add('invisible');
        this.mobileMenu.classList.add('translate-x-full');
        this.mobileMenu.classList.remove('translate-x-0');
    }
}

/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (MobileMenu);


/***/ }),

/***/ "./static_src/javascript/components/skip-link.js":
/*!*******************************************************!*\
  !*** ./static_src/javascript/components/skip-link.js ***!
  \*******************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
class SkipLink {
    static selector() {
        return '[data-skip-link]';
    }

    constructor(node) {
        this.skipLink = node;
        this.main = document.querySelector('main');

        if (this.skipLink && this.main) {
            this.skipLink.addEventListener('click', () => this.handleClick());
        }
    }

    handleClick() {
        this.main.setAttribute('tabindex', -1);
        this.main.addEventListener('blur', () => this.handleBlur());
        this.main.addEventListener('focusout', () => this.handleBlur());
        this.main.focus();
    }

    handleBlur() {
        this.main.removeAttribute('tabindex');
        this.main.removeEventListener('blur', this.handleBlur);
        this.main.removeEventListener('focusout', this.handleBlur);
    }
}

/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (SkipLink);


/***/ }),

/***/ "./static_src/javascript/components/theme-toggle.js":
/*!**********************************************************!*\
  !*** ./static_src/javascript/components/theme-toggle.js ***!
  \**********************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
class ThemeToggle {
    static selector() {
        return '[data-theme-toggle]';
    }

    constructor(node) {
        this.toggleSwitch = node;
        // Detect system preference if no stored theme
        this.currentTheme = localStorage.getItem('theme') ||
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');

        this.applyTheme(this.currentTheme);
        this.bindEvents();
    }

    bindEvents() {
        // Bind switchTheme to this instance
        this.toggleSwitch.addEventListener('change', (e) => this.switchTheme(e), false);
    }

    applyTheme(theme) {
        // Add transition class to prevent jarring changes
        document.documentElement.classList.add('theme-transitioning');

        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
            document.documentElement.classList.remove('light');
            this.toggleSwitch.checked = true;
        } else {
            document.documentElement.classList.add('light');
            document.documentElement.classList.remove('dark');
            this.toggleSwitch.checked = false;
        }

        // Remove transition class after transition completes
        setTimeout(() => {
            document.documentElement.classList.remove('theme-transitioning');
        }, 300);
    }

    switchTheme(e) {
        const theme = e.target.checked ? 'dark' : 'light';
        this.currentTheme = theme;
        localStorage.setItem('theme', theme);
        this.applyTheme(theme);
    }
}

/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (ThemeToggle);

/***/ }),

/***/ "./static_src/javascript/components/utils.js":
/*!***************************************************!*\
  !*** ./static_src/javascript/components/utils.js ***!
  \***************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   hideDropdownElement: () => (/* binding */ hideDropdownElement),
/* harmony export */   isMobileOperatingSystem: () => (/* binding */ isMobileOperatingSystem),
/* harmony export */   showDropdownElement: () => (/* binding */ showDropdownElement)
/* harmony export */ });
/**
 * Hides a dropdown element, used in desktop navigation dropdowns and the search dropdown.
 */
const hideDropdownElement = (element) => {
    element.classList.add('invisible');
    element.classList.add('-translate-y-2');
    element.classList.remove('translate-y-0');
};

/**
 * Shows a dropdown element, used in desktop navigation dropdowns and the search dropdown.
 */
const showDropdownElement = (element) => {
    element.classList.remove('invisible');
    element.classList.remove('-translate-y-2');
    element.classList.add('translate-y-0');
};

/**
 * Determine if the client is using a mobile operating system based off
 * regex matching OS names and the client's user agent.
 * Returns true if user agent matches 'iOS', 'Android' or 'Windows Phone'.
 *
 * @returns {boolean}
 */
const isMobileOperatingSystem = () => {
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;

    // Windows Phone must come first because its UA also contains "Android"
    if (/windows phone/i.test(userAgent)) {
        return true;
    }

    if (/android/i.test(userAgent)) {
        return true;
    }

    // iOS detection from: http://stackoverflow.com/a/9039885/177710
    if (/iPad|iPhone|iPod/.test(userAgent) && !window.MSStream) {
        return true;
    }

    return false;
};


/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId](module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/define property getters */
/******/ 	(() => {
/******/ 		// define getter functions for harmony exports
/******/ 		__webpack_require__.d = (exports, definition) => {
/******/ 			for(var key in definition) {
/******/ 				if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 					Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 				}
/******/ 			}
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/hasOwnProperty shorthand */
/******/ 	(() => {
/******/ 		__webpack_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/make namespace object */
/******/ 	(() => {
/******/ 		// define __esModule on exports
/******/ 		__webpack_require__.r = (exports) => {
/******/ 			if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 				Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 			}
/******/ 			Object.defineProperty(exports, '__esModule', { value: true });
/******/ 		};
/******/ 	})();
/******/ 	
/************************************************************************/
var __webpack_exports__ = {};
// This entry need to be wrapped in an IIFE because it need to be isolated against other modules in the chunk.
(() => {
/*!***************************************!*\
  !*** ./static_src/javascript/main.js ***!
  \***************************************/
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _components_theme_toggle__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./components/theme-toggle */ "./static_src/javascript/components/theme-toggle.js");
/* harmony import */ var _components_header_search_panel__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./components/header-search-panel */ "./static_src/javascript/components/header-search-panel.js");
/* harmony import */ var _components_mobile_menu__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./components/mobile-menu */ "./static_src/javascript/components/mobile-menu.js");
/* harmony import */ var _components_skip_link__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./components/skip-link */ "./static_src/javascript/components/skip-link.js");
/* harmony import */ var _sass_main_scss__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../sass/main.scss */ "./static_src/sass/main.scss");








function initComponent(ComponentClass) {
    const items = document.querySelectorAll(ComponentClass.selector());
    items.forEach((item) => new ComponentClass(item));
}

document.addEventListener('DOMContentLoaded', () => {
    initComponent(_components_theme_toggle__WEBPACK_IMPORTED_MODULE_0__["default"]);
    initComponent(_components_theme_toggle__WEBPACK_IMPORTED_MODULE_0__["default"]);
    initComponent(_components_skip_link__WEBPACK_IMPORTED_MODULE_3__["default"]);
    initComponent(_components_header_search_panel__WEBPACK_IMPORTED_MODULE_1__["default"]);
    initComponent(_components_mobile_menu__WEBPACK_IMPORTED_MODULE_2__["default"]);
});

})();

/******/ })()
;
//# sourceMappingURL=data:application/json;charset=utf-8;base64,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dGFydGVyLWtpdC8uL3N0YXRpY19zcmMvc2Fzcy9tYWluLnNjc3M/YWMzYSIsIndlYnBhY2s6Ly93YWd0YWlsLXN0YXJ0ZXIta2l0Ly4vc3RhdGljX3NyYy9qYXZhc2NyaXB0L2NvbXBvbmVudHMvaGVhZGVyLXNlYXJjaC1wYW5lbC5qcyIsIndlYnBhY2s6Ly93YWd0YWlsLXN0YXJ0ZXIta2l0Ly4vc3RhdGljX3NyYy9qYXZhc2NyaXB0L2NvbXBvbmVudHMvbW9iaWxlLW1lbnUuanMiLCJ3ZWJwYWNrOi8vd2FndGFpbC1zdGFydGVyLWtpdC8uL3N0YXRpY19zcmMvamF2YXNjcmlwdC9jb21wb25lbnRzL3NraXAtbGluay5qcyIsIndlYnBhY2s6Ly93YWd0YWlsLXN0YXJ0ZXIta2l0Ly4vc3RhdGljX3NyYy9qYXZhc2NyaXB0L2NvbXBvbmVudHMvdGhlbWUtdG9nZ2xlLmpzIiwid2VicGFjazovL3dhZ3RhaWwtc3RhcnRlci1raXQvLi9zdGF0aWNfc3JjL2phdmFzY3JpcHQvY29tcG9uZW50cy91dGlscy5qcyIsIndlYnBhY2s6Ly93YWd0YWlsLXN0YXJ0ZXIta2l0L3dlYnBhY2svYm9vdHN0cmFwIiwid2VicGFjazovL3dhZ3RhaWwtc3RhcnRlci1raXQvd2VicGFjay9ydW50aW1lL2RlZmluZSBwcm9wZXJ0eSBnZXR0ZXJzIiwid2VicGFjazovL3dhZ3RhaWwtc3RhcnRlci1raXQvd2VicGFjay9ydW50aW1lL2hhc093blByb3BlcnR5IHNob3J0aGFuZCIsIndlYnBhY2s6Ly93YWd0YWlsLXN0YXJ0ZXIta2l0L3dlYnBhY2svcnVudGltZS9tYWtlIG5hbWVzcGFjZSBvYmplY3QiLCJ3ZWJwYWNrOi8vd2FndGFpbC1zdGFydGVyLWtpdC8uL3N0YXRpY19zcmMvamF2YXNjcmlwdC9tYWluLmpzIl0sInNvdXJjZXNDb250ZW50IjpbIi8vIGV4dHJhY3RlZCBieSBtaW5pLWNzcy1leHRyYWN0LXBsdWdpblxuZXhwb3J0IHt9OyIsImltcG9ydCB7IGhpZGVEcm9wZG93bkVsZW1lbnQsIHNob3dEcm9wZG93bkVsZW1lbnQgfSBmcm9tICcuL3V0aWxzJztcblxuY2xhc3MgSGVhZGVyU2VhcmNoIHtcbiAgICBzdGF0aWMgc2VsZWN0b3IoKSB7XG4gICAgICAgIHJldHVybiAnW2RhdGEtdG9nZ2xlLXNlYXJjaC1wYW5lbF0nO1xuICAgIH1cblxuICAgIGNvbnN0cnVjdG9yKG5vZGUpIHtcbiAgICAgICAgdGhpcy5zZWFyY2hUb2dnbGVCdXR0b24gPSBub2RlO1xuXG4gICAgICAgIHRoaXMuc2VhcmNoRHJvcGRvd24gPSBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKCdbZGF0YS1zZWFyY2gtcGFuZWxdJyk7XG4gICAgICAgIHRoaXMuc2VhcmNoRHJvcGRvd25Db250ZW50ID0gZG9jdW1lbnQucXVlcnlTZWxlY3RvcihcbiAgICAgICAgICAgICdbZGF0YS1zZWFyY2gtY29udGVudF0nLFxuICAgICAgICApO1xuICAgICAgICB0aGlzLnNlYXJjaElucHV0ID0gdGhpcy5zZWFyY2hEcm9wZG93bi5xdWVyeVNlbGVjdG9yKFxuICAgICAgICAgICAgJ1tkYXRhLXNlYXJjaC1pbnB1dF0nLFxuICAgICAgICApO1xuICAgICAgICB0aGlzLm5hdmlnYXRpb25NZW51SXRlbXMgPSBkb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxsKFxuICAgICAgICAgICAgJ1tkYXRhLWRlc2t0b3AtbmF2LWl0ZW1dJyxcbiAgICAgICAgKTtcblxuICAgICAgICB0aGlzLmJpbmRFdmVudHMoKTtcbiAgICB9XG5cbiAgICBvcGVuU2VhcmNoKCkge1xuICAgICAgICBzaG93RHJvcGRvd25FbGVtZW50KHRoaXMuc2VhcmNoRHJvcGRvd24pO1xuXG4gICAgICAgIC8vIE1ha2Ugc3VyZSB0aGF0IHRoZSBwYWdlIGlzIG5vdCBzY3JvbGxhYmxlLlxuICAgICAgICBkb2N1bWVudC5ib2R5LnN0eWxlLm92ZXJmbG93WSA9ICdoaWRkZW4nO1xuXG4gICAgICAgIC8vIEZvY3VzIG9uIHRoZSBpbnB1dC5cbiAgICAgICAgdGhpcy5zZWFyY2hJbnB1dC5mb2N1cygpO1xuICAgIH1cblxuICAgIGNsb3NlU2VhcmNoKCkge1xuICAgICAgICBoaWRlRHJvcGRvd25FbGVtZW50KHRoaXMuc2VhcmNoRHJvcGRvd24pO1xuXG4gICAgICAgIC8vIFNldCB0aGUgcGFnZSB0byBiZSBzY3JvbGxhYmxlLlxuICAgICAgICBkb2N1bWVudC5ib2R5LnN0eWxlLm92ZXJmbG93WSA9ICd2aXNpYmxlJztcbiAgICB9XG5cbiAgICBiaW5kRXZlbnRzKCkge1xuICAgICAgICB0aGlzLnNlYXJjaFRvZ2dsZUJ1dHRvbi5hZGRFdmVudExpc3RlbmVyKCdjbGljaycsIChlKSA9PiB7XG4gICAgICAgICAgICBlLnByZXZlbnREZWZhdWx0KCk7XG5cbiAgICAgICAgICAgIGlmICh0aGlzLnNlYXJjaERyb3Bkb3duLmNsYXNzTGlzdC5jb250YWlucygnaW52aXNpYmxlJykpIHtcbiAgICAgICAgICAgICAgICB0aGlzLm9wZW5TZWFyY2goKTtcbiAgICAgICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgICAgICAgdGhpcy5jbG9zZVNlYXJjaCgpO1xuICAgICAgICAgICAgfVxuICAgICAgICB9KTtcblxuICAgICAgICB0aGlzLnNlYXJjaERyb3Bkb3duLmFkZEV2ZW50TGlzdGVuZXIoJ2NsaWNrJywgKGUpID0+IHtcbiAgICAgICAgICAgIC8vIENsb3NlIHRoZSBkcm9wZG93biBpZiBjbGlja2luZyBhbnl3aGVyZSBlbHNlIG9uIHRoZSBwYWdlXG4gICAgICAgICAgICBpZiAoIXRoaXMuc2VhcmNoRHJvcGRvd25Db250ZW50LmNvbnRhaW5zKGUudGFyZ2V0KSkge1xuICAgICAgICAgICAgICAgIHRoaXMuY2xvc2VTZWFyY2goKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgfSk7XG4gICAgfVxufVxuXG5leHBvcnQgZGVmYXVsdCBIZWFkZXJTZWFyY2g7XG4iLCJpbXBvcnQgeyBoaWRlRHJvcGRvd25FbGVtZW50IH0gZnJvbSAnLi91dGlscyc7XG5cbmNsYXNzIE1vYmlsZU1lbnUge1xuICAgIHN0YXRpYyBzZWxlY3RvcigpIHtcbiAgICAgICAgcmV0dXJuICdbZGF0YS1tb2JpbGUtbWVudS10b2dnbGVdJztcbiAgICB9XG5cbiAgICBjb25zdHJ1Y3Rvcihub2RlKSB7XG4gICAgICAgIHRoaXMubm9kZSA9IG5vZGU7XG4gICAgICAgIHRoaXMuYm9keSA9IGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3IoJ2JvZHknKTtcbiAgICAgICAgdGhpcy5tb2JpbGVNZW51ID0gZG9jdW1lbnQucXVlcnlTZWxlY3RvcignW2RhdGEtbW9iaWxlLW1lbnUtY29udGVudF0nKTtcbiAgICAgICAgdGhpcy5oZWFkZXJMb2dvID0gZG9jdW1lbnQucXVlcnlTZWxlY3RvcignW2RhdGEtaGVhZGVyLWxvZ29dJyk7XG5cbiAgICAgICAgdGhpcy5iaW5kRXZlbnRMaXN0ZW5lcnMoKTtcbiAgICB9XG5cbiAgICBiaW5kRXZlbnRMaXN0ZW5lcnMoKSB7XG4gICAgICAgIHRoaXMubm9kZS5hZGRFdmVudExpc3RlbmVyKCdjbGljaycsICgpID0+IHtcbiAgICAgICAgICAgIGlmICh0aGlzLm1vYmlsZU1lbnUuY2xhc3NMaXN0LmNvbnRhaW5zKCdpbnZpc2libGUnKSkge1xuICAgICAgICAgICAgICAgIHRoaXMub3BlbigpO1xuICAgICAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICAgICAgICB0aGlzLmNsb3NlKCk7XG4gICAgICAgICAgICB9XG4gICAgICAgIH0pO1xuICAgIH1cblxuICAgIG9wZW4oKSB7XG4gICAgICAgIC8vIFNldCB0aGUgbWVudSBidXR0b24gdG8gYmUgYSBjcm9zcy5cbiAgICAgICAgdGhpcy5ub2RlLmNsYXNzTGlzdC5hZGQoJ21vYmlsZS1tZW51LWlzLW9wZW4nKTtcbiAgICAgICAgdGhpcy5oZWFkZXJMb2dvLmNsYXNzTGlzdC5hZGQoJ21vYmlsZS1tZW51LWlzLW9wZW4nKTtcbiAgICAgICAgdGhpcy5ub2RlLnNldEF0dHJpYnV0ZSgnYXJpYS1leHBhbmRlZCcsICd0cnVlJyk7XG4gICAgICAgIHRoaXMubm9kZS5zZXRBdHRyaWJ1dGUoJ2FyaWEtbGFiZWwnLCAnY2xvc2UgbmF2aWdhdGlvbiBtZW51Jyk7XG4gICAgICAgIHRoaXMuYm9keS5jbGFzc0xpc3QuYWRkKCduby1zY3JvbGwnKTtcblxuICAgICAgICAvLyBNYWtlIHN1cmUgdGhhdCB0aGUgcGFnZSBpcyBub3Qgc2Nyb2xsYWJsZS4gT25seSB0aGUgZHJhd2VyLlxuICAgICAgICBkb2N1bWVudC5ib2R5LnN0eWxlLm92ZXJmbG93WSA9ICdoaWRkZW4nO1xuXG4gICAgICAgIC8vIE9wZW4gdGhlIG1vYmlsZSBtZW51LiBNb2JpbGUgbWVudSBzbGlkZXMgZnJvbSB0aGUgcmlnaHQuXG4gICAgICAgIHRoaXMubW9iaWxlTWVudS5jbGFzc0xpc3QucmVtb3ZlKCdpbnZpc2libGUnKTtcbiAgICAgICAgdGhpcy5tb2JpbGVNZW51LmNsYXNzTGlzdC5yZW1vdmUoJ3RyYW5zbGF0ZS14LWZ1bGwnKTtcbiAgICAgICAgdGhpcy5tb2JpbGVNZW51LmNsYXNzTGlzdC5hZGQoJ3RyYW5zbGF0ZS14LTAnKTtcblxuICAgICAgICAvLyBGb2N1cyBvbiB0aGUgZmlyc3QgbGluayBpbiB0aGUgbW9iaWxlIG1lbnUuXG4gICAgICAgIGNvbnN0IGZpcnN0SXRlbSA9IHRoaXMubW9iaWxlTWVudS5xdWVyeVNlbGVjdG9yKCdhJyk7XG4gICAgICAgIGZpcnN0SXRlbT8uZm9jdXMoKTtcbiAgICB9XG5cbiAgICBjbG9zZSgpIHtcbiAgICAgICAgLy8gU2V0IHRoZSBjcm9zcyBidXR0b24gdG8gYmUgYSBtZW51IGJ1dHRvbi5cbiAgICAgICAgdGhpcy5ub2RlLmNsYXNzTGlzdC5yZW1vdmUoJ21vYmlsZS1tZW51LWlzLW9wZW4nKTtcbiAgICAgICAgdGhpcy5oZWFkZXJMb2dvLmNsYXNzTGlzdC5yZW1vdmUoJ21vYmlsZS1tZW51LWlzLW9wZW4nKTtcbiAgICAgICAgdGhpcy5ub2RlLnNldEF0dHJpYnV0ZSgnYXJpYS1leHBhbmRlZCcsICdmYWxzZScpO1xuICAgICAgICB0aGlzLm5vZGUuc2V0QXR0cmlidXRlKCdhcmlhLWxhYmVsJywgJ09wZW4gbmF2aWdhdGlvbiBtZW51Jyk7XG4gICAgICAgIHRoaXMuYm9keS5jbGFzc0xpc3QucmVtb3ZlKCduby1zY3JvbGwnKTtcblxuICAgICAgICAvLyBTZXQgdGhlIHBhZ2UgdG8gYmUgc2Nyb2xsYWJsZS5cbiAgICAgICAgZG9jdW1lbnQuYm9keS5zdHlsZS5vdmVyZmxvd1kgPSAndmlzaWJsZSc7XG5cbiAgICAgICAgLy8gQ2xvc2UgdGhlIG1vYmlsZSBtZW51LlxuICAgICAgICB0aGlzLm1vYmlsZU1lbnUuY2xhc3NMaXN0LmFkZCgnaW52aXNpYmxlJyk7XG4gICAgICAgIHRoaXMubW9iaWxlTWVudS5jbGFzc0xpc3QuYWRkKCd0cmFuc2xhdGUteC1mdWxsJyk7XG4gICAgICAgIHRoaXMubW9iaWxlTWVudS5jbGFzc0xpc3QucmVtb3ZlKCd0cmFuc2xhdGUteC0wJyk7XG4gICAgfVxufVxuXG5leHBvcnQgZGVmYXVsdCBNb2JpbGVNZW51O1xuIiwiY2xhc3MgU2tpcExpbmsge1xuICAgIHN0YXRpYyBzZWxlY3RvcigpIHtcbiAgICAgICAgcmV0dXJuICdbZGF0YS1za2lwLWxpbmtdJztcbiAgICB9XG5cbiAgICBjb25zdHJ1Y3Rvcihub2RlKSB7XG4gICAgICAgIHRoaXMuc2tpcExpbmsgPSBub2RlO1xuICAgICAgICB0aGlzLm1haW4gPSBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKCdtYWluJyk7XG5cbiAgICAgICAgaWYgKHRoaXMuc2tpcExpbmsgJiYgdGhpcy5tYWluKSB7XG4gICAgICAgICAgICB0aGlzLnNraXBMaW5rLmFkZEV2ZW50TGlzdGVuZXIoJ2NsaWNrJywgKCkgPT4gdGhpcy5oYW5kbGVDbGljaygpKTtcbiAgICAgICAgfVxuICAgIH1cblxuICAgIGhhbmRsZUNsaWNrKCkge1xuICAgICAgICB0aGlzLm1haW4uc2V0QXR0cmlidXRlKCd0YWJpbmRleCcsIC0xKTtcbiAgICAgICAgdGhpcy5tYWluLmFkZEV2ZW50TGlzdGVuZXIoJ2JsdXInLCAoKSA9PiB0aGlzLmhhbmRsZUJsdXIoKSk7XG4gICAgICAgIHRoaXMubWFpbi5hZGRFdmVudExpc3RlbmVyKCdmb2N1c291dCcsICgpID0+IHRoaXMuaGFuZGxlQmx1cigpKTtcbiAgICAgICAgdGhpcy5tYWluLmZvY3VzKCk7XG4gICAgfVxuXG4gICAgaGFuZGxlQmx1cigpIHtcbiAgICAgICAgdGhpcy5tYWluLnJlbW92ZUF0dHJpYnV0ZSgndGFiaW5kZXgnKTtcbiAgICAgICAgdGhpcy5tYWluLnJlbW92ZUV2ZW50TGlzdGVuZXIoJ2JsdXInLCB0aGlzLmhhbmRsZUJsdXIpO1xuICAgICAgICB0aGlzLm1haW4ucmVtb3ZlRXZlbnRMaXN0ZW5lcignZm9jdXNvdXQnLCB0aGlzLmhhbmRsZUJsdXIpO1xuICAgIH1cbn1cblxuZXhwb3J0IGRlZmF1bHQgU2tpcExpbms7XG4iLCJjbGFzcyBUaGVtZVRvZ2dsZSB7XG4gICAgc3RhdGljIHNlbGVjdG9yKCkge1xuICAgICAgICByZXR1cm4gJ1tkYXRhLXRoZW1lLXRvZ2dsZV0nO1xuICAgIH1cblxuICAgIGNvbnN0cnVjdG9yKG5vZGUpIHtcbiAgICAgICAgdGhpcy50b2dnbGVTd2l0Y2ggPSBub2RlO1xuICAgICAgICAvLyBEZXRlY3Qgc3lzdGVtIHByZWZlcmVuY2UgaWYgbm8gc3RvcmVkIHRoZW1lXG4gICAgICAgIHRoaXMuY3VycmVudFRoZW1lID0gbG9jYWxTdG9yYWdlLmdldEl0ZW0oJ3RoZW1lJykgfHxcbiAgICAgICAgICAgICh3aW5kb3cubWF0Y2hNZWRpYSgnKHByZWZlcnMtY29sb3Itc2NoZW1lOiBkYXJrKScpLm1hdGNoZXMgPyAnZGFyaycgOiAnbGlnaHQnKTtcblxuICAgICAgICB0aGlzLmFwcGx5VGhlbWUodGhpcy5jdXJyZW50VGhlbWUpO1xuICAgICAgICB0aGlzLmJpbmRFdmVudHMoKTtcbiAgICB9XG5cbiAgICBiaW5kRXZlbnRzKCkge1xuICAgICAgICAvLyBCaW5kIHN3aXRjaFRoZW1lIHRvIHRoaXMgaW5zdGFuY2VcbiAgICAgICAgdGhpcy50b2dnbGVTd2l0Y2guYWRkRXZlbnRMaXN0ZW5lcignY2hhbmdlJywgKGUpID0+IHRoaXMuc3dpdGNoVGhlbWUoZSksIGZhbHNlKTtcbiAgICB9XG5cbiAgICBhcHBseVRoZW1lKHRoZW1lKSB7XG4gICAgICAgIC8vIEFkZCB0cmFuc2l0aW9uIGNsYXNzIHRvIHByZXZlbnQgamFycmluZyBjaGFuZ2VzXG4gICAgICAgIGRvY3VtZW50LmRvY3VtZW50RWxlbWVudC5jbGFzc0xpc3QuYWRkKCd0aGVtZS10cmFuc2l0aW9uaW5nJyk7XG5cbiAgICAgICAgaWYgKHRoZW1lID09PSAnZGFyaycpIHtcbiAgICAgICAgICAgIGRvY3VtZW50LmRvY3VtZW50RWxlbWVudC5jbGFzc0xpc3QuYWRkKCdkYXJrJyk7XG4gICAgICAgICAgICBkb2N1bWVudC5kb2N1bWVudEVsZW1lbnQuY2xhc3NMaXN0LnJlbW92ZSgnbGlnaHQnKTtcbiAgICAgICAgICAgIHRoaXMudG9nZ2xlU3dpdGNoLmNoZWNrZWQgPSB0cnVlO1xuICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgZG9jdW1lbnQuZG9jdW1lbnRFbGVtZW50LmNsYXNzTGlzdC5hZGQoJ2xpZ2h0Jyk7XG4gICAgICAgICAgICBkb2N1bWVudC5kb2N1bWVudEVsZW1lbnQuY2xhc3NMaXN0LnJlbW92ZSgnZGFyaycpO1xuICAgICAgICAgICAgdGhpcy50b2dnbGVTd2l0Y2guY2hlY2tlZCA9IGZhbHNlO1xuICAgICAgICB9XG5cbiAgICAgICAgLy8gUmVtb3ZlIHRyYW5zaXRpb24gY2xhc3MgYWZ0ZXIgdHJhbnNpdGlvbiBjb21wbGV0ZXNcbiAgICAgICAgc2V0VGltZW91dCgoKSA9PiB7XG4gICAgICAgICAgICBkb2N1bWVudC5kb2N1bWVudEVsZW1lbnQuY2xhc3NMaXN0LnJlbW92ZSgndGhlbWUtdHJhbnNpdGlvbmluZycpO1xuICAgICAgICB9LCAzMDApO1xuICAgIH1cblxuICAgIHN3aXRjaFRoZW1lKGUpIHtcbiAgICAgICAgY29uc3QgdGhlbWUgPSBlLnRhcmdldC5jaGVja2VkID8gJ2RhcmsnIDogJ2xpZ2h0JztcbiAgICAgICAgdGhpcy5jdXJyZW50VGhlbWUgPSB0aGVtZTtcbiAgICAgICAgbG9jYWxTdG9yYWdlLnNldEl0ZW0oJ3RoZW1lJywgdGhlbWUpO1xuICAgICAgICB0aGlzLmFwcGx5VGhlbWUodGhlbWUpO1xuICAgIH1cbn1cblxuZXhwb3J0IGRlZmF1bHQgVGhlbWVUb2dnbGU7IiwiLyoqXG4gKiBIaWRlcyBhIGRyb3Bkb3duIGVsZW1lbnQsIHVzZWQgaW4gZGVza3RvcCBuYXZpZ2F0aW9uIGRyb3Bkb3ducyBhbmQgdGhlIHNlYXJjaCBkcm9wZG93bi5cbiAqL1xuZXhwb3J0IGNvbnN0IGhpZGVEcm9wZG93bkVsZW1lbnQgPSAoZWxlbWVudCkgPT4ge1xuICAgIGVsZW1lbnQuY2xhc3NMaXN0LmFkZCgnaW52aXNpYmxlJyk7XG4gICAgZWxlbWVudC5jbGFzc0xpc3QuYWRkKCctdHJhbnNsYXRlLXktMicpO1xuICAgIGVsZW1lbnQuY2xhc3NMaXN0LnJlbW92ZSgndHJhbnNsYXRlLXktMCcpO1xufTtcblxuLyoqXG4gKiBTaG93cyBhIGRyb3Bkb3duIGVsZW1lbnQsIHVzZWQgaW4gZGVza3RvcCBuYXZpZ2F0aW9uIGRyb3Bkb3ducyBhbmQgdGhlIHNlYXJjaCBkcm9wZG93bi5cbiAqL1xuZXhwb3J0IGNvbnN0IHNob3dEcm9wZG93bkVsZW1lbnQgPSAoZWxlbWVudCkgPT4ge1xuICAgIGVsZW1lbnQuY2xhc3NMaXN0LnJlbW92ZSgnaW52aXNpYmxlJyk7XG4gICAgZWxlbWVudC5jbGFzc0xpc3QucmVtb3ZlKCctdHJhbnNsYXRlLXktMicpO1xuICAgIGVsZW1lbnQuY2xhc3NMaXN0LmFkZCgndHJhbnNsYXRlLXktMCcpO1xufTtcblxuLyoqXG4gKiBEZXRlcm1pbmUgaWYgdGhlIGNsaWVudCBpcyB1c2luZyBhIG1vYmlsZSBvcGVyYXRpbmcgc3lzdGVtIGJhc2VkIG9mZlxuICogcmVnZXggbWF0Y2hpbmcgT1MgbmFtZXMgYW5kIHRoZSBjbGllbnQncyB1c2VyIGFnZW50LlxuICogUmV0dXJucyB0cnVlIGlmIHVzZXIgYWdlbnQgbWF0Y2hlcyAnaU9TJywgJ0FuZHJvaWQnIG9yICdXaW5kb3dzIFBob25lJy5cbiAqXG4gKiBAcmV0dXJucyB7Ym9vbGVhbn1cbiAqL1xuZXhwb3J0IGNvbnN0IGlzTW9iaWxlT3BlcmF0aW5nU3lzdGVtID0gKCkgPT4ge1xuICAgIGNvbnN0IHVzZXJBZ2VudCA9IG5hdmlnYXRvci51c2VyQWdlbnQgfHwgbmF2aWdhdG9yLnZlbmRvciB8fCB3aW5kb3cub3BlcmE7XG5cbiAgICAvLyBXaW5kb3dzIFBob25lIG11c3QgY29tZSBmaXJzdCBiZWNhdXNlIGl0cyBVQSBhbHNvIGNvbnRhaW5zIFwiQW5kcm9pZFwiXG4gICAgaWYgKC93aW5kb3dzIHBob25lL2kudGVzdCh1c2VyQWdlbnQpKSB7XG4gICAgICAgIHJldHVybiB0cnVlO1xuICAgIH1cblxuICAgIGlmICgvYW5kcm9pZC9pLnRlc3QodXNlckFnZW50KSkge1xuICAgICAgICByZXR1cm4gdHJ1ZTtcbiAgICB9XG5cbiAgICAvLyBpT1MgZGV0ZWN0aW9uIGZyb206IGh0dHA6Ly9zdGFja292ZXJmbG93LmNvbS9hLzkwMzk4ODUvMTc3NzEwXG4gICAgaWYgKC9pUGFkfGlQaG9uZXxpUG9kLy50ZXN0KHVzZXJBZ2VudCkgJiYgIXdpbmRvdy5NU1N0cmVhbSkge1xuICAgICAgICByZXR1cm4gdHJ1ZTtcbiAgICB9XG5cbiAgICByZXR1cm4gZmFsc2U7XG59O1xuIiwiLy8gVGhlIG1vZHVsZSBjYWNoZVxudmFyIF9fd2VicGFja19tb2R1bGVfY2FjaGVfXyA9IHt9O1xuXG4vLyBUaGUgcmVxdWlyZSBmdW5jdGlvblxuZnVuY3Rpb24gX193ZWJwYWNrX3JlcXVpcmVfXyhtb2R1bGVJZCkge1xuXHQvLyBDaGVjayBpZiBtb2R1bGUgaXMgaW4gY2FjaGVcblx0dmFyIGNhY2hlZE1vZHVsZSA9IF9fd2VicGFja19tb2R1bGVfY2FjaGVfX1ttb2R1bGVJZF07XG5cdGlmIChjYWNoZWRNb2R1bGUgIT09IHVuZGVmaW5lZCkge1xuXHRcdHJldHVybiBjYWNoZWRNb2R1bGUuZXhwb3J0cztcblx0fVxuXHQvLyBDcmVhdGUgYSBuZXcgbW9kdWxlIChhbmQgcHV0IGl0IGludG8gdGhlIGNhY2hlKVxuXHR2YXIgbW9kdWxlID0gX193ZWJwYWNrX21vZHVsZV9jYWNoZV9fW21vZHVsZUlkXSA9IHtcblx0XHQvLyBubyBtb2R1bGUuaWQgbmVlZGVkXG5cdFx0Ly8gbm8gbW9kdWxlLmxvYWRlZCBuZWVkZWRcblx0XHRleHBvcnRzOiB7fVxuXHR9O1xuXG5cdC8vIEV4ZWN1dGUgdGhlIG1vZHVsZSBmdW5jdGlvblxuXHRfX3dlYnBhY2tfbW9kdWxlc19fW21vZHVsZUlkXShtb2R1bGUsIG1vZHVsZS5leHBvcnRzLCBfX3dlYnBhY2tfcmVxdWlyZV9fKTtcblxuXHQvLyBSZXR1cm4gdGhlIGV4cG9ydHMgb2YgdGhlIG1vZHVsZVxuXHRyZXR1cm4gbW9kdWxlLmV4cG9ydHM7XG59XG5cbiIsIi8vIGRlZmluZSBnZXR0ZXIgZnVuY3Rpb25zIGZvciBoYXJtb255IGV4cG9ydHNcbl9fd2VicGFja19yZXF1aXJlX18uZCA9IChleHBvcnRzLCBkZWZpbml0aW9uKSA9PiB7XG5cdGZvcih2YXIga2V5IGluIGRlZmluaXRpb24pIHtcblx0XHRpZihfX3dlYnBhY2tfcmVxdWlyZV9fLm8oZGVmaW5pdGlvbiwga2V5KSAmJiAhX193ZWJwYWNrX3JlcXVpcmVfXy5vKGV4cG9ydHMsIGtleSkpIHtcblx0XHRcdE9iamVjdC5kZWZpbmVQcm9wZXJ0eShleHBvcnRzLCBrZXksIHsgZW51bWVyYWJsZTogdHJ1ZSwgZ2V0OiBkZWZpbml0aW9uW2tleV0gfSk7XG5cdFx0fVxuXHR9XG59OyIsIl9fd2VicGFja19yZXF1aXJlX18ubyA9IChvYmosIHByb3ApID0+IChPYmplY3QucHJvdG90eXBlLmhhc093blByb3BlcnR5LmNhbGwob2JqLCBwcm9wKSkiLCIvLyBkZWZpbmUgX19lc01vZHVsZSBvbiBleHBvcnRzXG5fX3dlYnBhY2tfcmVxdWlyZV9fLnIgPSAoZXhwb3J0cykgPT4ge1xuXHRpZih0eXBlb2YgU3ltYm9sICE9PSAndW5kZWZpbmVkJyAmJiBTeW1ib2wudG9TdHJpbmdUYWcpIHtcblx0XHRPYmplY3QuZGVmaW5lUHJvcGVydHkoZXhwb3J0cywgU3ltYm9sLnRvU3RyaW5nVGFnLCB7IHZhbHVlOiAnTW9kdWxlJyB9KTtcblx0fVxuXHRPYmplY3QuZGVmaW5lUHJvcGVydHkoZXhwb3J0cywgJ19fZXNNb2R1bGUnLCB7IHZhbHVlOiB0cnVlIH0pO1xufTsiLCJpbXBvcnQgVGhlbWVUb2dnbGUgZnJvbSBcIi4vY29tcG9uZW50cy90aGVtZS10b2dnbGVcIjtcbmltcG9ydCBIZWFkZXJTZWFyY2hQYW5lbCBmcm9tIFwiLi9jb21wb25lbnRzL2hlYWRlci1zZWFyY2gtcGFuZWxcIjtcbmltcG9ydCBNb2JpbGVNZW51IGZyb20gXCIuL2NvbXBvbmVudHMvbW9iaWxlLW1lbnVcIjtcbmltcG9ydCBTa2lwTGluayBmcm9tICcuL2NvbXBvbmVudHMvc2tpcC1saW5rJztcblxuaW1wb3J0ICcuLi9zYXNzL21haW4uc2Nzcyc7XG5cblxuZnVuY3Rpb24gaW5pdENvbXBvbmVudChDb21wb25lbnRDbGFzcykge1xuICAgIGNvbnN0IGl0ZW1zID0gZG9jdW1lbnQucXVlcnlTZWxlY3RvckFsbChDb21wb25lbnRDbGFzcy5zZWxlY3RvcigpKTtcbiAgICBpdGVtcy5mb3JFYWNoKChpdGVtKSA9PiBuZXcgQ29tcG9uZW50Q2xhc3MoaXRlbSkpO1xufVxuXG5kb2N1bWVudC5hZGRFdmVudExpc3RlbmVyKCdET01Db250ZW50TG9hZGVkJywgKCkgPT4ge1xuICAgIGluaXRDb21wb25lbnQoVGhlbWVUb2dnbGUpO1xuICAgIGluaXRDb21wb25lbnQoVGhlbWVUb2dnbGUpO1xuICAgIGluaXRDb21wb25lbnQoU2tpcExpbmspO1xuICAgIGluaXRDb21wb25lbnQoSGVhZGVyU2VhcmNoUGFuZWwpO1xuICAgIGluaXRDb21wb25lbnQoTW9iaWxlTWVudSk7XG59KTtcbiJdLCJuYW1lcyI6W10sInNvdXJjZVJvb3QiOiIifQ==