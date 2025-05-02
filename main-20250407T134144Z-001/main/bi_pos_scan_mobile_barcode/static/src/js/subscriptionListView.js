//** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";

export class subscriptionListView extends AbstractAwaitablePopup {
    static template = "bi_pos_scan_mobile_barcode.subscriptionListPopup";

    static defaultProps = {
        confirmText: _t("Ok"),
        title: _t("Subscriptions"),
        body: "",
        cancelText: _t("Close"),
    };

    setup() {
        super.setup();
        this.customerList = this.props.partner_subscriptions;
        var items = JSON.parse(JSON.stringify(this.props.partner_subscriptions))
        this.props.items = items;
        this.props.is_data = false;
        if(items.length){this.props.is_data = true;}
    }

    async onClick() {
        this.props.close();
    }

    getDate(date_d) {
        const date = new Date(date_d);

        // Get the day, month (short format), and year from the Date object
        const day = String(date.getDate()).padStart(2, '0');
        const month = date.toLocaleString('en-GB', { month: 'short' }); // 'Jan', 'Feb', etc., converted to lowercase
        const year = date.getFullYear();

        // Format the date as DD-MMM-YYYY (e.g., 29-jan-2025)
        const formattedDate = `${day}-${month}-${year}`;

        console.log(formattedDate); // Output: 29-jan-2025
        return formattedDate;
    }

    isNextInvoiceDateValid(next_invoice_date) {
        const currentDate = new Date(); // Get the current date
        const vaccinationDate = new Date(next_invoice_date); // Convert the input date to a Date object

        // Compare the two dates
        if (vaccinationDate > currentDate) {
            return true;  // next_vaccination_date is in the future
        } else {
            return false; // next_vaccination_date is in the past or today
        }
    }
}