/* DermaScan AI – accessible custom presentation for native selects.
 * Keep the native select as the single source of truth for form values/events. */
(() => {
  "use strict";
  const instances = new Map();
  let active = null;
  const panel = document.createElement("div");
  panel.className = "ds-select-menu";
  panel.setAttribute("role", "listbox");
  panel.hidden = true;
  document.body.appendChild(panel);

  function close() {
    panel.hidden = true;
    panel.replaceChildren();
    if (active) active.wrap.classList.remove("is-open");
    active = null;
  }
  function optionsOf(select) {
    return [...select.options];
  }
  function update(inst) {
    const { select, trigger } = inst;
    const selected = select.selectedOptions[0];
    trigger.textContent = selected ? selected.textContent.trim() : "Chọn...";
    trigger.disabled = select.disabled;
    trigger.setAttribute("aria-expanded", active === inst ? "true" : "false");
    trigger.title = trigger.textContent;
    inst.wrap.classList.toggle("is-disabled", select.disabled);
  }
  function place(inst) {
    const rect = inst.trigger.getBoundingClientRect();
    const available = window.innerHeight - rect.bottom - 12;
    const height = Math.min(300, Math.max(120, optionsOf(inst.select).length * 39 + 12));
    const above = available < Math.min(height, 180) && rect.top > available;
    panel.style.left = Math.max(8, Math.min(rect.left, window.innerWidth - Math.max(rect.width, 220) - 8)) + "px";
    panel.style.width = Math.min(Math.max(rect.width, 220), window.innerWidth - 16) + "px";
    panel.style.maxHeight = Math.max(100, Math.min(height, above ? rect.top - 12 : available)) + "px";
    panel.style.top = above ? Math.max(8, rect.top - Math.min(height, rect.top - 12) - 6) + "px" : rect.bottom + 6 + "px";
  }
  function open(inst, focusSelection = false) {
    if (inst.select.disabled) return;
    if (active === inst) { close(); return; }
    close();
    active = inst;
    panel.replaceChildren();
    for (const [index, option] of optionsOf(inst.select).entries()) {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "ds-select-option";
      item.setAttribute("role", "option");
      item.setAttribute("aria-selected", String(option.selected));
      item.dataset.index = String(index);
      item.disabled = option.disabled;
      item.textContent = option.textContent;
      if (option.selected) item.classList.add("is-selected");
      item.addEventListener("click", () => {
        if (option.disabled) return;
        const changed = inst.select.selectedIndex !== index;
        inst.select.selectedIndex = index;
        update(inst);
        close();
        if (changed) inst.select.dispatchEvent(new Event("change", { bubbles: true }));
        inst.trigger.focus();
      });
      panel.appendChild(item);
    }
    panel.hidden = false;
    inst.wrap.classList.add("is-open");
    inst.trigger.setAttribute("aria-expanded", "true");
    place(inst);
    if (focusSelection) {
      const target = panel.querySelector(".is-selected:not(:disabled)") || panel.querySelector("button:not(:disabled)");
      target?.focus();
    }
  }
  function enhance(select) {
    if (instances.has(select) || select.multiple || select.size > 1 || select.closest(".ds-select-wrap")) return;
    const wrap = document.createElement("span");
    wrap.className = "ds-select-wrap";
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "ds-select-trigger";
    trigger.setAttribute("aria-haspopup", "listbox");
    trigger.setAttribute("aria-expanded", "false");
    trigger.setAttribute("aria-label", select.getAttribute("aria-label") || select.labels?.[0]?.textContent?.trim() || "Chọn giá trị");
    select.parentNode.insertBefore(wrap, select);
    wrap.appendChild(select);
    wrap.appendChild(trigger);
    select.classList.add("ds-select-native");
    select.tabIndex = -1;
    const inst = { select, wrap, trigger };
    instances.set(select, inst);
    trigger.addEventListener("click", () => open(inst));
    trigger.addEventListener("keydown", event => {
      if (["ArrowDown", "ArrowUp", " ", "Enter"].includes(event.key)) {
        event.preventDefault();
        open(inst, true);
      }
    });
    select.addEventListener("change", () => update(inst));
    update(inst);
  }
  function scan(root = document) {
    if (root.nodeType === 1 && root.matches("select")) enhance(root);
    root.querySelectorAll?.("select").forEach(enhance);
    for (const [select, inst] of instances) {
      if (!select.isConnected) {
        if (active === inst) close();
        instances.delete(select);
      } else update(inst);
    }
  }
  panel.addEventListener("keydown", event => {
    const buttons = [...panel.querySelectorAll("button:not(:disabled)")];
    const index = buttons.indexOf(document.activeElement);
    if (event.key === "Escape") {
      event.preventDefault();
      const trigger = active?.trigger;
      close();
      trigger?.focus();
    } else if (event.key === "ArrowDown" || event.key === "ArrowUp" || event.key === "Home" || event.key === "End") {
      event.preventDefault();
      const target = event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : Math.max(0, Math.min(buttons.length - 1, index + (event.key === "ArrowDown" ? 1 : -1)));
      buttons[target]?.focus();
    } else if (event.key === "Tab") close();
  });
  document.addEventListener("pointerdown", event => {
    if (active && !panel.contains(event.target) && !active.wrap.contains(event.target)) close();
  }, true);
  window.addEventListener("resize", () => { if (active) place(active); });
  window.addEventListener("scroll", () => { if (active) close(); }, true);
  const observer = new MutationObserver(records => {
    let rescan = false;
    for (const record of records) {
      if (record.type === "childList") {
        if (record.target === panel || panel.contains(record.target)) continue;
        rescan = true;
      } else if (record.target instanceof HTMLSelectElement) rescan = true;
    }
    if (rescan) scan();
  });
  function init() {
    scan();
    observer.observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ["disabled"] });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})();
