document.addEventListener('DOMContentLoaded', () => {
    const loginBtn = document.getElementById('loginBtn');

    function showToast(message, type="error", duration=3000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerText = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.classList.add('show'), 100);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    loginBtn.addEventListener('click', async () => {
        const nat = document.getElementById('nationality_number').value.trim();
        const pass = document.getElementById('password').value;

        if(!nat || !pass){
            showToast("لطفا کد ملی و رمز عبور را وارد کنید", "warning");
            return;
        }

        try {
            const res = await fetch('/api/accounts/login/', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({nationality_number: nat, password: pass})
            });

            const j = await res.json();

            if (res.ok && j.access_token) {
                localStorage.setItem('token', j.access_token);
                localStorage.setItem('role', j.user.roles);
                localStorage.setItem('company', j.user.company || '');
                showToast("ورود موفقیت آمیز بود", "success");

                setTimeout(() => {
                    window.location.href = "/profile/";
                }, 800);

            } else {
                showToast(j.error || j.message || 'خطا در ورود', "error");
            }

        } catch (err) {
            showToast("خطا در اتصال به سرور", "error");
            console.error(err);
        }
    });
});
