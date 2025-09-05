export function populate_search_cards(list_searches) {
    const container = document.getElementById("search-cards-container");

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
        pscCode.innerHTML = `<strong>PSČ Code:</strong> ${search.psc_code}`;

        const pscRange = document.createElement("p");
        pscRange.className = "card-text mb-2";
        pscRange.innerHTML = `<strong>PSČ km range:</strong> ${search.psc_km_range}`;

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

        const form = document.createElement("form");
        form.method = "post";
        form.action = `/delete_search/${search.id}/${search.user_id}`;
        form.className = "d-inline";

        const btn = document.createElement("button");
        btn.type = "submit";
        btn.className = "btn btn-outline-danger btn-sm";
        btn.innerText = "🗑️ Delete";

        form.appendChild(btn);

        body.appendChild(title);
        body.appendChild(pscCode);
        body.appendChild(pscRange);
        body.appendChild(attrTitle);
        body.appendChild(ul);
        body.appendChild(form);

        card.appendChild(body);
        container.appendChild(card);
    })
}