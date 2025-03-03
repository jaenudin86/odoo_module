/** @odoo-module **/

import { FieldSelection } from 'web.relational_fields';
import { registry } from '@web/core/registry';
import $ from 'jquery';
import _ from 'underscore';

const ColoredRadioField = FieldSelection.extend({
    _render: function () {
        this.$el.empty();
        var fieldInstance = this;
        _.each(this.getSelection(), function (option) {
            var value = option[0];
            var label = option[1];
            var colorMap = {
                'white': '#ffffff',
                'red': '#ff0000',
                'yellow': '#ffff00',
                'green': '#00ff00'
            };
            var color = colorMap[value] || '#000000';

            var $label = $('<label>', { "class": "o_colored_radio_label" }).css({
                'background-color': color,
                'padding': '5px 10px',
                'margin-right': '10px',
                'border-radius': '3px',
                'cursor': 'pointer'
            });

            var $input = $('<input>', {
                type: 'radio',
                name: fieldInstance.name,
                value: value,
                style: 'margin-right:5px'
            });

            if (fieldInstance.value === value) {
                $input.prop('checked', true);
            }

            $input.on('change', function () {
                fieldInstance._setValue(value);
            });

            $label.append($input).append(label);
            fieldInstance.$el.append($label);
        });
    },
});
registry.category('fields').add('colored_radio', ColoredRadioField);
