odoo.define('finnapps_liasse_fiscale_dz.background_field', function (require) {

    // this js file will add background color to one2many listview based on condition display_type === 'total'

    "use strict";
    var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
    var fieldRegistry = require('web.field_registry');
    var ListRenderer = require('web.ListRenderer');

    var totalListRenderer = ListRenderer.extend({

        /**
         * We add the o_is_{display_type} class 
         *
         * @override
         */
        _renderRow: function (record, index) {
            var $row = this._super.apply(this, arguments);

            if (record.data.display_type) {
                $row.addClass('o_is_' + record.data.display_type);
            }

            return $row;
        },
        /**
         * We want to add .o_display_type_list_view on the table to have stronger CSS.
         *
         * @override
         * @private
         */
        _renderView: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self.$('.o_list_table').addClass('o_display_type_list_view');
            });
        }
    });

    var TotalFieldOne2Many = FieldOne2Many.extend({
        /**
         * We want to use our custom renderer for the list.
         *
         * @override
         */
        _getRenderer: function () {
            if (this.view.arch.tag === 'tree') {
                return totalListRenderer;
            }
            return this._super.apply(this, arguments);
        },
    });

    fieldRegistry.add('total_one2many', TotalFieldOne2Many);
    return totalListRenderer;
});
