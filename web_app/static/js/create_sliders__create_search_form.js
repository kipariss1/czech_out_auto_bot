const currentYear = new Date().getFullYear();
var slider_year = document.getElementById('id-slider-year');
var input_year_from = document.getElementById('id-input-year-range-from');
var input_year_to = document.getElementById('id-input-year-range-to');
var slider_mileage = document.getElementById('id-slider-mileage');
var input_mileage_from = document.getElementById('id-input-mileage-range-from');
var input_mileage_to = document.getElementById('id-input-mileage-range-to');
var slider_price = document.getElementById('id-slider-price');
var input_price_from = document.getElementById('id-input-price-range-from');
var input_price_to = document.getElementById('id-input-price-range-to');

var list_sliders = [slider_year, slider_mileage, slider_price];
var list_from = [input_year_from, input_mileage_from, input_price_from];
var list_to = [input_year_to, input_mileage_to, input_price_to];
var list_show = [[1990, 2010], [50000, 200000], [50000, 100000]];
var list_range = [[1950, currentYear], [0, 500000], [0, 1000000]];
var list_optional = [false, true, true];

function create_slider(slider, show, range, step, input_from, input_to, optional) {
    noUiSlider.create(slider, {
        start: [show[0], show[1]],
        connect: true,
        range: {
            "min": range[0],
            "max": range[1]
        },
        step: step,
        format: {
            to: function (value) {
                return Math.round(value);
            },
            from: function (value) {
                return Number(value);
            }
        }
    });

    var sync_inputs = !optional;
    if (optional) {
        setTimeout(function() {
            sync_inputs = true;
        }, 0);
    }

    slider.noUiSlider.on("update", function (values, handle) {
        if (!sync_inputs) {
            return;
        }
        if (handle === 0) {
            input_from.value = Math.round(values[0])
        } else {
            input_to.value = Math.round(values[1])
        }
    });
    input_from.addEventListener('change', function() {
        if (optional && this.value === "") {
            return;
        }
        slider.noUiSlider.set([this.value, null])
    });
    input_to.addEventListener('change', function() {
        if (optional && this.value === "") {
            return;
        }
        slider.noUiSlider.set([null, this.value])
    });
    if (optional) {
        input_from.value = "";
        input_to.value = "";
    }
}

list_sliders.forEach((slider, i) => {
    create_slider(slider, list_show[i], list_range[i], 1, list_from[i], list_to[i], list_optional[i]);
})
