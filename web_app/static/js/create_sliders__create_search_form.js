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
var mileage_filter_switch = document.getElementById('id-enable-mileage-filter');
var price_filter_switch = document.getElementById('id-enable-price-filter');
var psc_filter_switch = document.getElementById('id-enable-psc-filter');
var psc_km_filter_switch = document.getElementById('id-enable-psc-km-filter');
var psc_input = document.getElementById('id-psc-code');
var psc_km_input = document.getElementById('id-psc-km-range');

var list_sliders = [slider_year, slider_mileage, slider_price];
var list_from = [input_year_from, input_mileage_from, input_price_from];
var list_to = [input_year_to, input_mileage_to, input_price_to];
var list_show = [[1990, 2010], [50000, 200000], [50000, 100000]];
var list_range = [[1950, currentYear], [0, 500000], [0, 1000000]];
var list_optional = [false, true, true];
var list_switches = [null, mileage_filter_switch, price_filter_switch];

function clear_input(input) {
    input.value = "";
}

function set_input_enabled(input, enabled) {
    input.disabled = !enabled;
    if (!enabled) {
        clear_input(input);
    }
}

function create_slider(slider, show, range, step, input_from, input_to, optional, optional_switch) {
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

    slider.noUiSlider.on("update", function (values, handle) {
        if (optional && !optional_switch.checked) {
            return;
        }
        if (handle === 0) {
            input_from.value = Math.round(values[0])
        } else {
            input_to.value = Math.round(values[1])
        }
    });
    input_from.addEventListener('change', function() {
        if (optional && !optional_switch.checked) {
            return;
        }
        if (optional && this.value === "") {
            return;
        }
        slider.noUiSlider.set([this.value, null])
    });
    input_to.addEventListener('change', function() {
        if (optional && !optional_switch.checked) {
            return;
        }
        if (optional && this.value === "") {
            return;
        }
        slider.noUiSlider.set([null, this.value])
    });

    if (optional) {
        optional_switch.checked = false;
        set_optional_slider_state(
            slider,
            input_from,
            input_to,
            optional_switch.checked
        );
        optional_switch.addEventListener('change', function() {
            set_optional_slider_state(slider, input_from, input_to, this.checked);
        });
    }
}

function set_optional_slider_state(slider, input_from, input_to, enabled) {
    if (enabled) {
        slider.noUiSlider.enable();
        input_from.disabled = false;
        input_to.disabled = false;
        var values = slider.noUiSlider.get();
        input_from.value = Math.round(values[0]);
        input_to.value = Math.round(values[1]);
        return;
    }

    slider.noUiSlider.disable();
    set_input_enabled(input_from, false);
    set_input_enabled(input_to, false);
}

function create_optional_input(input, optional_switch) {
    optional_switch.checked = false;
    set_input_enabled(input, optional_switch.checked);
    optional_switch.addEventListener('change', function() {
        set_input_enabled(input, this.checked);
    });
}

list_sliders.forEach((slider, i) => {
    create_slider(
        slider,
        list_show[i],
        list_range[i],
        1,
        list_from[i],
        list_to[i],
        list_optional[i],
        list_switches[i]
    );
})

create_optional_input(psc_input, psc_filter_switch);
create_optional_input(psc_km_input, psc_km_filter_switch);
