/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.portalDetails = publicWidget.Widget.extend({
    selector: '.add_row_user_lines',
    events: {
        "click .add_row_users": "_AddRowUsers",
    },

    init() {
        this._super(...arguments);
        this.counter = 1;
    },

    start: function() {
        var def = this._super.apply(this, arguments);
        console.log("Start Add Row");
        //  this.counter = 1;
        return def;
    },

    _AddRowUsers: function() {
        console.log("Click Add Row",this.counter);
        this.counter++;

        // Select the existing table
        var table = document.getElementById("user_lines");

        // Create a new row
        var tr = table.insertRow();

        // Add a class to the new row
        tr.classList.add("user_line");

        // Create a cell for the new row
        var td1 = tr.insertCell();

        // Create the input element
        var input_login = document.createElement("input");
        input_login.classList.add("form-control","form-control-sm");
        input_login.setAttribute("type", "text");
        input_login.setAttribute("required", "required");
        input_login.name = "login_" + this.counter;
        input_login.id = "login_" + this.counter;

        // Append the input element to the cell
        td1.appendChild(input_login);

        var td2 = tr.insertCell();

        var input_name = document.createElement("input");
        input_name.classList.add("form-control","form-control-sm");
        input_name.setAttribute("type", "text");
        input_name.setAttribute("required", "required");
        input_name.name = "name_" + this.counter;
        input_name.id = "name_" + this.counter;

        // Append the input element to the cell
        td2.appendChild(input_name);
    },
});