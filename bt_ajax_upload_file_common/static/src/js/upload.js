/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";
import { renderToElement } from "@web/core/utils/render";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.SurveyUploadFile = publicWidget.Widget.extend({
    selector: '.upload-files',

    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.file_loaded = false;
        this.readonly = options.readonly;
        this.options = options.readonly;
    },
    start: function () {
        var self = this;
        var $inputFile = this.$target.find(".input-file");
        var files_ids = [];
        var input_name = $inputFile.attr('data-name');
        var res_model = $inputFile.attr('res-model');
        var res_id = $inputFile.attr('data-res-id');
        var question_id = $inputFile.attr('data-name');
        var data_type = $inputFile.attr('data-file');
        var max_file_size = $inputFile.attr('max-file-size');
        var multifile = $inputFile.attr('multi-file');
        var maxFileSize = 500 * 1024;
        var ufiles = this.$target.find('input');
        var show_del = $inputFile.attr('show-delete');
        var show_del = show_del=="true" ?  true : false;
        var multifile = multifile=="true" ?  true : false;

        var show_download = $inputFile.attr('show-download');
        var show_download = show_download=="true" ?  true : false;
        if(this.readonly !== undefined){
            show_del = !this.readonly;
            show_download = !this.readonly;
        }
        var totalfilesize = 0;
        $inputFile.uploadFile({
            url: '/upload/attachment/onchange',
            fileName: 'attachments',
            multiple: multifile,
            maxFileCount: multifile ?  99 : 1,
            maxFileSize: maxFileSize,
            showDelete: show_del,
            showDownload: show_download,
            formData: {'res_id': res_id, 'res_model': res_model},
            onSelect: function (files) {
                var totalfilesize_select = 0;
                const ALLOWED_FILE_TYPES = [];
                const invalidFiles = [];
                const file_type = [];
                for(var i=0;i<files.length;i++){
                    totalfilesize_select += files[i].size;
                }
                if((totalfilesize+totalfilesize_select)>maxFileSize){
                    alert("The maximum size for all your attachments is 500 KB, please compress your files if required");
                    return false;
                }
                if (data_type == 'document') {
                    ALLOWED_FILE_TYPES.push('application/pdf', );
                    file_type.length = 0;
                    file_type.push(data_type);
                } else {
                    ALLOWED_FILE_TYPES.push('image/jpeg',
                        'image/jpg',
                    );
                    file_type.length = 0;
                    file_type.push(data_type);
                }
                for (let i = 0; i < files.length; i++) {
                    // totalfilesize_select += files[i].size;
                    if (!ALLOWED_FILE_TYPES.includes(files[i].type)) {
                        invalidFiles.push(files[i].name);
                    }
                }
                if(invalidFiles.length > 0)
                {
                    if (file_type[0] == 'document') {
                        alert("Unsupported file. File must be a document in (.pdf) format.");
                        return false;
                    } else {
                        alert("Unsupported file. File must be an image in (.jpg / .jpeg) format.");
                        return false;
                    }
                }
                totalfilesize += totalfilesize_select;
                return true;
            },
            deleteCallback: function(data, pd){
                jsonrpc('/upload/attachment/delete', {
                    'attachment_id': data,
                }).then(function(response){
                    var index = files_ids.indexOf(response[0]);
                    if (index > -1) {
                        files_ids.splice(index, 1);
                        totalfilesize -= response[1];
                    }
                    ufiles.val(files_ids.toString())
                });
            },
            onLoad:function(obj){
                jsonrpc('/upload/attachment/onload', {
                    'res_model': res_model,
                    'res_id': res_id,
                    'files_ids': ufiles.val()
                }).then(function(data){
                    for(var i=0;i<data.length;i++)
                    {
                        obj.createProgress(data[i]["path"], data[i]["name"], data[i]["size"]);
                        files_ids.push(data[i]["path"]);
                        totalfilesize += data[i]["size"];
                    }
                    ufiles.val(files_ids.toString());
                    if (data.length <= 0){
                        var $noattachment = $('form').find('.no-attachment');
                        if ($noattachment.length <= 0){
                            $noattachment = $('div').find('.no-attachment');
                        }
                        if ($noattachment.length > 0){
                            $noattachment.show();
                        }
                    }
                    self.file_loaded = true;
                })
            },
            onSuccess: function (files, response, xhr, pd) {
                files_ids.push(response);
                ufiles.val(files_ids.toString())
            },
            downloadCallback:function(filename, pd)
            {
                window.open(
                  "/web/content/"+filename,
                  '_blank'
                );
            },
            uploadButtonClass: "btn browse-btn",
            uploadStr: '<i class="fa fa-paperclip"></i>  &#160; Select Files',
            dragDropStr: "<span><b>Drag &amp; Drop Files Here</b></span>",
            sizeErrorStr: "is not allowed. Allowed Max size:",
            maxFileCountErrorStr: " is not allowed. Maximum allowed files are: ",
            statusBarWidth:350,
            dragdropWidth:350,
        });


        if(show_del==false){
            $inputFile.hide('form');
        }
        $('.btn-bs-file input').on('change', function(event) {
            var file_text = $(this).parent().parent().find('span');
            if( this.files.length > 1) {
                file_text.text(this.files.length +' files selected');
            } else if( this.files.length == 1) {
                file_text.text(this.files[0].name);
            } else {
                file_text.text('No file choosen');
            }

        });
    },

})