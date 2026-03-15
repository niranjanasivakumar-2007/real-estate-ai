function formatPrice(price) {
    return '₹' + Number(price).toLocaleString('en-IN');
}

function showAlert(message, type = 'error', containerId = 'alert') {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.textContent = message;
    el.className = `alert alert-${type} show`;
    el.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setTimeout(() => { el.style.display = 'none'; }, 5000);
}

function hideAlert(containerId = 'alert') {
    const el = document.getElementById(containerId);
    if (el) el.style.display = 'none';
}

async function requireLogin(role = null) {
    const res = await fetch('/session');
    const data = await res.json();
    if (!data.logged_in) {
        window.location.href = '/';
        return null;
    }
    if (role && data.role !== role) {
        window.location.href = '/';
        return null;
    }
    return data;
}

async function logout() {
    await fetch('/logout', { method: 'POST' });
    window.location.href = '/';
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function debounce(fn, delay = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
}

function truncate(text, maxLength = 60) {
    if (!text) return '';
    return text.length > maxLength
        ? text.substring(0, maxLength) + '...'
        : text;
}

function getParam(name) {
    return new URLSearchParams(window.location.search).get(name);
}


function setParam(name, value) {
    const url = new URL(window.location);
    if (value) url.searchParams.set(name, value);
    else url.searchParams.delete(name);
    window.history.replaceState({}, '', url);
}


async function apiFetch(url, options = {}) {
    try {
        const res = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });
        const data = await res.json();
        return { ok: res.ok, status: res.status, data };
    } catch (err) {
        console.error('API error:', err);
        return { ok: false, data: { error: 'Network error' } };
    }
}


function renderSkeletons(containerId, count = 3) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = Array(count).fill(`
        <div class="card" style="padding:0">
            <div class="skeleton" style="height:180px;border-radius:16px 16px 0 0"></div>
            <div style="padding:16px">
                <div class="skeleton" style="height:20px;width:60%;margin-bottom:10px"></div>
                <div class="skeleton" style="height:14px;width:80%;margin-bottom:8px"></div>
                <div class="skeleton" style="height:14px;width:40%"></div>
            </div>
        </div>
    `).join('');
}


async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch {
        return false;
    }
}


document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('img').forEach(img => {
        img.addEventListener('error', function () {
            this.style.display = 'none';
            const placeholder = document.createElement('div');
            placeholder.style.cssText =
                'width:100%;height:100%;display:flex;align-items:center;' +
                'justify-content:center;font-size:32px;color:#ccc;background:#f1f3f5';
            placeholder.textContent = '🏠';
            this.parentNode.appendChild(placeholder);
        });
    });
});


function scrollTo(elementId) {
    document.getElementById(elementId)
        ?.scrollIntoView({ behavior: 'smooth' });
}


function formatDate(dateStr) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('en-IN', {
        year: 'numeric', month: 'short', day: 'numeric'
    });
}

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}


function isValidPhone(phone) {
    return /^[+]?[\d\s\-]{10,15}$/.test(phone);
}
