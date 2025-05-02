/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Product } from "@point_of_sale/app/store/models";


patch(PosStore.prototype, {

    async _processData(loadedData) {

        await super._processData(loadedData);
        this.db.product_by_default_code = {};
        this.db.product_by_qr = {};
        this.offline_status_updates = []
        this.subscription_dog = loadedData["subscription.dog"];
        this.subscription_vehicle = loadedData["subscription.vehicle"];
        this.subscription_partner_order = loadedData["sale.order"];
        this.subscription_partner = loadedData["sale.order.line"];
        console.log('___ this : ', this);
        // this.custom_model = loadedData["subscription.vehicle"];
        await this.db.bi_add_product(loadedData["product.product"]);
    },

    async push_state_updates(customer_checklist_dict){
        customer_checklist_dict = customer_checklist_dict.map(proxyObj => Object.assign({}, proxyObj));
        console.log('___ customer_checklist_dict : ', customer_checklist_dict);
        const response =await this.orm.call("res.partner", "update_customer_sign_in_out_status", [null,{customer_checklist_dict}]);
        console.log('___ response : ', response);
        return response;
    },

    get_dog_by_id(id) {
        return this.subscription_dog.find(item => item.id === id);

    },
    get_car_by_id(id) {
        return this.subscription_vehicle.find(item => item.id === id);
    },
    get_subscriptions_by_partner_id(id, subscription_code) {
        const line_list = this.subscription_partner.filter(item => 
            item.order_partner_id[0] == id && item.subscription_type_code == subscription_code
        );

        console.log('___ line_list : ', line_list);

        const processedOrders = new Set(); // To track unique order IDs
        const order_list = []; // Final list of unique orders

        for (let loop of line_list) {
            console.log('___ loop : ', loop);

            // Filter orders that match the current `order_id` and `subscription_type_code`
            const matchedOrders = this.subscription_partner_order.filter(item => 
                item.id == loop.order_id[0] && 
                !processedOrders.has(item.id) // Ensure it's not already processed
            );
            console.log('___ matchedOrders : ', matchedOrders);
            // Add unique orders to the result list and mark them as processed
            matchedOrders.forEach(order => {
                order_list.push(order);
                processedOrders.add(order.id);
            });
        }

        console.log('___ order_list : ', order_list);
        return order_list;
    },
});

