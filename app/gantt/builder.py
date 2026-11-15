def build_gantt_data(submissions):
    data = []
    for sub in submissions:
        t = sub.task
        data.append({
            "id": str(sub.id),
            "name": t.subject.name if t.subject else "Без предмета",
            "title": t.title,
            "start": t.start_date.strftime("%Y-%m-%d"),
            "end": t.due_date.strftime("%Y-%m-%d"),
            "completed": sub.is_completed,
            "week_type": t.week_type
        })
    return data