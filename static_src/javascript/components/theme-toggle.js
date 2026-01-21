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

export default ThemeToggle;