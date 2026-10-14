document.addEventListener("DOMContentLoaded", () => {
  const tasks = (window.ganttData || []).map(t => ({
    id: String(t.id),
    name: `${t.subject}: ${t.title}`,
    start: t.start,
    end: t.end,
    progress: t.completed ? 100 : 0,
    custom_class: t.completed ? "bar-done" : "bar-todo"
  }));

  if (tasks.length && document.getElementById("gantt-chart")) {
    new Gantt("#gantt-chart", tasks, {
      view_mode: "Day",
      language: "ru",
      on_click: (task) => toggle(task.id)
    });
  }

  document.querySelectorAll(".btn-toggle").forEach(btn => {
    btn.addEventListener("click", () => toggle(btn.dataset.id));
  });

  async function toggle(id) {
    try {
      const data = await API.toggleSubmission(id);
      const row = document.getElementById(`row-${id}`);
      const cell = row.querySelector(".status-cell");
      const btn = row.querySelector(".btn-toggle");

      if (data.is_completed) {
        cell.innerHTML = '<span class="badge green">Выполнено</span>';
        btn.textContent = "Отменить";
      } else {
        cell.innerHTML = '<span class="badge red">Не выполнено</span>';
        btn.textContent = "Отметить";
      }

      const bar = document.querySelector(`.bar-wrapper[data-id="${id}"] .bar`);
      if (bar) bar.style.fill = data.color;

    } catch (e) {
      alert("Не удалось обновить статус задания");
    }
  }
});