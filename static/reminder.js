async function loadReminders() {
  const res = await fetch('/api/reminders');
  const list = await res.json();
  const container = document.getElementById('reminder-list');
  container.innerHTML = '';
  list.forEach(r => {
    const div = document.createElement('div');
    div.className = 'event-item';
    const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    div.innerHTML = `<p>${dayNames[r.day_of_week]} ${r.time_of_day}</p>`;
    const audio = document.createElement('audio');
    audio.controls = true;
    audio.src = r.audio_url;
    div.appendChild(audio);
    container.appendChild(div);
  });
}

document.getElementById('reminder-form').addEventListener('submit', async e => {
  e.preventDefault();
  const file = document.getElementById('audio').files[0];
  const day = document.getElementById('day').value;
  const time = document.getElementById('time').value;
  const formData = new FormData();
  formData.append('file', file);
  formData.append('day_of_week', day);
  formData.append('time_of_day', time);
  await fetch('/api/reminders', { method: 'POST', body: formData });
  loadReminders();
});

window.addEventListener('DOMContentLoaded', loadReminders);
