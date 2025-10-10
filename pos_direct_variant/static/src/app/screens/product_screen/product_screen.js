/** @odoo-module */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";

patch(ProductScreen.prototype, {
    
    async _onClickProduct(event) {
        const product = event.detail;
        
        // If direct variant search is enabled, skip variant selection
        if (this.pos.config.direct_variant_search) {
            // Add product directly to order
            const currentOrder = this.pos.get_order();
            if (currentOrder) {
                await currentOrder.add_product(product, {
                    force: true, // Force add even if it's a variant
                });
            }
            return;
        }
        
        // Otherwise use default behavior
        return super._onClickProduct(event);
    },

    async _updateProductList() {
        await super._updateProductList();
        
        // If searching with direct variant enabled, show all variants
        if (this.pos.config.direct_variant_search && this.state.search) {
            const products = this.pos.searchProductsWithVariants(this.state.search);
            this.state.products = products;
        }
    },
});
