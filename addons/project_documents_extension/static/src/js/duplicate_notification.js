odoo.define('project_documents_extension.duplicate_notification', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var Dialog = require('web.Dialog');

    var _t = core._t;

    var DuplicateNotification = Widget.extend({
        template: 'duplicate_notification_template',
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.message = options.message || '';
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                // Show the notification as a modal dialog
                var dialog = new Dialog(self, {
                    title: _t('Duplicate Document Detected'),
                    $content: $('<div>').text(self.message),
                    buttons: [{
                        text: _t('OK'),
                        close: true,
                        classes: 'btn-primary'
                    }]
                });
                dialog.open();
            });
        }
    });

    // Listen for duplicate warning messages in chatter
    $(document).on('click', '.o_mail_thread .o_message_content', function () {
        var $message = $(this);
        var messageText = $message.text();
        
        if (messageText.includes('🚨 POPUP_WARNING:')) {
            // Extract the warning message
            var warningMessage = messageText.replace('🚨 POPUP_WARNING:', '').trim();
            
            // Show popup notification
            var notification = new DuplicateNotification(null, {
                message: warningMessage
            });
            notification.appendTo($('body'));
        }
    });

    return DuplicateNotification;
}); 