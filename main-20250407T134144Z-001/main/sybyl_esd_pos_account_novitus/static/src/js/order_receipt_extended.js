/** @odoo-module */
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/store/models";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PaymentScreen.prototype, {
    async _finalizeValidation() {
        const name = this.pos.get_order().name;
        await super._finalizeValidation(...arguments);
        const order = this.pos.get_order();
        const selectedRecords = await this.orm.call("pos.order", "return_data", [null, { name }]);
    }
});

patch(PosStore.prototype, {
    async _save_to_server(orders, options) {
        if (!orders || !orders.length) {
            return Promise.resolve([]);
        }
        this.set_synch("connecting", orders.length);
        options = options || {};

        // Keep the order ids that are about to be sent to the
        // backend. In between create_from_ui and the success callback
        // new orders may have been added to it.
        var order_ids_to_sync = orders.map((o) => o.id);

        for (const order of orders) {
            order.to_invoice = options.to_invoice || false;
        }
        // we try to send the order. silent prevents a spinner if it takes too long. (unless we are sending an invoice,
        // then we want to notify the user that we are waiting on something )
        const orm = options.to_invoice ? this.orm : this.orm.silent;

        try {
            // FIXME POSREF timeout
            // const timeout = typeof options.timeout === "number" ? options.timeout : 30000 * orders.length;
            const serverIds = await orm.call(
                "pos.order",
                "create_from_ui",
                [orders, options.draft || false],
                {
                    context: this._getCreateOrderContext(orders, options),
                }
            );

            for (const serverId of serverIds) {
                const order = this.env.services.pos.orders.find(
                    (order) => order.name === serverId.pos_reference
                );
                const name = order.name
                const selectedRecords = await orm.call("pos.order", "return_data", [null, { name }]);
                order.fiscal_receipt_no = selectedRecords[0]
                console.log('___ order.fiscal_receipt_no : ', order.fiscal_receipt_no);
                order.kra_qr_png_image = selectedRecords[1]
                order.cus_no = selectedRecords[2]
                console.log('___ order.kra_qr_png_image : ', order.kra_qr_png_image);
                if (order) {
                    order.server_id = serverId.id;
                }
            }

            for (const order_id of order_ids_to_sync) {
                this.db.remove_order(order_id);
            }

            this.failed = false;
            this.set_synch("connected");
            return serverIds;
        } catch (error) {
            console.warn("Failed to send orders:", orders);
            if (error.code === 200) {
                // Business Logic Error, not a connection problem
                // Hide error if already shown before ...
                if ((!this.failed || options.show_error) && !options.to_invoice) {
                    this.failed = error;
                    this.set_synch("error");
                    throw error;
                }
            }
            this.set_synch("disconnected");
            throw error;
        }
    }
});


patch(Order.prototype, {
    setup() {
        super.setup(...arguments);
        this.fiscal_receipt_no = this.fiscal_receipt_no || false;
        this.kra_qr_png_image = this.kra_qr_png_image || false;
        this.cus_no = this.cus_no || false;
    },
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        result.fiscal_receipt_no = this.fiscal_receipt_no    
        result.kra_qr_png_image = this.kra_qr_png_image
        result.cus_no = this.cus_no
        return result;
    },
});

