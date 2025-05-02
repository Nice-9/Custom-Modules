//** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { onMounted, useRef, useState } from "@odoo/owl";
//import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { customerListPopup } from "@bi_pos_scan_mobile_barcode/js/customerListPopup";
import { ConnectionLostError } from "@web/core/network/rpc_service";
const CACHE = {};
import { loadJS } from "@web/core/assets";
var qrScannerGlobal;

// const QrScanner = require('path/to/qr-scanner.umd.min.js'); // if not installed via package
// import QRScanner  from "@bi_pos_scan_mobile_barcode/qr-scanner/qr-scanner.umd.min.js";
// import QrScanner from "@bi_pos_scan_mobile_barcode/../qr-scanner.min.js";
// import QrScanner from 'path/to/qr-scanner.min.js';
// import QRScanner from 'https://unpkg.com/qr-scanner/qr-scanner.min.js';
// console.log('___ QRScanner : ', QrScanner);


export class scanqrcodecustomer extends AbstractAwaitablePopup {
    static template = "bi_pos_scan_mobile_barcode.scanqrcode";

    static defaultProps = {
        confirmText: _t("OK"),
        title: _t("Scanning QrCode for Customer"),
        body: '',
        cancelText: _t("Close"),
    };

    setup() {
        super.setup();
        this.pos = usePos();
        this.rpc = useService('rpc');
        this.sound = useService("sound");
        this.popup = useService("popup");
        this.state = useState({
            codeFound: '',
        });
        this.updateStatus();
    };

    load(store, deft) {
        var data = localStorage[this.name + "_" + store];
        console.log('___ data : ', data);
        if (data !== undefined && data !== "") {
            data = JSON.parse(data);
            CACHE[store] = data;
            return data;
        } else {
            return deft;
        }
    };

    /* saves a record store to the database */
    save(store, data, val) {
        if (val) {
            localStorage[this.name + "_" + store] = [];
            CACHE[store] = [];
        } else {
            /* saves a record store to the database */
            localStorage[this.name + "_" + store] = JSON.stringify(data);
            CACHE[store] = data;
        }
    };

    async updateStatus() {
        await loadJS("/bi_pos_scan_mobile_barcode/static/src/qr-scanner/qr-scanner.umd.min.js");
        try {
            // 1. Save Updates to server.
            this.pos.offline_status_updates = []
            var updated_status = this.load("updated_status", []);
            var syncResult = await this.pos.push_state_updates(updated_status);
            if (syncResult && syncResult.state == 'updated') {
                this.save("updated_status", [], true);
            }
            this.initializeQRScanner()
        } catch (error) {
            if (error instanceof ConnectionLostError) {
                // this.pos.showScreen(this.nextScreen);
                // onMounted(this.onMounted);
                this.initializeQRScanner()
                Promise.reject(error);
                // return error;
            } else {
                throw error;
            }
        }
    };

    onMounted() {
        this.initializeQRScanner()
    };

    setResult(label, result) {
        console.log(result.data);
        label.textContent = result.data;
    };

    requestCameraAccess() {
        navigator.mediaDevices.getUserMedia({ video: true })
        .then((stream) => {
            // Access granted, stream the video to an element
            const video = document.getElementById('qr-video');
            video.srcObject = stream;
            video.play();
        })
        .catch((error) => {
            // Handle the error (e.g., user denied access)
            console.error('Camera access denied:', error);
            alert('Camera access denied or not available.');
        });
    }


    async initializeQRScanner() {
        const video = document.getElementById('qr-video');
        const video_permission = document.getElementById('cameraPermissionSection');
        const result = document.getElementById('result');
        // const result = document.getElementById('result');
        const camQrResult = document.getElementById('cam-qr-result');

        // QRScanner.WORKER_PATH = '/your_module/static/src/js/qr-scanner-worker.min.js'; // Path to worker

        // const qrScanner = new QrScanner(video, function (qrCode) {
        //     result.textContent = qrCode;
        //     qrScanner.stop();
        //     // You can add logic here to send the scanned code back to the Odoo server
        //     console.log("QR Code Scanned: ", qrCode);
        // });

        const qrScanner = new QrScanner(
            video,
            result => {
                console.log('decoded qr code:', result);

                this.onScanSuccess(result,qrScanner) // Stop the scanner after successfully decoding the QR code
            },
            { 
                onDecodeError: error => {
                    console.log('decoded qr code: error', error);
                },
                maxScansPerSecond: 1
                /* your options or returnDetailedScanResult: true if you're not specifying any other options */
            }
        );

        qrScannerGlobal = qrScanner

        // try {
            // const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            // stream.getTracks().forEach(track => track.stop());
            // navigator.mediaDevices.enumerateDevices()
            // .then(devices => {
            //     const videoDevices = devices.filter(device => device.kind === 'videoinput');
            //     if (videoDevices.length > 0) {
            //         console.log("Camera is available.");
            //     } else {
            //         console.log("No camera available.");
            //     }
            // })
            // .catch(err => {
            //     console.error("Error accessing media devices: ", err);
            // });
            // console.log('___ qrScanner : ', qrScanner);
        qrScanner.start().then(() => {
            // Success callback when the scanner starts
            console.log('Camera access granted here lala');
            video.style.display = 'block';
            video_permission.style.display = 'none';
            console.log("Scanner started successfully.");
        }).catch((err) => {
            // Error occurred
            console.log('___ video : ', video);
            console.log('___ video_permission : ', video_permission);
            video.style.display = 'none';
            video_permission.style.display = 'block';
            console.error("Error occurred while starting scanner:", err);
            // You can call stop() to stop the scanner here
            // qrScanner.stop().then(() => {
            //     console.log("Scanner stopped.");
            // }).catch((stopErr) => {
            //     console.error("Error occurred while stopping scanner:", stopErr);
            // });
        });
        

        const fileSelector = document.getElementById('file-selector');
        const fileQrResult = document.getElementById('file-qr-result');
        fileSelector.addEventListener('change', event => {
        const file = fileSelector.files[0];
        if (!file) {
            return;
        }
            QrScanner.scanImage(file, { returnDetailedScanResult: true })
                .then(result =>
                {
                    console.log('___ result : ', result);
                fileSelector.value = '';
                this.onScanSuccess(result,qrScanner)  
                }
                    )
                .catch(e => {
                    console.log("QR Scanning Error",e)
                    fileSelector.value = '';

                });

        });

    }

    onScanSuccess(result, qrScanner){
        var self = this
        if (self.pos.config.customer_scan) {
            if (result.data) {
                var customerList = ''
                var res1 = self.pos.db.get_partners_sorted(1000000);
                var foundItem = res1.find(item => item['qr_sequence'] === result.data);
                if (foundItem) {
                    customerList = foundItem;
                }
                if (!customerList) {
                    console.log("No Customer Found");
                    $.iaoAlert({
                        msg: "Warning: No matching records found. Retry with a valid QR code",
                        type: "error",
                        autoHide: true,
                        alertTime: "3000",
                        closeButton: true,
                        mode: "dark",
                    })
                    if (self.sound) {
                        self.sound.play("error");
                    }
                    qrScanner.stop();
                    // self.popup.add(scanqrcodecustomer, {});
                    qrScanner.start();
                    // html5QrcodeScanner.pause();
                    // html5QrcodeScanner.clear();
                }
                var partnerDetailsList = []
                var allpartnerDetailsList = []
                var childpartnerDetailsList = []
                var dogDetailsList = []
                var carDetailsList = []
                partnerDetailsList.push(customerList)
                allpartnerDetailsList.push(customerList)
                // print ('___ customerList : ', customerList);
                // console.log('___ customerList : ', customerList);
                if (customerList) {
                    customerList.child_ids.forEach(id => {
                        var partnerDetails = self.pos.db.get_partner_by_id(id);
                        if (partnerDetails) {
                            childpartnerDetailsList.push(partnerDetails);
                            allpartnerDetailsList.push(partnerDetails);
                        }
                    });
                    customerList.dog_ids.forEach(id => {
                        var dogDetails = self.pos.get_dog_by_id(id);
                        if (dogDetails) {
                            dogDetailsList.push(dogDetails);
                        }
                    });
                    customerList.car_ids.forEach(id => {
                        var carDetails = self.pos.get_car_by_id(id);
                        if (carDetails) {
                            carDetailsList.push(carDetails);
                        }
                    });
                    partnerDetailsList = partnerDetailsList.map(proxyObj => Object.assign({}, proxyObj));
                    allpartnerDetailsList = allpartnerDetailsList.map(proxyObj => Object.assign({}, proxyObj));
                    childpartnerDetailsList = childpartnerDetailsList.map(proxyObj => Object.assign({}, proxyObj));
                    carDetailsList = carDetailsList.map(proxyObj => Object.assign({}, proxyObj));
                    dogDetailsList = dogDetailsList.map(proxyObj => Object.assign({}, proxyObj));
                    var expiredPartnerDetailsList = partnerDetailsList.filter(partner => partner.subscription_state === "expired");
                    if (expiredPartnerDetailsList.length) {
                        console.log("Customer subscription Expired");
                        $.iaoAlert({
                            msg: "Customer: Subscription Expired, Please Subscribe.",
                            type: "error",
                            mode: "dark",
                            autoHide: true,
                            alertTime: "3000",
                            closeButton: true,
                        })
                        if (self.sound) {
                            self.sound.play("error");
                        }
                        qrScanner.stop();
                        // html5QrcodeScanner.pause();
                        // html5QrcodeScanner.clear();
                    } else {
                        self.popup.add(customerListPopup, { partnerDetailsList,childpartnerDetailsList,dogDetailsList,carDetailsList,allpartnerDetailsList });
                        $.iaoAlert({
                            msg: "Customer: Found Successfully.",
                            type: "notification",
                            mode: "dark",
                            autoHide: true,
                            alertTime: "3000",
                            closeButton: true,
                        })
                        if (self.sound) {
                            self.sound.play("bell");
                        }
                        qrScanner.stop();
                    }
                }
            }
        }

    }


    async onClick() {
        var self = this;
        console.log('___ self allalalalalalalalal: ', self);
        console.log('___ self allalalalalalalalal: ', self);
        console.log('___ self allalalalalalalalal: ', self);
        qrScannerGlobal.stop()
        this.props.close();
    }
    async onClickCancel() {
        var self = this;
        qrScannerGlobal.stop()
        this.props.close();
    }

    // _startCamera() {
    //     var self = this
    //     // var html5QrcodeScanner = false

    //     function onScanSuccess(decodedText, decodedResult) {
    //         // Handle on success condition with the decoded text or result.
    //         if (self.pos.config.customer_scan) {
    //             if (decodedText) {
    //                 var customerList = ''
    //                     // if (this.state.query && this.state.query.trim() !== "") {
    //                 var res = self.pos.db.search_partner();
    //                 // } else {
    //                 var res1 = self.pos.db.get_partners_sorted(1000000);
    //                 var foundItem = res1.find(item => item['qr_sequence'] === decodedText);
    //                 if (foundItem) {
    //                     customerList = foundItem;
    //                 }
    //                 if (!customerList) {
    //                     console.log("No Customer Found");
    //                     $.iaoAlert({
    //                         msg: "Warning: No matching customer found for the scanned QR Code!",
    //                         type: "error",
    //                         autoHide: true,
    //                         alertTime: "3000",
    //                         closeButton: true,
    //                         mode: "dark",
    //                     })
    //                     if (self.sound) {
    //                         self.sound.play("error");
    //                     }
    //                     html5QrcodeScanner.pause();
    //                     html5QrcodeScanner.clear();
    //                 }
    //                 var partnerDetailsList = []
    //                 partnerDetailsList.push(customerList)
    //                 if (customerList) {
    //                     customerList.child_ids.forEach(id => {
    //                         var partnerDetails = self.pos.db.get_partner_by_id(id);
    //                         if (partnerDetails) {
    //                             partnerDetailsList.push(partnerDetails);
    //                         }
    //                     });
    //                     partnerDetailsList = partnerDetailsList.map(proxyObj => Object.assign({}, proxyObj));
    //                     var expiredPartnerDetailsList = partnerDetailsList.filter(partner => partner.subscription_state === "expired");
    //                     if (expiredPartnerDetailsList.length) {
    //                         console.log("Customer subscription Expired");
    //                         $.iaoAlert({
    //                             msg: "Customer: Subscription Expired, Please Subscribe.",
    //                             type: "error",
    //                             mode: "dark",
    //                             autoHide: true,
    //                             alertTime: "3000",
    //                             closeButton: true,
    //                         })
    //                         if (self.sound) {
    //                             self.sound.play("error");
    //                         }
    //                         html5QrcodeScanner.pause();
    //                         html5QrcodeScanner.clear();
    //                     } else {
    //                         self.popup.add(customerListPopup, { partnerDetailsList });
    //                         $.iaoAlert({
    //                             msg: "Customer: Found Successfully.",
    //                             type: "notification",
    //                             mode: "dark",
    //                             autoHide: true,
    //                             alertTime: "3000",
    //                             closeButton: true,
    //                         })
    //                         if (self.sound) {
    //                             self.sound.play("bell");
    //                         }
    //                         html5QrcodeScanner.pause();
    //                         html5QrcodeScanner.clear();
    //                     }
    //                 }
    //             }
    //         }
    //         html5QrcodeScanner.clear().then(_ => {
    //             // the UI should be cleared here
    //         }).catch(error => {
    //             // Could not stop scanning for reasons specified in `error`.
    //             // This conditions should ideally not happen.
    //         });
    //     }

    //     function onScanFailure(error) {
    //         // handle scan failure, usually better to ignore and keep scanning.
    //         // for example:
    //         console.warn('Code scan error = ${error}');
    //     }

    //     var html5QrcodeScanner = new Html5QrcodeScanner(
    //     "reader", { fps: 20, qrbox: {width: 250,height: 250} });
    //     html5QrcodeScanner.render(onScanSuccess, onScanFailure);


    //     // var html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 100 });
    //     // html5QrcodeScanner.render(onScanSuccess, onScanFailure);
    // }
}