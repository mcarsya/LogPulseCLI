/**
 * LogPulse Enterprise Client Utilities
 * Search filter, code copy, and table sorting.
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Sidebar Search Filter
  const searchInput = document.getElementById("sidebarSearch");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      const query = e.target.value.toLowerCase().trim();
      const navLinks = document.querySelectorAll(".nav-link");

      navLinks.forEach((link) => {
        const text = link.textContent.toLowerCase();
        const navItem = link.closest(".nav-item");
        if (text.includes(query) || query === "") {
          navItem.style.display = "";
        } else {
          navItem.style.display = "none";
        }
      });
    });
  }

  // 2. Code Block Copy Buttons
  const codeBlocks = document.querySelectorAll("pre code");
  codeBlocks.forEach((codeEl) => {
    const pre = codeEl.parentElement;
    const btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.innerHTML = "📋 Copy";
    btn.style.position = "absolute";
    btn.style.top = "10px";
    btn.style.right = "10px";
    btn.style.padding = "4px 8px";
    btn.style.fontSize = "0.75rem";
    btn.style.background = "rgba(255,255,255,0.15)";
    btn.style.border = "none";
    btn.style.borderRadius = "4px";
    btn.style.color = "#fff";
    btn.style.cursor = "pointer";

    btn.addEventListener("click", () => {
      navigator.clipboard.writeText(codeEl.innerText).then(() => {
        btn.innerHTML = "✓ Copied!";
        setTimeout(() => {
          btn.innerHTML = "📋 Copy";
        }, 2000);
      });
    });

    pre.style.position = "relative";
    pre.appendChild(btn);
  });
});
