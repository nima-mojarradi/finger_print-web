document.addEventListener("DOMContentLoaded", () => {
    const menuToggle = document.getElementById("menu-toggle");
    const navbar = document.getElementById("navbar");
    const sidebar = document.getElementById("sidebar");

    menuToggle.addEventListener("click", () => {
        navbar.classList.toggle("active");
        sidebar.classList.toggle("active");
    });

    console.log("نسخه ریسپانسیو آماده است!");
});
