var default_option_manufacturer = document.getElementById("id-manufacturer").value

document.getElementById("id-manufacturer").addEventListener("change", function(){
    let manufacturer = this.value;
    let modelSelect = document.getElementById("id-model");

    if (manufacturer !== default_option_manufacturer){
        fetch("/get_models/${manufacturer}")
        .then(response => response.json())
        .then(models => {
            models.forEach(model => {
                let option = document.createElement("option");
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
            // TODO: make catching error with Alerts!
        })
    }
})