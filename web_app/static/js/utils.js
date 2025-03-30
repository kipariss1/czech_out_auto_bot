export function show_alert_message(message) {
    var alert_tab = document.getElementById('id-alert-tab');
    alert_tab.innerText = message;
    alert_tab.style.display = "block";
}

export function get_cookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }

