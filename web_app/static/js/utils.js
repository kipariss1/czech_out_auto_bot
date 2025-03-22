export function show_alert_message(message) {
    var alert_tab = document.getElementById('id-alert-tab');
    alert_tab.innerText = message;
    alert_tab.style.display = "block";
}