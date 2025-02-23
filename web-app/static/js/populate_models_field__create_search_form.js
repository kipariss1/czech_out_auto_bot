document.getElementById("id-manufacturer").addEventListener("change", function(){
    let default_option_manufacturer = "Select model!";
    let manufacturer = this.value;
    let modelSelect = document.getElementById("id-model");
    modelSelect.innerHTML = `<option selected>${default_option_manufacturer}</option>`;

    if (manufacturer !== default_option_manufacturer){
        fetch(`/get_models/${manufacturer}`)
        .then(response => response.json())
        .then(models => {
            models.forEach(model => {
                let option = document.createElement("option");
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
            modelSelect.disabled = false;
            // TODO: make catching error with Alerts!
        })
    }
})