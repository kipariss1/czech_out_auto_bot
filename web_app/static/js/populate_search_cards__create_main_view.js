import { show_error_message, show_success_message } from "./utils.js";

function display_optional_value(value) {
    if (value === null || value === undefined || value === "") {
        return "any";
    }
    return value;
}

export function populate_search_cards(list_searches) {
    const container = document.getElementById("search-cards-container");
    container.innerHTML = "";

    list_searches.forEach((search, index) => {
        const card = document.createElement("div");
        card.className = "card shadow-sm my-3 mx-2";

        const body = document.createElement("div");
        body.className = "card-body";

        const title = document.createElement("h5");
        title.className = "card-title";
        title.innerHTML = `🚗 Search #${index + 1} <strong>${search.car_model}</strong>`;

        const pscCode = document.createElement("p");
        pscCode.className = "card-text mb-1";
        pscCode.innerHTML = `<strong>PSČ Code:</strong> ${display_optional_value(search.psc_code)}`;

        const pscRange = document.createElement("p");
        pscRange.className = "card-text mb-2";
        pscRange.innerHTML = `<strong>PSČ km range:</strong> ${display_optional_value(search.psc_km_range)}`;

        const attrTitle = document.createElement("p");
        attrTitle.className = "card-text";
        attrTitle.innerHTML = "<strong>Attributes:</strong>";

        const ul = document.createElement("ul");
        ul.className = "mb-3";
        for (let key in search.attributes) {
            const li = document.createElement("li");
            if (key === 'Price range') {
                const newKey = 'Price range (Kč)';
                li.innerHTML = `<strong>${newKey}:</strong> ${search.attributes[key]}`;
                ul.appendChild(li);
                continue;
            }
            li.innerHTML = `<strong>${key}:</strong> ${search.attributes[key]}`;
            ul.appendChild(li);
        }

        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-outline-danger btn-sm";
        btn.innerText = "🗑️ Delete";
        btn.addEventListener("click", async () => {
            btn.disabled = true;

            try {
                if (search.id === undefined || search.id === null) {
                    btn.disabled = false;
                    show_error_message("Failed to delete search: search id is missing.");
                    return;
                }

                const deleteUrl = new URL(
                    `/delete_search/${encodeURIComponent(String(search.id))}`,
                    window.location.origin
                );

                const response = await fetch(deleteUrl, {
                    method: "POST",
                });

                let payload = null;
                try {
                    payload = await response.json();
                } catch {
                    payload = null;
                }

                if (!response.ok) {
                    btn.disabled = false;
                    const backendReason = payload?.reason
                        ? ` ${payload.reason}.`
                        : "";
                    show_error_message(
                        `Failed to delete search ${search.id}. HTTP ${response.status}.${backendReason}`
                    );
                    return;
                }

                if (payload?.deleted !== true) {
                    btn.disabled = false;
                    show_error_message(
                        `Failed to delete search ${search.id}.`
                    );
                    return;
                }

                card.remove();
                show_success_message("Search deleted.");
            } catch (error) {
                btn.disabled = false;
                show_error_message(String(error));
            }
        });

        body.appendChild(title);
        body.appendChild(pscCode);
        body.appendChild(pscRange);
        body.appendChild(attrTitle);
        body.appendChild(ul);
        body.appendChild(btn);

        card.appendChild(body);
        container.appendChild(card);
    });
}
