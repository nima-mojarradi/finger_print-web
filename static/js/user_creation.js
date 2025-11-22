document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("createUserForm");
    const resultDiv = document.getElementById("createUserResult");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        resultDiv.innerHTML = "";

        const formData = new FormData(form);
        const data = {};

        formData.forEach((value, key) => {
            data[key] = value;
        });

        // اگر اثر انگشت هم داری، میتونی اینجا اضافه کنی
        // data["fingerprints"] = [...]

        try {
            const response = await fetch("{% url 'user-create' %}", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                resultDiv.innerHTML = `<div class="alert alert-success">${result.message}<br>رمز عبور: ${result.password}</div>`;
                form.reset();
            } else {
                resultDiv.innerHTML = `<div class="alert alert-danger">${result.error || JSON.stringify(result)}</div>`;
            }
        } catch (err) {
            resultDiv.innerHTML = `<div class="alert alert-danger">خطای شبکه یا سرور: ${err}</div>`;
        }
    });
});

// helper برای گرفتن CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
