document.addEventListener("DOMContentLoaded", function () {
    const flashMessages = document.querySelectorAll(".flash");
    const menuToggle = document.getElementById("menuToggle");
    const navLinks = document.getElementById("navLinks");
    const darkModeToggle = document.getElementById("darkModeToggle");

    // Flash messages auto-dismiss
    flashMessages.forEach((message) => {
        setTimeout(() => {
            message.style.opacity = "0";
            message.style.transform = "translateY(-8px)";
            setTimeout(() => {
                message.style.display = "none";
            }, 300);
        }, 3000);
    });

    // Mobile menu toggle
    if (menuToggle && navLinks) {
        menuToggle.addEventListener("click", function () {
            navLinks.classList.toggle("open");
            const expanded = navLinks.classList.contains("open");
            menuToggle.setAttribute("aria-expanded", expanded ? "true" : "false");
        });
    }

    // Dark mode toggle
    if (darkModeToggle) {
        // Check for saved preference or default to light mode
        const isDarkMode = localStorage.getItem("darkMode") === "true";
        if (isDarkMode) {
            document.body.classList.add("dark-mode");
        }

        darkModeToggle.addEventListener("click", function () {
            document.body.classList.toggle("dark-mode");
            const isDark = document.body.classList.contains("dark-mode");
            localStorage.setItem("darkMode", isDark ? "true" : "false");
        });
    }
});
