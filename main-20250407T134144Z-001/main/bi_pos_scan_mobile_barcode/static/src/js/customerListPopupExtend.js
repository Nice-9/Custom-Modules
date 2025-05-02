//** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { onMounted, useRef, useState } from "@odoo/owl";
import { ConnectionLostError } from "@web/core/network/rpc_service";
const CACHE = {};
import { deserializeDateTime, formatDateTime, parseDateTime } from "@web/core/l10n/dates";

export class customerListExtendPopup extends AbstractAwaitablePopup {
    static template = "bi_pos_scan_mobile_barcode.customerListExtendPopup";

    static defaultProps = {
        confirmText: _t("Confirm"),
        title: _t("Customer Data List"),
        body: "",
        cancelText: _t("Close"),
    };

    setup() {
        super.setup();
        this.pos = usePos();
        this.rpc = useService("rpc");
        console.log('___ this.props : ', this.props);
        this.customerList = this.props.allpartnerDetailsList;
        console.log('___ this.customerList : ', this.customerList);
        this.dogList = this.props.dogDetailsList;
        this.carList = this.props.carDetailsList;
        var items = JSON.parse(JSON.stringify(this.props.allpartnerDetailsList))
        var caritems = JSON.parse(JSON.stringify(this.props.carDetailsList))
        var dogitems = JSON.parse(JSON.stringify(this.props.dogDetailsList))
        this.props.items = items;
        this.props.caritems = caritems;
        this.props.dogitems = dogitems;
        console.log('___ this.props : ', this.props);
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

    toggleDiv(event) {
        // console.log('___ event : ', event);
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

    getDate(next_vaccination_date) {
        const date = new Date(next_vaccination_date);

        // Get the day, month, and year from the Date object
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
        const year = date.getFullYear();

        // Format the date as DD/MM/YYYY
        const formattedDate = `${day}/${month}/${year}`;

        console.log(formattedDate); // Output: 29/01/2025
        return formattedDate;
    }



    async onClick() {
        console.log("onClick customerListExtendPopup");
        var self = this;
        var checkboxes = $("input:checkbox.check-in-out");
        var customer_checklist_dict = [];
        console.log('___ checkboxes : ', checkboxes);
        checkboxes.each(function(index, obj) {
            if (obj.id.startsWith('dog_')) {
                let dogId = obj.id.substring(4); // Extract part after 'dog_'
                var checklist_dict = { "id": false, "checked": obj.checked ,"dog_id":parseInt(dogId),"car_id":false}
            } else if (obj.id.startsWith('car_')) {
                let carId = obj.id.substring(4); // Extract part after 'car_'
                var checklist_dict = { "id": false, "checked": obj.checked ,"dog_id":false,"car_id":parseInt(carId)}
            }else{
                var checklist_dict = { "id": parseInt(obj.id), "checked": obj.checked ,"dog_id":false,"car_id":false}
            }
            customer_checklist_dict.push(checklist_dict);
        });

        console.log("customer_checklist_dict props", customer_checklist_dict);
        var updated = false;

        // var partnerDetailsList = []
        customer_checklist_dict.forEach(function(item) {
            var id = item.id;
            var checked = item.checked;
            var dog_id = item.dog_id;
            var car_id = item.car_id;
            if (id){
                var CheckInOutDetails = self.pos.db.get_partner_by_id(id);

            }else if(dog_id){
                var CheckInOutDetails = self.pos.get_dog_by_id(dog_id);

            }else if(car_id){
                var CheckInOutDetails = self.pos.get_car_by_id(car_id);

            }else{
                var CheckInOutDetails = false;
            }
            if (CheckInOutDetails) {
                // Update check_in_out_state based on checked value
                console.log('___ CheckInOutDetails before: ', CheckInOutDetails);
                if (checked) {
                    if (CheckInOutDetails.check_in_out_state) {
                        CheckInOutDetails.check_in_out_state = false;
                        updated = true;
                    } else {
                        CheckInOutDetails.check_in_out_state = true;
                        updated = true;
                    }
                    console.log('___ CheckInOutDetails : ', CheckInOutDetails);
                    // partnerDetailsList.push(partnerDetails)
                }
            } else {
                console.log('PARTNER Or DOG Or CAR details not found for id:', id);
            }
        });

        // if (updated) {
        var response = { "state": "updated" };
        try {
            // 1. Save Updated to server.
            var syncOrderResult = await this.pos.push_state_updates(customer_checklist_dict);
            console.log('___ syncOrderResult : ', syncOrderResult);
        } catch (error) {
            if (error instanceof ConnectionLostError) {
                var updated_status = this.load("updated_status", []);
                customer_checklist_dict.forEach(function(item) {
                    updated_status.push(item);
                    self.save("updated_status", updated_status);
                });
            } else {
                throw error;
            }
        }
        console.log(response);
        this.props.close();
    }

    async onAllCheck(event) {
        console.log("onAllCheck customerListExtendPopup");
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