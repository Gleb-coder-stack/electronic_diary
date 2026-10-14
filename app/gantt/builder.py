def build_gantt_data(submissions):
    data = []
    for sub in submissions:
        t = sub.task
        data.append({
            "id": sub.id,
            "subject": t.subject.name if t.subject else "—",
            "title": t.title,
            "start": t.start_date.strftime("%Y-%m-%d"),
            "end": t.due_date.strftime("%Y-%m-%d"),
            "completed": sub.is_completed
        })
    return data