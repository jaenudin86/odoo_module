/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    
    async setup() {
        await super.setup(...arguments);
        // Store all variants separately for quick access
        this.productVariants = {};
        this._indexProductVariants();
    },

    _indexProductVariants() {
        // Index all product variants for faster search
        for (const product of Object.values(this.models['product.product'].getAllBy('id'))) {
            const key = this._getProductSearchKey(product);
            if (!this.productVariants[key]) {
                this.productVariants[key] = [];
            }
            this.productVariants[key].push(product);
        }
    },

    _getProductSearchKey(product) {
        // Create searchable string from product data
        const parts = [
            product.display_name || '',
            product.default_code || '',
            product.barcode || '',
        ];
        return parts.join(' ').toLowerCase();
    },

    searchProductsWithVariants(searchWord) {
        if (!this.config.direct_variant_search) {
            return this.searchProductInCategory(0, searchWord);
        }

        const query = searchWord.toLowerCase().trim();
        if (!query) {
            return [];
        }

        const results = [];
        const seenIds = new Set();

        // Search through all products including variants
        for (const product of Object.values(this.models['product.product'].getAllBy('id'))) {
            if (seenIds.has(product.id)) continue;

            const searchKey = this._getProductSearchKey(product);
            
            if (searchKey.includes(query)) {
                results.push(product);
                seenIds.add(product.id);
            }

            // Limit results for performance
            if (results.length >= 100) {
                break;
            }
        }

        return results;
    },

    // Override the original method to support variant search
    searchProductInCategory(categoryId, searchWord) {
        if (this.config.direct_variant_search && searchWord) {
            return this.searchProductsWithVariants(searchWord);
        }
        return super.searchProductInCategory(categoryId, searchWord);
    },
});