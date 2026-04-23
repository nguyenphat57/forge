(function() {
  const WS_URL = 'ws://' + window.location.host;
  let ws = null;
  let queue = [];

  function connect() {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      queue.forEach(event => ws.send(JSON.stringify(event)));
      queue = [];
    };

    ws.onmessage = (message) => {
      const event = JSON.parse(message.data);
      if (event.type === 'reload') window.location.reload();
    };

    ws.onclose = () => setTimeout(connect, 1000);
  }

  function send(event) {
    event.timestamp = Date.now();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(event));
    } else {
      queue.push(event);
    }
  }

  function selectedLabel(element) {
    return element.querySelector('h3, .content h3, .card-body h3')?.textContent?.trim()
      || element.dataset.choice;
  }

  function updateIndicator(target) {
    const indicator = document.getElementById('indicator-text');
    if (!indicator) return;
    const container = target.closest('.options') || target.closest('.cards');
    const selected = container ? container.querySelectorAll('.selected') : [];
    if (selected.length === 0) {
      indicator.textContent = 'Click an option above, then return to the terminal';
    } else if (selected.length === 1) {
      indicator.innerHTML = '<span class="selected-text">' + selectedLabel(selected[0]) + '</span> selected - return to terminal to continue';
    } else {
      indicator.innerHTML = '<span class="selected-text">' + selected.length + '</span> selected - return to terminal to continue';
    }
  }

  document.addEventListener('click', (event) => {
    const target = event.target.closest('[data-choice]');
    if (!target) return;

    send({
      type: 'click',
      text: target.textContent.trim(),
      choice: target.dataset.choice,
      id: target.id || null
    });
    setTimeout(() => updateIndicator(target), 0);
  });

  window.selectedChoice = null;
  window.toggleSelect = function(element) {
    const container = element.closest('.options') || element.closest('.cards');
    const multi = container && container.dataset.multiselect !== undefined;
    if (container && !multi) {
      container.querySelectorAll('.option, .card').forEach(option => option.classList.remove('selected'));
    }
    if (multi) element.classList.toggle('selected');
    else element.classList.add('selected');
    window.selectedChoice = element.dataset.choice;
  };

  window.forgeVisualCompanion = {
    send,
    choice: (value, metadata = {}) => send({ type: 'choice', value, ...metadata })
  };

  connect();
})();
