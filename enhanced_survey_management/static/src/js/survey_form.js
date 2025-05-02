/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import SurveyPreloadImageMixin from "@survey/js/survey_preload_image_mixin";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.SurveyForm = publicWidget.Widget.extend(SurveyPreloadImageMixin, {
    selector: '.o_survey_form',
    events: {
        'focus .o_select_Country': '_onSelectCountry',
        'change .o_select_Country': '_onSelectState',
        'change .o_select_many2many': '_onSelectMany2many',
        'change .o_survey_upload_file': '_onFileChange',
    },
    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
    },
    _onSelectCountry: async function(ev) {
        /*
         * method to load country
         */
        var self = this;
        await jsonrpc(
            '/survey/load_country', {},
        ).then(function(result) {
            var count = 0;
            self.$el.find(`#${ev.target.id}`).html('<option value="">Country</option>')
            result['id'].forEach(element => {
                self.$el.find(`#${ev.target.id}`).append(
                    `<option value='${result['name'][count]}'>${result['name'][count]}</option>`
                )
                count += 1
            })
        });
    },
    _onSelectState: async function(ev) {
        /*
         * method to load states
         */
        var self = this
        var country_id = ev.target.value
        var question_id = ev.target.dataset.id
            // rpc.query({
        await jsonrpc(
            '/survey/load_states', { country_id: country_id },
        ).then(function(result) {
            var count = 0;
            self.$el.find(`#${question_id}-state`).html('<option value="">State</option>')
            result['id'].forEach(element => {
                self.$el.find(`#${question_id}-state`).append(
                    `<option value="${result['name'][count]}">${result['name'][count]}</option>`
                )
                count += 1
            })
        });
    },
    _onSelectMany2many: function(ev) {
        /*
         * method to add selected items to input
         */
        this.$el.find('.o_select_many2many_text').val(this.$el.find('.o_select_many2many').val())
    },
    /** On adding file function */
    _onFileChange: async function(event) {
        var self = this;
        var files = event.target.files;
        var question_id = event.target.name
        const ALLOWED_FILE_TYPES = [];
        const file_type = [];
        await jsonrpc(
            '/survey/fetch_filetype', { question_id: question_id },
        ).then(function(result) {
            if (result == 'document') {
                ALLOWED_FILE_TYPES.push('application/pdf', );
                file_type.push(result)
            } else {
                ALLOWED_FILE_TYPES.push('image/jpeg',
                    'image/jpg',
                );
            }
        });
        var fileNames = [];
        var dataURLs = [];
        var totalfilesize_select = 0
        const invalidFiles = [];
        const MAX_FILE_SIZE = 500 * 1024; // 500 KB in bytes
        var fileList = document.getElementById('fileList');
        fileList.innerHTML = '';
        for (let i = 0; i < files.length; i++) {
            totalfilesize_select += files[i].size;
            if (!ALLOWED_FILE_TYPES.includes(files[i].type)) {
                invalidFiles.push(files[i].name);
            }
        }
        console.log('___ invalidFiles : ', invalidFiles);
        console.log('___ totalfilesize_select : ', totalfilesize_select);
        if (totalfilesize_select < MAX_FILE_SIZE && invalidFiles.length == 0) {
            for (let i = 0; i < files.length; i++) {
                var file = files[i];
                var reader = new FileReader();
                reader.readAsDataURL(files[i]);
                reader.onload = function(e) {
                    var file = files[i];
                    var filename = file.name;
                    var dataURL = e.target.result.split(',')[1]; /**  split base64 data */
                    fileNames.push(filename);
                    dataURLs.push(dataURL);
                    /**  Set the data-oe-data and data-oe-file_name attributes of the input element self call el */
                    var $input = self.$el.find('input.o_survey_upload_file');
                    $input.attr('data-oe-data', JSON.stringify(dataURLs));
                    $input.attr('data-oe-file_name', JSON.stringify(fileNames));
                    // Create file list elements
                    var fileList = document.getElementById('fileList');
                    fileList.innerHTML = ''; // clear previous contents of file list
                    var ul = document.createElement('ul');
                    fileNames.forEach(function(fileName) {
                        var li = document.createElement('li');
                        li.textContent = fileName;
                        ul.appendChild(li);
                    });
                    // Create delete button
                    var deleteBtn = document.createElement('button');
                    deleteBtn.textContent = 'Delete All';
                    deleteBtn.addEventListener('click', function() {
                        // Clear file list
                        fileList.innerHTML = '';
                        // Clear input field attributes
                        $input.attr('data-oe-data', '');
                        $input.attr('data-oe-file_name', '');
                        self.$el.find('input[type="file"]').val('');
                    });
                    // Append file list and delete button to file input container
                    fileList.appendChild(ul);
                    fileList.appendChild(deleteBtn);
                }
            }
        } else {
            var fileList = document.getElementById('fileList');
            fileList.innerHTML = '';
            self.$el.find('input[type="file"]').val('');
            if (file_type[0] == 'document') {
                alert("Unsupported file. The maximum allowed file size is 500KB, and the file must be a document in (.pdf) format.");
            } else {
                alert("Unsupported file. The maximum allowed file size is 500KB, and the file must be an image in (.jpg / .jpeg) format.");
            }
        }
    },
});