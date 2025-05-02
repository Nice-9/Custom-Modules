//** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { onMounted, useRef, useState } from "@odoo/owl";
import { ConnectionLostError } from "@web/core/network/rpc_service";
import { customerListExtendPopup } from "@bi_pos_scan_mobile_barcode/js/customerListPopupExtend";
import { subscriptionListView } from "@bi_pos_scan_mobile_barcode/js/subscriptionListView";

const CACHE = {};

export class customerListPopup extends AbstractAwaitablePopup {
    static template = "bi_pos_scan_mobile_barcode.customerListPopup";

    static defaultProps = {
        confirmText: _t("Check In"),
        title: _t("Customer List"),
        body: "",
        cancelText: _t("Close"),
    };

    setup() {
        super.setup();
        this.pos = usePos();
        this.rpc = useService("rpc");
        this.popup = useService("popup");
        console.log('___ this : ', this);
        console.log('___ this.props : ', this.props);
        this.customerList = this.props.partnerDetailsList;
        this.dogList = this.props.dogDetailsList;
        this.carList = this.props.carDetailsList;
        var items = JSON.parse(JSON.stringify(this.props.partnerDetailsList))
        var caritems = JSON.parse(JSON.stringify(this.props.carDetailsList))
        var dogitems = JSON.parse(JSON.stringify(this.props.dogDetailsList))
        this.props.items = items;
        this.props.caritems = caritems;
        this.props.dogitems = dogitems;
    }

    load(store, deft) {
            console.log('___ CACHE[store] : ', CACHE[store]);
            if (CACHE[store] !== undefined) {
                return CACHE[store];
            }
            var data = localStorage[this.name + "_" + store];
            console.log('___ dataconfirm load : ', data);
            if (data !== undefined && data !== "") {
                data = JSON.parse(data);
                // CACHE[store] = data;
                return data;
            } else {
                return deft;
            }
        }
        /* saves a record store to the database */
    save(store, data) {
        localStorage[this.name + "_" + store] = JSON.stringify(data);
        // CACHE[store] = data;
    }
    
    redirect_subscription(event, self) {
        // Access the clicked element (button or icon)
        const button = $(event.currentTarget);
        // Get the id attribute value
        const partner_id = button.attr('id'); // Just get the id, no need for $(...)
        // Get the data-code attribute value
        const subscription_code = button.attr('data-code');
        if(subscription_code == 'MEM'){
            var subscription_desc = 'Membership'
        }else if(subscription_code == 'AEP'){
            var subscription_desc = 'Annual Entry Pass'
        }else if(subscription_code == 'CPP'){
            var subscription_desc = 'Annual Car Parking Pass'
        }else if(subscription_code == 'DEP'){
            var subscription_desc = 'Annual Dog Entry Pass'
        }else{
            var subscription_desc = 'Subscription'
        }

        // Log the values
        console.log('___ partner_id : ', partner_id);
        console.log('___ subscription_code : ', subscription_code);
        var partner_subscriptions = self.pos.get_subscriptions_by_partner_id(partner_id,subscription_code);
        partner_subscriptions = partner_subscriptions.map(proxyObj => Object.assign({}, proxyObj));
        console.log('___ partner_subscriptions : ', partner_subscriptions);
        console.log('___ subscriptionListView : ', subscriptionListView);
        self.popup.add(subscriptionListView, { partner_subscriptions,title: _t(subscription_desc)});

    }

    toggleDiv(event) {
        console.log('___ event : ', event);
        const button = $(event.currentTarget);
        const targetDiv = $(button.data('target'));

        // Hide all other divs
        $('.pass-holders, .dogs-details, .cars-details').not(targetDiv).hide();

        // Toggle the target div
        if (targetDiv.is(':visible')) {
            targetDiv.hide();
            button.text('+'); // Change button text back to '+'
        } else {
            targetDiv.show();
            button.text('-'); // Change button text to '-'
        }
    }

    async onClick() {
        var self = this;
        // var checkboxes = $("input:checkbox.check-in-out");
        // var customer_checklist_dict = [];

        // checkboxes.each(function(index, obj) {
        //     const checklist_dict = { "id": parseInt(obj.id), "checked": true }
        //     customer_checklist_dict.push(checklist_dict);
        // });

        // console.log("customer_checklist_dict props", customer_checklist_dict);
        // var updated = false;

        // var partnerDetailsList = []
        // customer_checklist_dict.forEach(function(item) {
        //     var id = item.id;
        //     var checked = item.checked;
        //     var partnerDetails = self.pos.db.get_partner_by_id(id);
        //     console.log('___ partnerDetails : ', partnerDetails);

        //     if (partnerDetails) {
        //         // Update check_in_out_state based on checked value
        //         if (checked) {
        //             if (partnerDetails.check_in_out_state) {
        //                 partnerDetails.check_in_out_state = false;
        //                 updated = true;
        //             } else {
        //                 partnerDetails.check_in_out_state = true;
        //                 updated = true;
        //             }
        //             console.log('___ partnerDetails : ', partnerDetails);
        //             partnerDetailsList.push(partnerDetails)
        //         }
        //     } else {
        //         console.log('Partner details not found for id:', id);
        //     }
        // });

        // // if (updated) {
        // var response = { "state": "updated" };
        // try {
        //     // 1. Save Updated to server.
        //     var syncOrderResult = await this.pos.push_state_updates(customer_checklist_dict);
        //     console.log('___ syncOrderResult : ', syncOrderResult);
        // } catch (error) {
        //     if (error instanceof ConnectionLostError) {
        //         var updated_status = this.load("updated_status", []);
        //         customer_checklist_dict.forEach(function(item) {
        //             updated_status.push(item);
        //             self.save("updated_status", updated_status);
        //         });
        //     } else {
        //         throw error;
        //     }
        // }
        // console.log(response);
        // this.props.close();
        var partnerDetailsList_extend = self.props.partnerDetailsList
        var dogDetailsList = self.props.dogDetailsList
        var carDetailsList = self.props.carDetailsList
        var allpartnerDetailsList = self.props.allpartnerDetailsList
        console.log('___ this.popup : ', this.popup);
        this.props.close();
        self.popup.add(customerListExtendPopup, { allpartnerDetailsList,dogDetailsList,carDetailsList });

    }

    async onAllCheck(event) {
        console.log("onAllCheck customerListPopup");
        var self = this;
        var checkboxes = $("input:checkbox.check-in-out");
        var allCheck = document.getElementById("allcb");

        if ($(allCheck).prop("checked")) {
            checkboxes.each(function() {
                $(this).prop("checked", true);
            });
        } else {
            checkboxes.each(function() {
                $(this).prop("checked", false);
            });
        }
    }
}