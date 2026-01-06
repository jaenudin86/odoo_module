/** @odoo-module **/

import AbstractField from 'web.AbstractField';
import { registry } from '@web/core/registry';
import $ from 'jquery';

const ColoredCircleField = AbstractField.extend({
    supportedFieldTypes: ['selection'],
    /**
     * Render widget sebagai lingkaran dengan background color sesuai nilai field.
     **/
    _render: function () {
        this.$el.empty();
        const colorValue = this.value;
        const colorMap = {
            'white': '#ffffff',
            'red': '#ff0000',
            'yellow': '#ffff00',
            'green': '#00ff00',
        };
        const colorHex = colorMap[colorValue] || '#000000';
        const $circle = $('<span>', {
            css: {
                'display': 'inline-block',
                'width': '16px',
                'height': '16px',
                'border-radius': '50%',
                'background-color': colorHex,
                'border': '1px solid #aaa'
            }
        });
        this.$el.append($circle);
    },
});

registry.category('fields').add('colored_circle', ColoredCircleField);
