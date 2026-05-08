/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { Message } from '@mail/core/common/message';
// import { Message } from "@mail/core/common/message_model";
import { MessagingMenu } from '@mail/core/web/messaging_menu';
// import { PersonaImStatusIcon } from '@mail/components/persona_im_status_icon/persona_im_status_icon';
// import ajax from "@web/legacy/js/core/ajax";
// import core from "@web/legacy/js/services/core";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { ActivityMenu } from '@mail/core/web/activity_menu';
import { DebugMenu } from "@web/core/debug/debug_menu";
// patch(PersonaImStatusIcon.prototype,{
//         _onClick: function (ev) {
//         var self = this;
//         const _super = this._super.bind(this);
//         jsonrpc("/wk/check/mp/seller", "call", {})
//           .then(function (is_seller) {
//             if (!is_seller) {
//               _super(ev);
//             }
//           });
//       },
// })

patch(MessagingMenu.prototype,{
  setup(){
    var res = super.setup()
    console.log('res',res)
    var self = this
    console.log('self',self)
    this.state = useState({
            seller:true
        });
    var seller = useService("user").hasGroup('odoo_marketplace.marketplace_officer_group')
    console.log('seller message menu',seller)
    seller.then(function(data){
      Object.assign(self.state, { seller: data});
    })
    console.log(this.state)
    return res
  },
})

patch(DebugMenu.prototype,{
  setup(){
    var res = super.setup()
    console.log('res',res)
    var self = this
    console.log('self',self)
    this.state = useState({
            seller:true
        });
    var seller = useService("user").hasGroup('odoo_marketplace.marketplace_officer_group')
    console.log('seller',seller)
    seller.then(function(data){
      Object.assign(self.state, { seller: data});
    })
    console.log(this.state)
    return super.setup()
  },
})

patch(ActivityMenu.prototype,{
  setup(){
    var res = super.setup()
    var self = this
    this.seller_info = useState({
            seller:true
        });
    var seller = useService("user").hasGroup('odoo_marketplace.marketplace_officer_group')
    seller.then(function(data){
      Object.assign(self.seller_info, { seller: data});
    })
    return res
  }
})

patch(Message.prototype,{

  setup() {
    var res = super.setup()
    var self = this
    this.noseller = useState({
      noseller:true
        });
  var noseller = useService("user").hasGroup('odoo_marketplace.marketplace_officer_group')
  noseller.then(function(data){
        self.noseller = data
      })
  this.noseller = self.noseller
  return res
},
onClick(ev) {
        console.log('onclick',this.noseller)
        if (!this.noseller){
          console.log('no seller',this.noseller)
          ev.preventDefault(); 
          return false
        }
        return super.onClick(ev)
    },
})
