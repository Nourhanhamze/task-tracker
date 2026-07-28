const API_BASE = "http://localhost:8000";
const STATUSES = ["ToDo", "InProgress", "Done"];
const PRIORITY_ORDER = { High: 0, Medium: 1, Low: 2 };

const board = document.getElementById("board");
const banner = document.getElementById("status-banner");
const overlay = document.getElementById("modal-overlay");
const form = document.getElementById("task-form");
const modalTitle = document.getElementById("modal-title");
const formError = document.getElementById("form-error");
const titleError = document.getElementById("f-title-error");
const tagFilterInput = document.getElementById("tag-filter");
const overdueFilterCheckbox = document.getElementById("overdue-filter");

let tasks = [];
let editingTaskId = null;

function showBanner(message, kind) {
  banner.textContent = message;
  banner.hidden = false;
  banner.className = kind;
}

function hideBanner() {
  banner.hidden = true;
  banner.textContent = "";
  banner.className = "";
}

async function fetchTasks() {
  showBanner("Loading tasks…", "loading");
  try {
    const params = new URLSearchParams();
    const tag = tagFilterInput.value.trim();
    if (tag) params.set("tag", tag);
    if (overdueFilterCheckbox.checked) params.set("overdue", "true");
    const query = params.toString();

    const res = await fetch(`${API_BASE}/tasks${query ? `?${query}` : ""}`);
    if (!res.ok) throw new Error(`Request failed with ${res.status}`);
    tasks = await res.json();
    hideBanner();
    renderBoard();
  } catch (err) {
    showBanner("Could not load tasks. Is the backend running at " + API_BASE + "?", "error");
    renderBoard();
  }
}

function sortTasks(list) {
  return [...list].sort((a, b) => {
    const p = PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority];
    if (p !== 0) return p;
    return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
  });
}

function cardHtml(task) {
  const desc = task.description ? `<div class="card-desc">${escapeHtml(task.description)}</div>` : "";
  const assignee = task.assignee ? `<span class="assignee">${escapeHtml(task.assignee)}</span>` : "";
  const overduePill = task.overdue ? `<span class="pill overdue">Overdue</span>` : "";
  const dueDate = task.due_date
    ? `<div class="due-date${task.overdue ? " overdue-text" : ""}">Due ${escapeHtml(task.due_date)}</div>`
    : "";
  const tags = (task.tags || [])
    .map((t) => `<span class="tag-chip">${escapeHtml(t)}</span>`)
    .join("");
  return `
    <article class="card" draggable="true" data-id="${task.id}">
      <div class="card-title">${escapeHtml(task.title)}</div>
      ${desc}
      <div class="card-meta">
        <span class="pill priority-${task.priority}">${task.priority}</span>
        ${overduePill}
        ${assignee}
      </div>
      ${dueDate}
      <div class="card-meta">${tags}</div>
      <div class="card-actions">
        <button type="button" class="btn-secondary edit-btn" data-id="${task.id}">Edit</button>
      </div>
    </article>
  `;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function renderBoard() {
  for (const status of STATUSES) {
    const list = document.querySelector(`[data-list="${status}"]`);
    const countEl = document.querySelector(`[data-count="${status}"]`);
    const items = sortTasks(tasks.filter((t) => t.status === status));
    countEl.textContent = items.length;

    if (items.length === 0) {
      list.innerHTML = `<div class="empty-placeholder">No tasks</div>`;
    } else {
      list.innerHTML = items.map(cardHtml).join("");
    }
  }
  attachCardListeners();
}

function attachCardListeners() {
  document.querySelectorAll(".card").forEach((card) => {
    card.addEventListener("dragstart", onDragStart);
  });
  document.querySelectorAll(".edit-btn").forEach((btn) => {
    btn.addEventListener("click", () => openEditModal(btn.dataset.id));
  });
}

function onDragStart(e) {
  e.dataTransfer.setData("text/plain", e.currentTarget.dataset.id);
}

document.querySelectorAll(".column").forEach((column) => {
  column.addEventListener("dragover", (e) => {
    e.preventDefault();
    column.classList.add("drag-over");
  });
  column.addEventListener("dragleave", () => column.classList.remove("drag-over"));
  column.addEventListener("drop", async (e) => {
    e.preventDefault();
    column.classList.remove("drag-over");
    const taskId = e.dataTransfer.getData("text/plain");
    const newStatus = column.dataset.status;
    const task = tasks.find((t) => t.id === taskId);
    if (!task || task.status === newStatus) return;

    try {
      const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        await fetchTasks();
        showBanner(body.detail || `Move rejected (${res.status})`, "error");
        return;
      }
      await fetchTasks();
    } catch (err) {
      showBanner("Network error while moving task.", "error");
      await fetchTasks();
    }
  });
});

function openCreateModal() {
  editingTaskId = null;
  modalTitle.textContent = "New Task";
  form.reset();
  document.getElementById("f-status").value = "ToDo";
  document.getElementById("f-priority").value = "Medium";
  clearErrors();
  overlay.hidden = false;
}

function openEditModal(taskId) {
  const task = tasks.find((t) => t.id === taskId);
  if (!task) return;
  editingTaskId = taskId;
  modalTitle.textContent = "Edit Task";
  document.getElementById("f-title").value = task.title;
  document.getElementById("f-description").value = task.description || "";
  document.getElementById("f-status").value = task.status;
  document.getElementById("f-priority").value = task.priority;
  document.getElementById("f-assignee").value = task.assignee || "";
  document.getElementById("f-due-date").value = task.due_date || "";
  document.getElementById("f-tags").value = (task.tags || []).join(", ");
  clearErrors();
  overlay.hidden = false;
}

function closeModal() {
  overlay.hidden = true;
  editingTaskId = null;
  form.reset();
  clearErrors();
}

function clearErrors() {
  formError.hidden = true;
  formError.textContent = "";
  titleError.textContent = "";
}

document.getElementById("new-task-btn").addEventListener("click", openCreateModal);
document.getElementById("cancel-btn").addEventListener("click", closeModal);
overlay.addEventListener("click", (e) => {
  if (e.target === overlay) closeModal();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !overlay.hidden) closeModal();
});
tagFilterInput.addEventListener("input", debounce(fetchTasks, 250));
overdueFilterCheckbox.addEventListener("change", fetchTasks);

function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function parseTags(rawValue) {
  return rawValue
    .split(",")
    .map((t) => t.trim())
    .filter((t) => t.length > 0);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearErrors();

  const title = document.getElementById("f-title").value.trim();
  if (!title) {
    titleError.textContent = "Title is required.";
    return;
  }

  const dueDateValue = document.getElementById("f-due-date").value;

  const payload = {
    title,
    description: document.getElementById("f-description").value,
    status: document.getElementById("f-status").value,
    priority: document.getElementById("f-priority").value,
    assignee: document.getElementById("f-assignee").value.trim() || null,
    due_date: dueDateValue || null,
    tags: parseTags(document.getElementById("f-tags").value),
  };

  const isEdit = Boolean(editingTaskId);
  const url = isEdit ? `${API_BASE}/tasks/${editingTaskId}` : `${API_BASE}/tasks`;
  const method = isEdit ? "PATCH" : "POST";

  try {
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      formError.textContent = formatError(body.detail) || `Save failed (${res.status})`;
      formError.hidden = false;
      return;
    }
    closeModal();
    await fetchTasks();
  } catch (err) {
    formError.textContent = "Network error while saving task.";
    formError.hidden = false;
  }
});

function formatError(detail) {
  if (!detail) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
  return JSON.stringify(detail);
}

fetchTasks();
