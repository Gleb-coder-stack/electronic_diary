document.addEventListener("DOMContentLoaded", () => {
    // Первичная отрисовка
    if (window.ganttData) renderChart(window.ganttData);

    // Логика кнопок
    document.querySelectorAll(".btn-toggle").forEach(btn => {
        btn.addEventListener("click", function() {
            const id = this.dataset.id;
            toggleComplete(id, this);
        });
    });

    async function toggleComplete(id, btnElement) {
        btnElement.disabled = true;
        const oldText = btnElement.textContent;
        btnElement.textContent = "...";
        try {
            const response = await fetch(`/api/submissions/${id}/toggle`, { method: "POST" });
            const data = await response.json();
            const row = document.getElementById(`row-${id}`);
            if (row) {
                const cell = row.querySelector(".status-cell");
                if (data.is_completed) {
                    cell.innerHTML = '<span class="badge green">Выполнено</span>';
                    btnElement.textContent = "Отменить";
                } else {
                    cell.innerHTML = '<span class="badge red">Не выполнено</span>';
                    btnElement.textContent = "Отметить";
                }
            }
            // Перерисовываем диаграмму для обновления цветов
            const updatedData = await fetch('/api/submissions/').then(r => r.json());
            const formatted = updatedData.map(t => ({
                id: t.id, name: t.subject, title: t.title, start: t.start, end: t.end, completed: t.is_completed
            }));
            renderChart(formatted);
        } catch (error) {
            btnElement.textContent = oldText;
        } finally {
            btnElement.disabled = false;
        }
    }
});

let chartRoot = null;

function renderChart(data) {
    if (!data || data.length === 0) return;

    // Группируем по предметам, чтобы слева были предметы, а не дубли
    const groupedData = {};
    data.forEach(t => {
        if (!groupedData[t.name]) groupedData[t.name] = [];
        groupedData[t.name].push(t);
    });

    const seriesData = [];
    const categories = [];

    for (const subject in groupedData) {
        groupedData[subject].forEach((t, index) => {
            const rowId = subject + "_row_" + index;
            seriesData.push({
                category: rowId, 
                start: new Date(t.start).getTime(),
                end: new Date(t.end).getTime(),
                task: t.title,
                completed: t.completed,
                // НОВЫЕ ЦВЕТА:
                // Красный (не выполнено) - сочный, но не режущий глаз
                // Зеленый (выполнено) - приятный изумрудный
                color: t.completed ? am5.color(0x2ecc71) : am5.color(0xe74c3c)
            });
            // Выводим название предмета только для первой полосы
            categories.push({
                category: rowId,
                displayName: index === 0 ? subject : "" 
            });
        });
    }

    am5.ready(function() {
        if (chartRoot) {
            chartRoot.dispose(); 
        }
        chartRoot = am5.Root.new("chartdiv");
        chartRoot.setThemes([am5themes_Animated.new(chartRoot)]);

        var chart = chartRoot.container.children.push(
            am5xy.XYChart.new(chartRoot, {
                panX: true, panY: false, wheelX: "panX", wheelY: "zoomX", layout: chartRoot.verticalLayout
            })
        );

        // Ось Y (Предметы)
        var yAxis = chart.yAxes.push(
            am5xy.CategoryAxis.new(chartRoot, {
                categoryField: "category",
                renderer: am5xy.AxisRendererY.new(chartRoot, { 
                    minGridDistance: 20, // Чуть больше отступ между строками
                    inversed: true, 
                    cellStartLocation: 0.1, 
                    cellEndLocation: 0.9 
                })
            })
        );

        // Ось X (Даты)
        var xAxis = chart.xAxes.push(
            am5xy.DateAxis.new(chartRoot, {
                baseInterval: { timeUnit: "day", count: 1 },
                renderer: am5xy.AxisRendererX.new(chartRoot, {}),
            })
        );

        // УВЕЛИЧИВАЕМ ШРИФТ СЛЕВА (Названия предметов)
        yAxis.get("renderer").labels.template.setAll({ 
            fontSize: 15, // Было 13
            fontWeight: "600", 
            fill: am5.color(0x2c3e50), 
            populateText: true 
        });
        
        yAxis.get("renderer").labels.template.adapters.add("text", function(text, target) {
            if (target.dataItem && target.dataItem.dataContext) return target.dataItem.dataContext.displayName;
            return text;
        });

        // Сами полосы
        var series = chart.series.push(
            am5xy.ColumnSeries.new(chartRoot, {
                name: "Задания", 
                xAxis: xAxis, 
                yAxis: yAxis, 
                openValueXField: "start", 
                valueXField: "end", 
                categoryYField: "category", 
                sequencedInterpolation: true
            })
        );

        // Настройки полос (закругления, отступы)
        series.columns.template.setAll({ 
            height: am5.percent(70), // Толщина полосы
            cornerRadius: 6, // Красивые закругленные углы
            strokeOpacity: 0, 
            tooltipText: "{task}" 
        });
        
        // Привязка цветов
        series.columns.template.adapters.add("fill", function(fill, target) { 
            return target.dataItem.dataContext.color; 
        });

        // ТЕКСТ ВНУТРИ ПОЛОС (УВЕЛИЧИВАЕМ ШРИФТ)
        series.bullets.push(function() {
            return am5.Bullet.new(chartRoot, {
                locationX: 0.05, 
                sprite: am5.Label.new(chartRoot, { 
                    text: "{task}", 
                    fill: am5.color(0xffffff), // Белый текст
                    centerY: am5.p50, 
                    centerX: am5.p0, 
                    fontSize: 14, // Было 12
                    fontWeight: "600", // Жирнее
                    populateText: true 
                })
            });
        });

        yAxis.data.setAll(categories);
        series.data.setAll(seriesData);
        series.appear(1000);
        chart.appear(1000, 100);
    });
}