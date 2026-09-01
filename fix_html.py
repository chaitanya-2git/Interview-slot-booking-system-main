
with open('templates/hr_dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('<td>\n                                <span class=" badge bg-secondary\>{{ booking.license_name }}</span>\n </td>', '<td data-label=\License\>\n <span class=\badge bg-secondary\>{{ booking.license_name }}</span>\n </td>')
with open('templates/hr_dashboard.html', 'w', encoding='utf-8') as f:
 f.write(c)

with open('templates/candidate_dashboard.html', 'r', encoding='utf-8') as f:
 c = f.read()
c = c.replace('<td>\n {% if block.available > 0 %}', '<td data-label=\Availability\>\n {% if block.available > 0 %}')
c = c.replace('<td>{{ block.interview_date }}</td>', '<td data-label=\Date\>{{ block.interview_date }}</td>')
c = c.replace('<td>{{ block.start_time }}</td>', '<td data-label=\Start Time\>{{ block.start_time }}</td>')
c = c.replace('<td>{{ block.end_time }}</td>', '<td data-label=\End Time\>{{ block.end_time }}</td>')
with open('templates/candidate_dashboard.html', 'w', encoding='utf-8') as f:
 f.write(c)

