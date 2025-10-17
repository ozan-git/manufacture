/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";

patch(ListController.prototype, "quality_control_oca.ExportAllPatch", {
    setup() {
        this._super(...arguments);
        this._qcActionService = useService("action");
        this._qcOrmService = useService("orm");
    },

    async onDirectExportData() {
        if (this.model.root.resModel !== "qc.test") {
            return this._super(...arguments);
        }

        const selectedIds = !this.isDomainSelected
            ? await this.getSelectedResIds()
            : [];
        const useDomain =
            this.isDomainSelected || !selectedIds.length;
        const domain = useDomain ? this.model.root.domain || [] : [];
        const ids = selectedIds.length ? selectedIds : [];

        const action = await this._qcOrmService.call(
            "qc.test",
            "action_export_excel_direct",
            [],
            {
                ids,
                domain,
                context: this.props.context,
            }
        );
        await this._qcActionService.doAction(action);
        return;
    },
});
