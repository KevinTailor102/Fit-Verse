/**
 * FitVerse — Main App JavaScript
 * Handles: Dark Mode, Sidebar, Toast Notifications, Utilities
 */

// ── Dark Mode ─────────────────────────────────────────────────────────────
const DARK_KEY = 'fitverse-dark';

function applyTheme(dark) {
  document.documentElement.setAttribute('data-bs-theme', dark ? 'dark' : 'light');
  const icons = document.querySelectorAll('#darkIcon, #darkIconMobile');
  icons.forEach(i => {
    i.className = dark ? 'fas fa-sun' : 'fas fa-moon';
  });
}

function toggleDark() {
  const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
  const next = !isDark;
  localStorage.setItem(DARK_KEY, next ? '1' : '0');
  applyTheme(next);
}

// Init theme on page load
(function initTheme() {
  const saved = localStorage.getItem(DARK_KEY);
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(saved !== null ? saved === '1' : prefersDark);
})();

document.addEventListener('DOMContentLoaded', () => {
  // Attach dark toggle buttons
  document.getElementById('darkToggle')?.addEventListener('click', toggleDark);
  document.getElementById('darkToggleMobile')?.addEventListener('click', toggleDark);

  // ── Sidebar Toggle ──────────────────────────────────────────────────────
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const mainContent = document.getElementById('mainContent');

  function openSidebar() {
    sidebar?.classList.add('open');
    overlay?.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar?.classList.remove('open');
    overlay?.classList.remove('active');
    document.body.style.overflow = '';
  }

  function toggleSidebar() {
    if (sidebar?.classList.contains('open')) closeSidebar();
    else openSidebar();
  }

  document.getElementById('sidebarToggle')?.addEventListener('click', toggleSidebar);
  document.getElementById('sidebarToggleDesktop')?.addEventListener('click', () => {
    // Desktop: collapse sidebar
    if (window.innerWidth >= 992) {
      const isCollapsed = sidebar?.style.width === '0px';
      if (isCollapsed) {
        sidebar.style.width = '';
        mainContent.style.marginLeft = '';
      } else {
        sidebar.style.width = '0px';
        mainContent.style.marginLeft = '0';
      }
    }
  });
  overlay?.addEventListener('click', closeSidebar);

  // Close sidebar on ESC
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSidebar();
  });

  // ── Auto-dismiss flash alerts ──────────────────────────────────────────
  setTimeout(() => {
    document.querySelectorAll('.alert.fade.show').forEach(a => {
      a.classList.remove('show');
    });
  }, 5000);
});

// ── Toast Notifications ───────────────────────────────────────────────────
function showToast(message, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const colors = {
    success: '#22c55e',
    danger: '#ef4444',
    warning: '#f59e0b',
    info: '#3b82d4',
  };

  const toast = document.createElement('div');
  toast.style.cssText = `
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid ${colors[type] || colors.info};
    border-radius: 10px;
    padding: 0.875rem 1.125rem;
    min-width: 260px;
    max-width: 340px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    font-size: 0.875rem;
    color: var(--text);
    margin-top: 0.5rem;
    animation: slideIn 0.3s ease;
    cursor: pointer;
  `;
  toast.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle'}" style="color:${colors[type]}; margin-right:0.5rem;"></i>${message}`;

  const style = document.createElement('style');
  style.textContent = '@keyframes slideIn{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:translateX(0)}}';
  document.head.appendChild(style);

  container.appendChild(toast);
  toast.addEventListener('click', () => toast.remove());

  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s, transform 0.3s';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ── HTML Escape Utility ───────────────────────────────────────────────────
function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return text.replace(/[&<>"']/g, m => map[m]);
}

// ── Jinja2 `now()` Polyfill for templates ────────────────────────────────
// (used in dashboard.html — Jinja2 handles this server-side)

// ── Active nav link highlighting ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && path.startsWith(href)) {
      link.classList.add('active');
    }
  });
});
