/** @odoo-module **/

import BoardView from 'board.BoardView';
import core from 'web.core';
import { renderToString } from "@web/core/utils/render";


const { blockDom, Component, useState, useRef } = owl;

BoardView.prototype.config.Controller.include({
    // custom_events: _.extend({}, BoardView.prototype.config.Controller.prototype.custom_events, {
        saveBoard() {
            const templateFn = renderToString.app.getTemplate("board.arch");
            const bdom = templateFn(this.board, {});
            const root = document.createElement("rendertostring");
            blockDom.mount(bdom, root);
            const result = xmlSerializer.serializeToString(root);
            const arch = result.slice(result.indexOf("<", 1), result.indexOf("</rendertostring>"));
    
            this.rpc("/web/view/edit_custom", {
                custom_id: this.customViewId !=null? this.customViewId:'',
                arch: arch,
            });
            this.env.bus.trigger("CLEAR-CACHES");
        }
});

    // /**
    //  * Actually save a dashboard
    //  * @override
    //  *
    //  * @returns {Promise}
    //  */
    // _saveDashboard: function () {
    //     const templateFn = renderToString.app.getTemplate("board.arch");
    //     const bdom = templateFn(this.board, {});
    //     const root = document.createElement("rendertostring");
    //     blockDom.mount(bdom, root);
    //     const result = xmlSerializer.serializeToString(root);
    //     const arch = result.slice(result.indexOf("<", 1), result.indexOf("</rendertostring>"));

    //     this.rpc("/web/view/edit_custom", {
    //         // real code:
    //         custom_id: this.board.customViewId,
    //         arch,
    //         // edited code:
    //         // custom_id: this.customViewId !=null? this.customViewId:'',
    //         // arch: arch,
    //     });
    //     this.env.bus.trigger("CLEAR-CACHES");
    // },
