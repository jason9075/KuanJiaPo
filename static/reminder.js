async function loadReminders() {
  const res = await fetch('/api/reminders');
  const list = await res.json();
  const container = document.getElementById('reminder-list');
  container.innerHTML = '';
  list.forEach(r => {
    const div = document.createElement('div');
    div.className = 'event-item';
    div.innerHTML = `<p>${r.play_time}</p>`;
    const audio = document.createElement('audio');
    audio.controls = true;
    audio.src = r.audio_path;
    div.appendChild(audio);
    container.appendChild(div);
  });
}

document.getElementById('reminder-form').addEventListener('submit', async e => {
  e.preventDefault();
  const file = document.getElementById('audio').files[0];
  const playTime = document.getElementById('play-time').value;
  const formData = new FormData();
  formData.append('file', file);
  formData.append('play_time', playTime);
  await fetch('/api/reminders', { method: 'POST', body: formData });
  loadReminders();
});

window.addEventListener('DOMContentLoaded', loadReminders);
